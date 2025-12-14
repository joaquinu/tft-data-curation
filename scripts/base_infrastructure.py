"""
Base Infrastructure Module
==========================

This module contains the core infrastructure components for TFT data collection.
Provides rate limiting, session management, request handling, and configuration.

Week 1 Deliverable: Basic Python Infrastructure
- Session management and API key handling
- Rate limiting implementation with dual-window tracking  
- Request handling with comprehensive error management
- JSON-LD data structure initialization
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Import rate limiting framework
from .rate_limiting import RateLimitedRequester, RateLimitConfig, create_rate_limited_session

logger = logging.getLogger(__name__)


class BaseAPIInfrastructure:
    """
    Base infrastructure class providing core API interaction capabilities.
    
    Features:
    - Advanced rate limiting framework with comprehensive error handling
    - Session management with proper headers
    - JSON-LD data structure initialization
    - Configurable API endpoints for different regions
    """
    
    def __init__(self, api_key: str, key_type: str = "personal"):
        """
        Initialize base infrastructure with API key and configuration
        
        Args:
            api_key: Riot Games API key for authentication
            key_type: Type of API key ("personal", "production", "development")
        """
        # API Configuration
        self.api_key = api_key
        self.platform_host = "la2.api.riotgames.com"
        self.regional_host = "americas.api.riotgames.com"  # LA2 uses AMERICAS region for matches
        
        # Initialize rate-limited requester with comprehensive framework
        self.requester = create_rate_limited_session(api_key, key_type)
        self.session = self.requester.session
        
        # Initialize JSON-LD data structure
        self.collected_data = self._initialize_data_structure()
    
    def _initialize_data_structure(self) -> Dict[str, Any]:
        """Initialize JSON-LD compliant data structure"""
        return {
            "@context": {
                "@vocab": "http://tft-data-extraction.com/schema#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "dcterms": "http://purl.org/dc/terms/",
                "extractionTimestamp": {"@type": "xsd:dateTime"},
                "gameCreation": {"@type": "xsd:dateTime"},
                "puuid": {"@type": "xsd:string"},
                "placement": {"@type": "xsd:integer"},
                "gameLength": {"@type": "xsd:float"}
            },
            "@type": "TFTDataCollection",
            "extractionTimestamp": datetime.utcnow().isoformat() + "Z",
            "extractionLocation": "LA2",
            "players": {},
            "matches": {},
            "leaderboards": {},
            "static_data": {},
            "live_games": {},
            "collection_config": {}
        }
    
    def _make_request(self, url: str, params: Dict = None, timeout: Optional[int] = None) -> Optional[Dict]:
        """
        Make API request using the advanced rate limiting framework
        
        Args:
            url: Full API endpoint URL
            params: Optional query parameters
            timeout: Optional custom timeout in seconds (defaults to config timeout)
            
        Returns:
            JSON response data or None if request failed
        """
        return self.requester.make_request(url, params, timeout=timeout)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics for monitoring using advanced rate limiting framework"""
        stats = self.requester.get_comprehensive_stats()
        stats["session_active"] = self.session is not None
        return stats


# =============================================================================
# INFRASTRUCTURE UTILITIES
# =============================================================================

def setup_logging(level: str = "INFO", format_string: str = None) -> logging.Logger:
    """
    Setup standardized logging configuration for TFT data collection
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom format string for log messages
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {level} level")
    return logger


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format (basic validation)
    
    Args:
        api_key: Riot Games API key
        
    Returns:
        True if key format appears valid
    """
    if not api_key:
        return False
    
    # Riot API keys typically start with "RGAPI-" and are 42+ characters
    if not api_key.startswith("RGAPI-"):
        return False
        
    if len(api_key) < 42:
        return False
    
    return True


# =============================================================================
# INFRASTRUCTURE CONSTANTS
# =============================================================================

RIOT_API_HOSTS = {
    "LA1": {
        "platform": "la1.api.riotgames.com",
        "regional": "americas.api.riotgames.com"
    },
    "LA2": {
        "platform": "la2.api.riotgames.com", 
        "regional": "americas.api.riotgames.com"
    },
    "NA1": {
        "platform": "na1.api.riotgames.com",
        "regional": "americas.api.riotgames.com"
    },
    "BR1": {
        "platform": "br1.api.riotgames.com",
        "regional": "americas.api.riotgames.com"
    }
}

RATE_LIMITS = {
    "personal": {
        "per_second": 20,
        "per_2_minutes": 100
    },
    "production": {
        "per_second": 3000,
        "per_2_minutes": 180000
    }
}
