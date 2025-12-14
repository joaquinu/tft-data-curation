"""
This module provides comprehensive rate limiting and error handling for API interactions.
Implements Riot Games API rate limits with dual-window tracking and intelligent error recovery.
"""

import time
import requests
import json
import random
from typing import Dict, List, Optional, Any, Callable, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration class for rate limiting settings"""
    max_requests_per_second: int = 20
    max_requests_per_2_minutes: int = 100
    retry_delay: float = 10.0
    min_retry_delay: float = 1.0
    min_sleep_time: float = 2.0
    max_retries: int = 10
    request_timeout: int = 60
    buffer_time: float = 0.1
    exponential_base: float = 2.0
    jitter_max: float = 0.3
    proactive_2m_buffer: int = 1

@dataclass
class RateLimitStats:
    """Statistics tracking for rate limiting"""
    total_requests: int = 0
    requests_1s: int = 0
    requests_2m: int = 0
    rate_limit_hits_1s: int = 0
    rate_limit_hits_2m: int = 0
    retry_count: int = 0
    error_count: int = 0
    last_request_time: Optional[float] = None
    rate_429_count: int = 0
    dynamic_rate_adjustment: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for monitoring"""
        return {
            "total_requests": self.total_requests,
            "recent_requests_1s": self.requests_1s,
            "recent_requests_2m": self.requests_2m,
            "rate_limit_1s_hits": self.rate_limit_hits_1s,
            "rate_limit_2m_hits": self.rate_limit_hits_2m,
            "retry_attempts": self.retry_count,
            "error_count": self.error_count,
            "last_request": datetime.fromtimestamp(self.last_request_time).isoformat() if self.last_request_time else None
        }


