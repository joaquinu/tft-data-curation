#!/usr/bin/env python3
"""
Test and demonstration script for the Configuration Manager

This script demonstrates all major features of the configuration management system.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scripts.config_manager import create_config_manager, CollectionPeriod
import json


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def test_basic_loading():
    """Test basic configuration loading"""
    print_section("1. Basic Configuration Loading")
    
    config = create_config_manager()
    print(f"✓ Configuration loaded successfully")
    print(f"  Config file: {config.config_file}")
    print(f"  API region: {config.get_api_config()['region']}")


def test_period_configs():
    """Test loading configuration for each period"""
    print_section("2. Collection Period Configurations")
    
    config = create_config_manager()
    
    for period in ["daily", "weekly", "monthly"]:
        period_config = config.get_period_config(period)
        if period_config:
            print(f"\n{period.upper()}:")
            print(f"  Enabled: {period_config.enabled}")
            print(f"  Schedule: {period_config.schedule}")
            print(f"  Max Players: {period_config.parameters.get('max_players', 'N/A')}")
            print(f"  Regions: {period_config.parameters.get('regions', ['default'])}")
            print(f"  Timeout: {period_config.collection_config.get('timeout', 'N/A')}s")
            print(f"  Retention: {period_config.preservation.get('retention', 'N/A')}")
            print(f"  Backup: {period_config.preservation.get('backup', 'N/A')}")


def test_get_parameters():
    """Test getting specific parameters"""
    print_section("3. Getting Specific Parameters")
    
    config = create_config_manager()
    
    period = "weekly"
    params_to_fetch = [
        "parameters.max_players",
        "parameters.regions",
        "collection_config.timeout",
        "collection_config.max_api_calls",
        "preservation.backup",
        "preservation.retention",
        "validation.min_matches",
    ]
    
    print(f"Parameters for {period.upper()} collection:\n")
    for param_path in params_to_fetch:
        value = config.get_parameter(period, param_path, "NOT FOUND")
        print(f"  {param_path}: {value}")


def test_export_config():
    """Test exporting period configuration"""
    print_section("4. Exporting Period Configuration as Dictionary")
    
    config = create_config_manager()
    
    period_dict = config.export_period_config_dict("weekly")
    print(f"Weekly configuration export:\n")
    print(json.dumps(period_dict, indent=2))


def test_active_periods():
    """Test getting active periods"""
    print_section("5. Active Collection Periods")
    
    config = create_config_manager()
    active = config.get_active_periods()
    
    print(f"Active periods: {active}")
    for period in active:
        print(f"  ✓ {period}")


def test_regions():
    """Test getting enabled regions for each period"""
    print_section("6. Enabled Regions by Period")
    
    config = create_config_manager()
    
    for period in ["daily", "weekly", "monthly"]:
        regions = config.get_enabled_regions(period)
        if regions:
            print(f"{period.upper()}: {regions}")


def test_cli_overrides():
    """Test CLI parameter overrides"""
    print_section("7. CLI Parameter Overrides")
    
    config = create_config_manager()
    
    print("Original weekly config:")
    print(f"  Max players: {config.get_parameter('weekly', 'parameters.max_players')}")
    print(f"  Regions: {config.get_parameter('weekly', 'parameters.regions')}")
    
    # Apply overrides
    overrides = {
        "collection_periods": {
            "weekly": {
                "parameters": {
                    "max_players": 2,
                    "regions": ["LA2"]
                }
            }
        }
    }
    config.apply_cli_overrides(overrides)
    
    print("\nAfter applying CLI overrides:")
    print(f"  Max players: {config.get_parameter('weekly', 'parameters.max_players')}")
    print(f"  Regions: {config.get_parameter('weekly', 'parameters.regions')}")


def test_validation():
    """Test configuration validation"""
    print_section("9. Configuration Validation")
    
    config = create_config_manager()
    
    if config.validate_configuration():
        print("✓ Configuration validation PASSED")
    else:
        print("✗ Configuration validation FAILED")


def test_feature_flags():
    """Test feature flags"""
    print_section("10. Feature Flags")
    
    config = create_config_manager()
    flags = config.get_feature_flags()
    
    for flag_name, flag_value in flags.items():
        status = "✓" if flag_value else "✗"
        print(f"  {status} {flag_name}: {flag_value}")


def test_quality_config():
    """Test quality assurance configuration"""
    print_section("11. Quality Assurance Configuration")
    
    config = create_config_manager()
    qa_config = config.get_quality_config()
    
    print("Quality validation rules:")
    for rule in qa_config.get('validation_rules', []):
        print(f"  ✓ {rule}")
    
    print("\nQuality thresholds:")
    thresholds = qa_config.get('thresholds', {})
    for threshold, value in thresholds.items():
        print(f"  {threshold}: {value}")


def test_preservation_config():
    """Test preservation configuration"""
    print_section("12. Preservation Configuration")
    
    config = create_config_manager()
    pres_config = config.get_preservation_config()
    
    print("Backup strategy:")
    backup = pres_config.get('backup', {})
    print(f"  Strategy: {backup.get('strategy')}")
    print(f"  Frequency: {backup.get('frequency')}")
    print(f"  Compression: {backup.get('compression')}")
    
    print("\nRetention policies:")
    retention = pres_config.get('retention_policies', {})
    for policy_name, duration in retention.items():
        print(f"  {policy_name}: {duration}")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  TFT Configuration Manager - Test Suite")
    print("=" * 70)
    
    try:
        test_basic_loading()
        test_period_configs()
        test_get_parameters()
        test_export_config()
        test_active_periods()
        test_regions()
        test_cli_overrides()
        test_validation()
        test_feature_flags()
        test_quality_config()
        test_preservation_config()
        
        print_section("✓ All Tests Completed Successfully")
        return 0
        
    except Exception as e:
        print_section(f"✗ Test Failed with Error")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
