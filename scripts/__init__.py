"""
Scripts Package
===============

This package contains modular components for TFT data collection.

Modules:
- base_infrastructure: Core API infrastructure and session management
- rate_limiting: Advanced rate limiting and error handling framework
- riot_api_endpoints: Complete Riot Games API endpoint implementations
- leaderboard_mixin: Shared leaderboard collection functionality
- schema: JSON-LD schema definitions and semantic data structure design
- optimized_match_collector: Optimized match collection with deduplication (30-70% API call reduction)
- utils: Data persistence utilities and general helper functions
"""

from .base_infrastructure import BaseAPIInfrastructure, setup_logging, validate_api_key
from .rate_limiting import (
    RateLimitedRequester, 
    RateLimiter, 
    APIErrorHandler, 
    RateLimitConfig,
    create_rate_limited_session,
    monitor_rate_limits,
    RIOT_API_RATE_LIMITS
)
from .riot_api_endpoints import RiotAPIEndpoints, API_ENDPOINTS_DOCUMENTATION
from .leaderboard_mixin import LeaderboardMixin
from .schema import TFTSchemaGenerator, create_default_schema, get_tft_context
from .optimized_match_collector import TFTMatchCollector, create_match_collector
from .governance_policies import TFTIdentifierGovernance, get_governance_policy, check_identifier_compliance
from .utils import (
    save_data_to_file,
    load_data_from_file,
    identify_incomplete_matches,
    SPECIAL_QUEUES,
)

__all__ = [
    'BaseAPIInfrastructure', 
    'RiotAPIEndpoints', 
    'API_ENDPOINTS_DOCUMENTATION',
    'LeaderboardMixin',
    'RateLimitedRequester',
    'RateLimiter',
    'APIErrorHandler', 
    'RateLimitConfig',
    'create_rate_limited_session',
    'monitor_rate_limits',
    'RIOT_API_RATE_LIMITS',
    'setup_logging',
    'validate_api_key',
    'TFTSchemaGenerator',
    'create_default_schema',
    'get_tft_context',
    'TFTMatchCollector',
    'create_match_collector',
    'TFTIdentifierGovernance',
    'get_governance_policy',
    'check_identifier_compliance',
    'save_data_to_file',
    'load_data_from_file',
    'identify_incomplete_matches',
    'SPECIAL_QUEUES',
]