class RateLimiter:
    """
    Advanced rate limiter with dual-window tracking for Riot Games API
    """
    
    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize rate limiter with configuration
        """
        self.config = config or RateLimitConfig()
        self.request_times: List[float] = []
        self.stats = RateLimitStats()
        self.last_429_time: Optional[float] = None
        self.recent_429_count: int = 0
        self.rate_adjustment_window_start: float = time.time()
        
        logger.info(f"Rate limiter initialized: {self.config.max_requests_per_second} req/s, "
                   f"{self.config.max_requests_per_2_minutes} req/2min")
    
    def record_429_error(self) -> None:
        """Record a 429 error for dynamic rate adjustment"""
        current_time = time.time()
        self.stats.rate_429_count += 1
        self.recent_429_count += 1
        self.last_429_time = current_time
        
        if current_time - self.rate_adjustment_window_start > 300:
            self.recent_429_count = 1
            self.rate_adjustment_window_start = current_time
        
        if self.recent_429_count > 5:
            reduction = min(0.5, (self.recent_429_count - 5) * 0.1)
            self.stats.dynamic_rate_adjustment = max(0.5, 1.0 - reduction)
            logger.warning(f"Dynamic rate adjustment: {self.stats.dynamic_rate_adjustment:.2f}x "
                          f"(due to {self.recent_429_count} recent 429 errors)")
        else:
            if self.stats.dynamic_rate_adjustment < 1.0:
                self.stats.dynamic_rate_adjustment = min(1.0, self.stats.dynamic_rate_adjustment + 0.05)
    
    def get_effective_rate_limit(self) -> Tuple[int, int]:
        """Get effective rate limits with dynamic adjustment"""
        effective_1s = int(self.config.max_requests_per_second * self.stats.dynamic_rate_adjustment)
        effective_2m = int(self.config.max_requests_per_2_minutes * self.stats.dynamic_rate_adjustment)
        return effective_1s, effective_2m
    
    def check_and_wait(self) -> None:
        """
        Check rate limits and sleep if necessary to prevent violations
        """
        current_time = time.time()
        
        self.request_times = [t for t in self.request_times if current_time - t < 120]
        
        self.stats.requests_1s = len([t for t in self.request_times if current_time - t < 1])
        self.stats.requests_2m = len(self.request_times)
        
        effective_1s, effective_2m = self.get_effective_rate_limit()
        
        if self.stats.requests_1s >= effective_1s:
            recent_requests = [t for t in self.request_times if current_time - t < 1]
            sleep_time = 1.0 - (current_time - recent_requests[0]) + self.config.buffer_time
            sleep_time = max(sleep_time, self.config.min_sleep_time)
            
            logger.debug(f"1-second rate limit reached ({self.stats.requests_1s}/{effective_1s}). "
                        f"Sleeping for {sleep_time:.2f} seconds")
            
            self.stats.rate_limit_hits_1s += 1
            time.sleep(sleep_time)
            current_time = time.time()
            self.request_times = [t for t in self.request_times if current_time - t < 120]
        
        available_slots = effective_2m - len(self.request_times)
        if available_slots < self.config.proactive_2m_buffer:
            if len(self.request_times) > 0:
                requests_to_wait = self.config.proactive_2m_buffer - available_slots
                
                if requests_to_wait > 0 and requests_to_wait < len(self.request_times):
                    target_request_idx = requests_to_wait
                    target_request_age = current_time - self.request_times[target_request_idx]
                    sleep_time = 120.0 - target_request_age + self.config.buffer_time
                    sleep_time = max(sleep_time, self.config.min_sleep_time)
                else:
                    age_of_oldest = current_time - self.request_times[0]
                    sleep_time = 120.0 - age_of_oldest + self.config.buffer_time
                    sleep_time = max(sleep_time, self.config.min_sleep_time)
                
                logger.debug(f"Proactive 2-minute rate limit check: {len(self.request_times)}/{effective_2m} "
                           f"(only {available_slots} slots available, need {self.config.proactive_2m_buffer}). "
                           f"Sleeping for {sleep_time:.2f} seconds")
                
                time.sleep(sleep_time)
                current_time = time.time()
                self.request_times = [t for t in self.request_times if current_time - t < 120]
        
        if len(self.request_times) >= effective_2m:
            age_of_oldest = current_time - self.request_times[0]
            safety_margin = 5.0
            sleep_time = 120.0 - age_of_oldest + self.config.buffer_time + safety_margin
            sleep_time = max(sleep_time, self.config.min_sleep_time)
            
            logger.info(f"2-minute rate limit reached ({len(self.request_times)}/{effective_2m}). "
                       f"Sleeping for {sleep_time:.2f} seconds")
            
            self.stats.rate_limit_hits_2m += 1
            time.sleep(sleep_time)
            current_time = time.time()
            self.request_times = [t for t in self.request_times if current_time - t < 120]
        
        self.request_times.append(time.time())
        self.stats.total_requests += 1
        self.stats.last_request_time = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiting statistics"""
        current_time = time.time()
        self.stats.requests_1s = len([t for t in self.request_times if current_time - t < 1])
        self.stats.requests_2m = len([t for t in self.request_times if current_time - t < 120])
        
        effective_1s, effective_2m = self.get_effective_rate_limit()
        
        stats_dict = self.stats.to_dict()
        stats_dict.update({
            "rate_limit_1s": f"{self.stats.requests_1s}/{effective_1s}",
            "rate_limit_2m": f"{self.stats.requests_2m}/{effective_2m}",
            "dynamic_rate_adjustment": self.stats.dynamic_rate_adjustment,
            "rate_429_count": self.stats.rate_429_count,
            "config": {
                "max_per_second": self.config.max_requests_per_second,
                "max_per_2_minutes": self.config.max_requests_per_2_minutes,
                "retry_delay": self.config.retry_delay,
                "min_retry_delay": self.config.min_retry_delay,
                "max_retries": self.config.max_retries,
                "timeout": self.config.request_timeout
            }
        })
        return stats_dict
    
    def reset_stats(self) -> None:
        """Reset statistics tracking"""
        self.stats = RateLimitStats()
        logger.info("Rate limiting statistics reset")


