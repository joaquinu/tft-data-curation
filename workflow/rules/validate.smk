# workflow/rules/validate.smk
# Data Validation Rule

rule validate_collection:
    """
    Validate collected data using quality assurance modules.
    
    This rule validates the collected data using the quality_assurance
    modules and generates a validation report.
    """
    input:
        raw_data="data/raw/tft_collection_{date}.json"
    output:
        validated_data="data/validated/tft_collection_{date}.json",
        validation_report="reports/validation_{date}.json"
    params:
        quality_threshold=lambda wildcards: config.get("quality", {}).get("quality_threshold", 0.8)
    log:
        "logs/validate_{date}.log"
    shell:
        """
        python3 -c "
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path('{input.raw_data}').parent.parent.parent))

try:
    from quality_assurance.data_validator import validate_tft_data_structure
    from quality_assurance.quality_metrics import calculate_data_quality_score
    from quality_assurance.tree_validator import validate_hierarchical_structure, calculate_tree_validation_score
    from scripts.governance_policies import get_governance_policy
    
    with open('{input.raw_data}', 'r') as f:
        data = json.load(f)
    
    # Structure validation
    is_valid, validation_errors = validate_tft_data_structure(data)
    
    # Quality metrics (includes tree validation as 'structure' component)
    quality_report = calculate_data_quality_score(data)
    
    # Tree-based hierarchical validation (per project proposal)
    tree_report = calculate_tree_validation_score(data)
    
    # Governance compliance check for identifiers
    governance = get_governance_policy()
    governance_compliance = {{}}
    if '@identifiers' in data:
        compliance_results = []
        for identifier_type, identifier_data in data.get('@identifiers', {{}}).items():
            if isinstance(identifier_data, dict) and 'type' in identifier_data:
                metadata = {{
                    'identifier': identifier_data.get('identifier', identifier_type),
                    'type': identifier_data.get('type', 'unknown'),
                    'created_at': identifier_data.get('created_at', datetime.now().isoformat())
                }}
                compliance = governance.validate_compliance(metadata)
                compliance_results.append(compliance)
        
        governance_compliance = {{
            'checked': len(compliance_results),
            'compliant': sum(1 for r in compliance_results if r.get('compliance_status') == 'compliant'),
            'warnings': sum(1 for r in compliance_results if r.get('compliance_status') == 'warning'),
            'non_compliant': sum(1 for r in compliance_results if r.get('compliance_status') == 'non-compliant'),
            'results': compliance_results
        }}
    else:
        governance_compliance = {{'checked': 0, 'message': 'No identifiers found in data'}}
    
    # Extract overall_score from the quality report (0-100 scale)
    quality_score = quality_report.get('overall_score', 0.0) / 100.0  # Convert to 0-1 scale
    threshold = {params.quality_threshold}
    
    report = {{
        'validation': {{
            'is_valid': is_valid,
            'errors': validation_errors
        }},
        'tree_validation': {{
            'tree_score': tree_report.get('tree_score', 0.0),
            'structure_valid': tree_report.get('structure_valid', False),
            'hierarchy_issues': tree_report.get('hierarchy_issues_count', 0),
            'relationship_integrity': tree_report.get('relationship_integrity_score', 0.0)
        }},
        'governance_compliance': governance_compliance,
        'quality_score': quality_score,
        'quality_report': quality_report,
        'threshold': threshold,
        'passed': quality_score >= threshold and is_valid
    }}
    
    with open('{output.validation_report}', 'w') as f:
        json.dump(report, f, indent=2)
    
    passed = quality_score >= threshold and is_valid
    
    if passed:
        import shutil
        shutil.copy('{input.raw_data}', '{output.validated_data}')
        governance_status = governance_compliance.get('compliant', 0)
        governance_total = governance_compliance.get('checked', 0)
        print(f'[SUCCESS] Validation passed: quality_score={{quality_score}} >= threshold={{threshold}}, structure_valid={{is_valid}}')
        if governance_total > 0:
            print(f'[SUCCESS] Governance compliance: {{governance_status}}/{{governance_total}} identifiers compliant')
    else:
        warnings = []
        if not is_valid:
            warnings.append(f'Structure validation failed: {{validation_errors}}')
        if quality_score < threshold:
            warnings.append(f'Quality score {{quality_score}} below threshold {{threshold}}')
        
        print(f'[WARNING] Validation issues detected', file=sys.stderr)
        for warning in warnings:
            print(f'   - {{warning}}', file=sys.stderr)
        print(f'   Continuing with validation report, but data may need review.', file=sys.stderr)
        # Still copy the data but mark it as needing review in the report
        import shutil
        shutil.copy('{input.raw_data}', '{output.validated_data}')
        print(f'Data copied to validated directory with validation warnings')
except Exception as e:
    print(f'Validation error: {{e}}', file=sys.stderr)
    raise
" 2>&1 | tee {log}
        """


rule validate_cross_cycle:
    """
    Run cross-cycle validation to detect trends and anomalies across collections.
    
    This rule runs after the current collection is validated and checks it against
    historical data in the validated directory.
    """
    input:
        current_file="data/validated/tft_collection_{date}.json"
    output:
        report="reports/cross_cycle_{date}.json"
    log:
        "logs/cross_cycle_{date}.log"
    shell:
        """
        python3 scripts/run_cross_cycle_validation.py \
            --input-dir data/validated \
            --report-file {output.report} \
            2>&1 | tee {log}
        """
