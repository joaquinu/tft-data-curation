"""
Quality Assurance Package:

- data_validator: Core data structure validation and integrity checking
- schema_validator: JSON-LD schema validation and compliance verification  
- anomaly_detector: Statistical analysis and outlier detection algorithms
- quality_metrics: Quality assessment metrics and reporting functions
- field_detector: Missing field detection and data completeness analysis
- tree_validator: Hierarchical/tree-based data validation for match structures
- cross_cycle_validator: Cross-cycle data consistency and trend analysis
"""

from .data_validator import (
    validate_json_structure,
    validate_tft_data_structure,
    validate_match_data_completeness,
    check_data_integrity
)
from .schema_validator import (
    validate_schema_structure,
    validate_jsonld_compliance,
    check_schema_completeness
)
from .anomaly_detector import (
    detect_statistical_anomalies,
    identify_performance_outliers,
    analyze_data_patterns,
    generate_anomaly_report
)
from .quality_metrics import (
    calculate_data_quality_score,
    generate_quality_report,
    assess_data_completeness,
    measure_data_consistency
)
from .field_detector import (
    detect_missing_fields,
    analyze_field_coverage,
    validate_required_fields,
    generate_field_report
)
from .tree_validator import (
    validate_hierarchical_structure,
    check_tree_data_integrity,
    validate_match_hierarchy,
    analyze_data_relationships,
    should_skip_match,
    calculate_tree_validation_score
)
from .cross_cycle_validator import (
    CrossCycleValidator,
    run_validation
)

__all__ = [
    'validate_json_structure',
    'validate_tft_data_structure', 
    'validate_match_data_completeness',
    'check_data_integrity',
    'validate_schema_structure',
    'validate_jsonld_compliance',
    'check_schema_completeness',
    'detect_statistical_anomalies',
    'identify_performance_outliers',
    'analyze_data_patterns',
    'generate_anomaly_report',
    'calculate_data_quality_score',
    'generate_quality_report',
    'assess_data_completeness',
    'measure_data_consistency',
    'detect_missing_fields',
    'analyze_field_coverage',
    'validate_required_fields',
    'generate_field_report',
    'validate_hierarchical_structure',
    'check_tree_data_integrity',
    'validate_match_hierarchy',
    'analyze_data_relationships',
    'should_skip_match',
    'calculate_tree_validation_score',
    'CrossCycleValidator',
    'run_validation'
]