class APIErrorHandler:
    """
    Comprehensive error handling for API requests with intelligent retry logic
    """
    
    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize error handler with configuration
        """
        self.config = config or RateLimitConfig()
        self.consecutive_errors = 0
        self.last_error_time = None
        
    def handle_response(self, response: requests.Response, url: str) -> Tuple[Optional[Dict], Optional[float]]:
        """
        Handle API response with appropriate error handling and retry logic
        """
        if response.status_code == 200:
            self.consecutive_errors = 0
            try:
                return response.json(), None
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from {url}")
                return None, None
        
        error_message = f"API request failed: {response.status_code} - {url}"
        retry_after = None
        
        if response.status_code == 401:
            logger.error(f"Unauthorized (401): Invalid or expired API key - {url}")
            self.consecutive_errors += 1
            return None, None
            
        elif response.status_code == 403:
            logger.error(f"Forbidden (403): Check API key permissions or rate limits - {url}")
            self.consecutive_errors += 1
            return None, None
            
        elif response.status_code == 404:
            logger.warning(f"Resource not found (404): {url}")
            return None, None
            
        elif response.status_code == 429:
            logger.warning(f"Rate limit exceeded (429): {url}")
            self.consecutive_errors += 1
            
            retry_after_header = response.headers.get('Retry-After')
            if retry_after_header:
                try:
                    retry_after = float(retry_after_header)
                    logger.info(f"API specified Retry-After: {retry_after} seconds")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid Retry-After header value: {retry_after_header}")
            
            return "RETRY", retry_after
            
        elif response.status_code >= 500:
            logger.error(f"Server error ({response.status_code}): {url}")
            self.consecutive_errors += 1
            
            retry_after_header = response.headers.get('Retry-After')
            if retry_after_header:
                try:
                    retry_after = float(retry_after_header)
                    logger.info(f"API specified Retry-After: {retry_after} seconds")
                except (ValueError, TypeError):
                    pass
            
            return "RETRY", retry_after
            
        else:
            logger.error(error_message)
            self.consecutive_errors += 1
            return None, None
    
    def handle_exception(self, exception: Exception, url: str, attempt: int = 0, max_retries: int = 10) -> Optional[Dict]:
        """
        Handle request exceptions with appropriate logging and error categorization
        """
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        
        has_retries = attempt < max_retries
        
        if isinstance(exception, requests.exceptions.Timeout):
            if has_retries:
                logger.warning(f"Request timeout after {self.config.request_timeout}s (will retry): {url}")
            else:
                logger.error(f"Request timeout after {self.config.request_timeout}s (max retries exceeded): {url}")
        elif isinstance(exception, requests.exceptions.ConnectionError):
            if has_retries:
                logger.warning(f"Connection error (will retry): {url}")
            else:
                logger.error(f"Connection error (max retries exceeded): {url}")
        elif isinstance(exception, requests.exceptions.HTTPError):
            logger.error(f"HTTP error: {exception}")
        else:
            if has_retries:
                logger.warning(f"Request exception (will retry): {exception}")
            else:
                logger.error(f"Request exception (max retries exceeded): {exception}")
        
        return None
    
    def should_circuit_break(self) -> bool:
        """
        Determine if circuit breaker should activate due to consecutive errors
        
        Returns:
            True if requests should be temporarily stopped
        """
        if self.consecutive_errors >= 10:
            if self.last_error_time and (time.time() - self.last_error_time) < 300:  # 5 minutes
                return True
        return False
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error handling statistics"""
        return {
            "consecutive_errors": self.consecutive_errors,
            "last_error_time": datetime.fromtimestamp(self.last_error_time).isoformat() if self.last_error_time else None,
            "circuit_breaker_active": self.should_circuit_break()
        }


