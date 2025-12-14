#!/usr/bin/env python3
"""
Configuration Manager for TFT Data Collection Pipeline

Handles loading, validation, and management of collection parameters from YAML
configuration files. Supports:
- Multiple collection periods (daily, weekly, monthly)
- Environment-specific overrides
- Environment variable substitution
- CLI parameter overrides
- Parameter validation and defaults
"""

import yaml
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CollectionPeriod(Enum):
    """Supported collection periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class CollectionParameters:
    """Data class for collection parameters"""
    max_players: int
    regions: List[str]
    match_history_depth: int
    quality_threshold: int
    deduplication: bool
    sample_rate: float


@dataclass
class CollectionConfig:
    """Data class for collection configuration"""
    timeout: int
    max_api_calls: int
    expected_matches: str  # e.g., "50-100"
    estimated_size_mb: str


@dataclass
class PeriodConfig:
    """Complete configuration for a collection period"""
    enabled: bool
    schedule: str
    description: str
    parameters: Dict[str, Any]
    collection_config: Dict[str, Any]
    validation: Dict[str, Any]
    preservation: Dict[str, Any]
    notifications: Dict[str, Any]
    post_processing: Optional[Dict[str, Any]] = None


class ConfigManager:
    """
    Manages loading and accessing configuration for the TFT data collection pipeline.
    
    Features:
    - YAML configuration file loading
    - Environment variable substitution
    - Environment-specific overrides
    - CLI parameter overrides
    - Parameter validation
    - Default value handling
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to YAML configuration file. Defaults to config/config.yaml
        """
        self.config_file = Path(config_file) if config_file else Path("config/config.yaml")
        self.config: Dict[str, Any] = {}
        self.cli_overrides: Dict[str, Any] = {}
        
        self._load_configuration()
    
    def _load_configuration(self):
        """Load and parse configuration file with environment variable substitution"""
        if not self.config_file.exists():
            logger.warning(f"Configuration file not found: {self.config_file}")
            self.config = self._get_default_config()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            
            # Substitute environment variables
            self._substitute_env_vars()
            
            logger.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_default_config()
    
    def _substitute_env_vars(self):
        """
        Replace environment variable placeholders in configuration.
        
        Supports ${VAR_NAME} syntax.
        """
        # Pattern: ${VAR_NAME} or ${VAR_NAME:default_value}
        pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}'
        for key, value in self.config.items():
            if isinstance(value, str):
                self.config[key] = self._replace_var_in_string(value, pattern)
            elif isinstance(value, dict):
                self._substitute_env_vars_in_dict(value, pattern)
    
    def _replace_var_in_string(self, text: str, pattern: str) -> str:
        """Replace environment variables in a string"""
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else None
            
            if var_name in os.environ:
                return os.environ[var_name]
            elif default_value:
                return default_value
            else:
                logger.warning(f"Environment variable not found: {var_name}")
                return match.group(0)
        
        return re.sub(pattern, replace_var, text)
    
    def _substitute_env_vars_in_dict(self, d: Dict, pattern: str = None):
        """Recursively substitute environment variables in a dictionary"""
        if pattern is None:
            pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}'
        
        for key, value in d.items():
            if isinstance(value, str):
                d[key] = self._replace_var_in_string(value, pattern)
            elif isinstance(value, dict):
                self._substitute_env_vars_in_dict(value, pattern)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge override dictionary into base dictionary.
        
        Args:
            base: Base dictionary to merge into
            override: Override dictionary with values to merge
            
        Returns:
            Merged dictionary (base is modified in-place)
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def apply_cli_overrides(self, overrides: Dict[str, Any]):
        """
        Apply command-line parameter overrides.
        
        Args:
            overrides: Dictionary of parameter overrides
        """
        self.cli_overrides = overrides
        self._deep_merge(self.config, overrides)
        logger.info(f"Applied CLI overrides: {overrides}")
    
    def get_period_config(self, period: str) -> Optional[PeriodConfig]:
        """
        Get configuration for a specific collection period.
        
        Args:
            period: Collection period (daily, weekly, monthly)
            
        Returns:
            PeriodConfig object or None if period not found
        """
        if "collection_periods" not in self.config:
            return None
        
        period_config = self.config["collection_periods"].get(period)
        if not period_config:
            logger.warning(f"Period configuration not found: {period}")
            return None
        
        return PeriodConfig(**period_config)
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration"""
        return self.config.get("global", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.get_global_config().get("api", {})
    
    def get_paths_config(self) -> Dict[str, Any]:
        """Get paths configuration"""
        return self.get_global_config().get("paths", {})
    
    def get_preservation_config(self) -> Dict[str, Any]:
        """Get preservation configuration"""
        return self.config.get("preservation", {})
    
    def get_quality_config(self) -> Dict[str, Any]:
        """Get quality assurance configuration"""
        return self.config.get("quality_assurance", {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """
        Get notification configuration.
        """
        global_config = self.get_global_config()
        return global_config.get("notifications", {})
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags"""
        return self.config.get("features", {})
    
    def get_advanced_config(self) -> Dict[str, Any]:
        """Get advanced configuration"""
        return self.config.get("advanced", {})
    
    def get_active_periods(self) -> List[str]:
        """Get list of enabled collection periods"""
        periods = []
        if "collection_periods" in self.config:
            for period_name, period_config in self.config["collection_periods"].items():
                if period_config.get("enabled", False):
                    periods.append(period_name)
        return periods
    
    def get_enabled_regions(self, period: str) -> List[str]:
        """
        Get enabled regions for a collection period.
        
        Args:
            period: Collection period
            
        Returns:
            List of region codes
        """
        period_config = self.get_period_config(period)
        if not period_config:
            return []
        
        return period_config.parameters.get("regions", [])
    
    def get_parameter(self, period: str, param_path: str, default: Any = None) -> Any:
        """
        Get a parameter value using dot notation.
        
        Args:
            period: Collection period
            param_path: Parameter path (e.g., "parameters.max_players" or "collection_config.timeout")
            default: Default value if parameter not found
            
        Returns:
            Parameter value or default
        """
        period_config = self.get_period_config(period)
        if not period_config:
            return default
        
        # Convert PeriodConfig to dict
        config_dict = asdict(period_config)
        
        # Navigate path
        parts = param_path.split(".")
        value = config_dict
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def validate_configuration(self) -> bool:
        """
        Validate configuration for required parameters and consistency.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required top-level sections
            required_sections = ["global", "collection_periods"]
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"Missing required configuration section: {section}")
                    return False
            
            # Check API configuration
            api_config = self.get_api_config()
            if "key" not in api_config or not api_config["key"]:
                logger.error("API key not configured")
                return False
            
            # Check at least one period is enabled
            if not self.get_active_periods():
                logger.warning("No collection periods enabled")
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def export_period_config_dict(self, period: str) -> Dict[str, Any]:
        """
        Export period configuration as a dictionary for easy access in collection scripts.
        
        Args:
            period: Collection period
            
        Returns:
            Dictionary with all configuration for the period
        """
        period_config = self.get_period_config(period)
        if not period_config:
            return {}
        
        return {
            "period": period,
            "enabled": period_config.enabled,
            "schedule": period_config.schedule,
            "description": period_config.description,
            "max_players": period_config.parameters.get("max_players"),
            "regions": period_config.parameters.get("regions", []),
            "match_history_depth": period_config.parameters.get("match_history_depth"),
            "quality_threshold": period_config.parameters.get("quality_threshold"),
            "deduplication": period_config.parameters.get("deduplication"),
            "timeout": period_config.collection_config.get("timeout"),
            "max_api_calls": period_config.collection_config.get("max_api_calls"),
            "backup_enabled": period_config.preservation.get("backup"),
            "backup_frequency": period_config.preservation.get("frequency"),
            "retention": period_config.preservation.get("retention"),
            "min_matches": period_config.validation.get("min_matches"),
            "quality_check": period_config.validation.get("quality_check"),
            "notifications_enabled": period_config.notifications.get("enabled"),
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when file not found"""
        return {
            "global": {
                "api": {
                    "key": os.getenv("RIOT_API_KEY", ""),
                    "region": "LA2",
                    "timeout": 30,
                    "max_retries": 3,
                },
                "paths": {
                    "data_dir": "./data",
                    "logs_dir": "./logs",
                }
            },
            "collection_periods": {
                "weekly": {
                    "enabled": True,
                    "schedule": "0 0 * * 0",
                    "description": "Standard weekly collection",
                    "parameters": {
                        "max_players": None,  # None = collect all players
                        "regions": ["LA2"],
                        "match_history_depth": 20,
                        "quality_threshold": 50,
                        "deduplication": True,
                    }
                }
            }
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ConfigManager(file={self.config_file})"


def create_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """
    Factory method to create a ConfigManager instance.
    
    Args:
        config_file: Path to configuration file (optional)
    
    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_file=config_file)
