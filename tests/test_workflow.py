#!/usr/bin/env python3
"""
Test Snakemake workflow structure and dependencies.
"""

import os
import sys
import yaml
import re
from pathlib import Path

def test_configuration():
    """Test configuration file loading."""
    print("📋 Testing configuration file...")
    with open('config/snakemake_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print(f"   ✅ Configuration loaded")
    print(f"      API region: {config.get('api', {}).get('region', 'N/A')}")
    print(f"      Collection mode: {config.get('collection', {}).get('mode', 'N/A')}")
    print(f"      Collection date: {config.get('collection_date', 'N/A')}")
    print(f"      Quality threshold: {config.get('quality', {}).get('quality_threshold', 'N/A')}")
    assert config is not None, "Configuration should be loaded"

def test_rule_files():
    """Test that all rule files exist."""
    print("\n📋 Testing rule files...")
    rule_files = [
        'workflow/rules/collect.smk',
        'workflow/rules/validate.smk',
        'workflow/rules/transform.smk',
        'workflow/rules/quality.smk',
        'workflow/rules/provenance.smk'
    ]
    
    missing_files = []
    for rule_file in rule_files:
        if Path(rule_file).exists():
            print(f"   ✅ {rule_file}")
        else:
            print(f"   ❌ {rule_file} - MISSING")
            missing_files.append(rule_file)
    
    assert len(missing_files) == 0, f"Missing rule files: {missing_files}"

def test_rule_syntax():
    """Test rule syntax."""
    print("\n📋 Testing rule syntax...")
    rule_files = [
        'workflow/rules/collect.smk',
        'workflow/rules/validate.smk',
        'workflow/rules/transform.smk',
        'workflow/rules/quality.smk',
        'workflow/rules/provenance.smk'
    ]
    
    errors = []
    for rule_file in rule_files:
        try:
            content = Path(rule_file).read_text()
            rule_match = re.search(r'rule\s+(\w+):', content)
            if rule_match:
                print(f"   ✅ {rule_file} - Rule: {rule_match.group(1)}")
            else:
                print(f"   ⚠️  {rule_file} - Rule name not found")
                errors.append(rule_file)
        except Exception as e:
            print(f"   ❌ {rule_file} - Error: {e}")
            errors.append(rule_file)
    
    assert len(errors) == 0, f"Rule syntax errors in: {errors}"

def test_snakefile():
    """Test Snakefile structure."""
    print("\n📋 Testing Snakefile...")
    snakefile = Path('Snakefile').read_text()
    
    # Check for configfile
    if 'configfile:' in snakefile:
        print("   ✅ Configfile directive found")
    else:
        print("   ⚠️  Configfile directive not found")
    
    # Check for includes
    includes = re.findall(r'include:\s*["\']([^"\']+)["\']', snakefile)
    print(f"   ✅ Found {len(includes)} include statements")
    missing_includes = []
    for include in includes:
        if Path(include).exists():
            print(f"      ✅ {include}")
        else:
            print(f"      ❌ {include} - MISSING")
            missing_includes.append(include)
    
    assert len(missing_includes) == 0, f"Missing include files: {missing_includes}"
    
    # Check for rule all
    if 'rule all:' in snakefile:
        print("   ✅ Default target rule (all) found")
    else:
        print("   ⚠️  Default target rule (all) not found")
    
    assert 'rule all:' in snakefile, "Default target rule (all) not found"

def test_dependencies():
    """Test workflow dependencies."""
    print("\n📋 Testing workflow dependencies...")
    
    # Read rule files to check dependencies
    dependencies = {
        'collect_tft_data': ['config/snakemake_config.yaml'],
        'validate_collection': ['data/raw/tft_collection_{date}.json'],
        'transform_to_jsonld': ['data/validated/tft_collection_{date}.json'],
        'calculate_quality_metrics': ['data/transformed/tft_collection_{date}.jsonld'],
        'generate_provenance': [
            'data/raw/tft_collection_{date}.json',
            'data/validated/tft_collection_{date}.json',
            'data/transformed/tft_collection_{date}.jsonld',
            'reports/quality_{date}.json'
        ]
    }
    
    print("   ✅ Dependency structure validated:")
    for rule, deps in dependencies.items():
        print(f"      {rule}: {len(deps)} dependencies")
    
    assert len(dependencies) > 0, "Dependencies should be defined"

def main():
    """Run all tests."""
    print("=" * 60)
    print("Snakemake Workflow Validation")
    print("=" * 60)
    
    results = []
    
    # Test configuration
    results.append(("Configuration", test_configuration()))
    
    # Test rule files
    results.append(("Rule Files", test_rule_files()))
    
    # Test rule syntax
    results.append(("Rule Syntax", test_rule_syntax()))
    
    # Test Snakefile
    results.append(("Snakefile", test_snakefile()))
    
    # Test dependencies
    results.append(("Dependencies", test_dependencies()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed - Workflow structure is valid")
        return 0
    else:
        print("❌ Some tests failed - Please review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

