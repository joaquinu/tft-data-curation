# workflow/rules/quality.smk
# Quality Metrics Rule

rule calculate_quality_metrics:
    """
    Calculate comprehensive quality metrics for processed data.
    
    This rule calculates quality metrics for the transformed data
    and generates a quality report.
    """
    input:
        jsonld_data="data/transformed/tft_collection_{date}.jsonld"
    output:
        quality_report="reports/quality_{date}.json"
    log:
        "logs/quality_{date}.log"
    shell:
        """
        # Ensure output directory exists
        mkdir -p $(dirname {output.quality_report})
        
        python3 -c "
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path('{input.jsonld_data}').parent.parent.parent))

try:
    from quality_assurance.quality_metrics import calculate_data_quality_score
    
    with open('{input.jsonld_data}', 'r') as f:
        jsonld_data = json.load(f)
    
    # Extract actual data from JSON-LD wrapper if present
    if isinstance(jsonld_data, dict) and '@context' in jsonld_data and 'data' in jsonld_data:
        data = jsonld_data['data']
        print(f'[INFO] Extracted data from JSON-LD wrapper')
    else:
        data = jsonld_data
        print(f'[INFO] Using data directly (no wrapper)')
    
    # Verify data structure
    data_keys = list(data.keys())[:10]
    print('[INFO] Data keys: ' + str(data_keys))
    has_collection_info = 'collectionInfo' in data
    print('[INFO] Has collectionInfo: ' + str(has_collection_info))
    if 'collectionInfo' in data:
        collection_info_keys = list(data['collectionInfo'].keys())[:10]
        print('[INFO] collectionInfo keys: ' + str(collection_info_keys))
    
    quality_score = calculate_data_quality_score(data)
    
    metrics = {{
        'quality_score': quality_score,
        'data_size': len(data) if isinstance(data, list) else 1,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }}
    
    with open('{output.quality_report}', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Verify output file was created
    output_path = Path('{output.quality_report}')
    if not output_path.exists():
        raise FileNotFoundError(f'Output file {{output_path}} was not created')
    
    overall_score = quality_score.get('overall_score', 0)
    quality_grade = quality_score.get('quality_grade', 'N/A')
    print(f'[SUCCESS] Quality metrics calculated: score={{overall_score:.2f}} ({{quality_grade}})')
    print(f'[SUCCESS] Output file: {{output_path}}')
except Exception as e:
    print(f'[ERROR] Quality metrics error: {{e}}', file=sys.stderr)
    raise
" 2>&1 | tee {log}
        """

