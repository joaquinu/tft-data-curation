"""
TFT Data Extraction Project
==========================

A comprehensive data collection and analysis system for Teamfight Tactics (TFT) 
using the Riot Games API with advanced quality assurance and pipeline testing frameworks.

This project provides:
- Automated data collection from Riot's TFT API
- Advanced rate limiting and error handling
- JSON-LD semantic data modeling
- Quality assurance framework with validation and anomaly detection  
- Comprehensive pipeline testing infrastructure
- Graph-based data exploration and analysis

Main Components:
- TFTMatchCollector: Optimized match collection system with deduplication
- Quality Assurance Framework: Data validation and quality metrics
- Pipeline Testing Framework: End-to-end testing and validation
- Graph Explorer: RDF and NetworkX-based data analysis

Author: TFT Data Extraction Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "TFT Data Extraction Team"
__license__ = "MIT"

# Package imports - modular framework components
try:
    from . import scripts
    from . import quality_assurance  
except ImportError:
    scripts = None
    quality_assurance = None

# Convenience imports for most common use cases
try:
    from .scripts import (
        RiotAPIEndpoints,
        BaseAPIInfrastructure, 
        RateLimiter,
        TFTSchemaGenerator
    )
except ImportError:
    RiotAPIEndpoints = None
    BaseAPIInfrastructure = None
    RateLimiter = None
    TFTSchemaGenerator = None

try:
    from .quality_assurance import (
        validate_json_structure,
        validate_schema_structure,
        detect_statistical_anomalies,
        calculate_data_quality_score
    )
except ImportError:
    validate_json_structure = None
    validate_schema_structure = None
    detect_statistical_anomalies = None
    calculate_data_quality_score = None

# Pipeline testing imports
try:
    from .tests import (
        run_complete_pipeline_test,
        run_all_pipeline_tests,
        EndToEndPipelineTester,
        PipelineTestRunner
    )
    pipeline_testing = True
except ImportError:
    run_complete_pipeline_test = None
    run_all_pipeline_tests = None
    EndToEndPipelineTester = None
    PipelineTestRunner = None
    pipeline_testing = None

# Define what gets exported with "from tft_data_extraction import *"
__all__ = [
    # Framework modules  
    'scripts',
    'quality_assurance',
    
    
    # Key components
    'RiotAPIEndpoints',
    'BaseAPIInfrastructure',
    'RateLimiter', 
    'TFTSchemaGenerator',
    
    # Quality functions
    'validate_json_structure',
    'validate_schema_structure', 
    'detect_statistical_anomalies',
    'calculate_data_quality_score',
    
    
    
    # Metadata
    '__version__',
    '__author__',
    '__license__'
]

def get_project_info():
    """
    Get comprehensive information about the TFT Data Extraction project.
    
    Returns:
        dict: Project metadata and component availability
    """
    return {
        'name': 'TFT Data Extraction Project',
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'components': {
            'scripts_module': scripts is not None,
            'quality_assurance': quality_assurance is not None,
            'pipeline_testing': pipeline_testing is not None,
        },
        'description': 'Comprehensive TFT data collection with quality assurance and testing'
    }

def list_available_components():
    """
    Print a summary of available project components.
    """
    info = get_project_info()
    print(f"\n[INFO] {info['name']} v{info['version']}")
    print("=" * 50)
    
    print("\n[INFO] Available Components:")
    for component, available in info['components'].items():
        status = "[SUCCESS] Available" if available else "[WARNING] Missing"
        print(f"  {component}: {status}")
    
    print(f"\n[INFO] Description: {info['description']}")
    print("\n[INFO] Quick Start:")
    print("  from scripts.optimized_match_collector import create_match_collector")
    print("  collector = create_match_collector('YOUR_API_KEY')")
    print("  # Start collecting TFT data!")

# Optional: Auto-display info when imported interactively
if __name__ == "__main__":
    list_available_components()