class RateLimitedRequester:
    """
    Complete rate-limited request handler combining rate limiting and error handling
    """
    
    def __init__(self, session: requests.Session, config: RateLimitConfig = None):
        """
        Initialize rate-limited requester
        """
        self.session = session
        self.config = config or RateLimitConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.error_handler = APIErrorHandler(self.config)
        
        logger.info("Rate-limited requester initialized")
    
    def _calculate_retry_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """
        Calculate retry delay with exponential backoff and jitter
        """
        if retry_after is not None:
            base_delay = max(self.config.min_retry_delay, retry_after)
        else:
            base_delay = self.config.retry_delay * (self.config.exponential_base ** attempt)
            base_delay = max(self.config.min_retry_delay, base_delay)
        
        jitter = random.uniform(0, base_delay * self.config.jitter_max)
        delay = base_delay + jitter
        
        delay = max(self.config.min_retry_delay, delay)
        
        return delay
    
    def make_request(self, url: str, params: Dict = None, timeout: Optional[int] = None) -> Optional[Dict]:
        """
        Make rate-limited API request with comprehensive error handling            
        """
        request_timeout = timeout if timeout is not None else self.config.request_timeout
        
        if self.error_handler.should_circuit_break():
            logger.error("Circuit breaker active - too many consecutive errors")
            return None
        
        for attempt in range(self.config.max_retries + 1):
            self.rate_limiter.check_and_wait()
            
            try:
                response = self.session.get(url, params=params, timeout=request_timeout)
                result, retry_after = self.error_handler.handle_response(response, url)
                
                if response.status_code == 429:
                    self.rate_limiter.record_429_error()
                
                if result == "RETRY" and attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt, retry_after)
                    logger.info(f"Retrying request (attempt {attempt + 1}/{self.config.max_retries}) "
                              f"after {delay:.2f}s: {url}")
                    time.sleep(delay)
                    continue
                elif result == "RETRY":
                    logger.error(f"Max retries exceeded for: {url}")
                    return None
                
                return result
                
            except Exception as e:
                result = self.error_handler.handle_exception(e, url, attempt, self.config.max_retries)
                if attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.debug(f"Retrying after exception (attempt {attempt + 1}/{self.config.max_retries}) "
                              f"after {delay:.2f}s: {url}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Max retries exceeded after exception for: {url}")
                    return None
        
        return None
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for monitoring"""
        return {
            "rate_limiting": self.rate_limiter.get_stats(),
            "error_handling": self.error_handler.get_error_stats(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


RIOT_API_RATE_LIMITS = {
    "personal": RateLimitConfig(
        max_requests_per_second=20,
        max_requests_per_2_minutes=100,
        retry_delay=10.0,
        min_retry_delay=1.0,
        max_retries=10,
        exponential_base=2.0,
        jitter_max=0.3
    ),
    "production": RateLimitConfig(
        max_requests_per_second=3000,
        max_requests_per_2_minutes=180000,
        retry_delay=1.0,
        min_retry_delay=1.0,
        max_retries=10,
        exponential_base=2.0,
        jitter_max=0.3
    ),
    "development": RateLimitConfig(
        max_requests_per_second=10,
        max_requests_per_2_minutes=50,
        retry_delay=15.0,
        min_retry_delay=1.0,
        max_retries=10,
        exponential_base=2.0,
        jitter_max=0.3
    )
}


def create_rate_limited_session(api_key: str, key_type: str = "personal") -> RateLimitedRequester:
    """
    Factory function to create a properly configured rate-limited session
    """
    session = requests.Session()
    session.headers.update({"X-Riot-Token": api_key})
    
    config = RIOT_API_RATE_LIMITS.get(key_type, RIOT_API_RATE_LIMITS["personal"])
    
    requester = RateLimitedRequester(session, config)
    logger.info(f"Created rate-limited session with {key_type} configuration")
    
    return requester


def monitor_rate_limits(requester: RateLimitedRequester) -> None:
    """
    Print comprehensive rate limiting statistics for monitoring
    """
    stats = requester.get_comprehensive_stats()
    
    print("\n" + "="*60)
    print("RATE LIMITING & ERROR HANDLING STATISTICS")
    print("="*60)
    
    rl_stats = stats["rate_limiting"]
    print("Rate Limiting:")
    print(f"  Total Requests: {rl_stats['total_requests']}")
    print(f"  Current Window Usage: {rl_stats['rate_limit_1s']} (1s), {rl_stats['rate_limit_2m']} (2m)")
    print(f"  Rate Limit Hits: {rl_stats['rate_limit_1s_hits']} (1s), {rl_stats['rate_limit_2m_hits']} (2m)")
    
    eh_stats = stats["error_handling"]
    print("\n[WARNING] Error Handling:")
    print(f"  Consecutive Errors: {eh_stats['consecutive_errors']}")
    print(f"  Circuit Breaker: {'🔴 Active' if eh_stats['circuit_breaker_active'] else '🟢 Inactive'}")
    
    print(f"\n🕒 Last Updated: {stats['timestamp']}")
    print("="*60)
