#!/usr/bin/env python3
"""
Regenerate all quality metrics and validation reports for existing validated data.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from quality_assurance.quality_metrics import calculate_data_quality_score
from quality_assurance.cross_cycle_validator import CrossCycleValidator

def regenerate_quality_metrics():
    """Regenerate quality metrics for all validated collections."""
    validated_dir = Path("data/validated")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    validated_files = sorted(validated_dir.glob("tft_collection_*.json"))
    
    print(f"Found {len(validated_files)} validated collections")
    print("Regenerating quality metrics...\n")
    
    for validated_file in validated_files:
        # Extract date from filename
        date = validated_file.stem.replace("tft_collection_", "")
        
        print(f"Processing {date}...")
        
        try:
            # Load validated data
            with open(validated_file, 'r') as f:
                data = json.load(f)
            
            # Calculate quality metrics
            metrics = calculate_data_quality_score(data)
            
            # Save quality report
            quality_report_path = reports_dir / f"quality_{date}.json"
            with open(quality_report_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            print(f"  ✓ Quality report saved: {quality_report_path}")
            print(f"  ✓ Overall score: {metrics.get('overall_score', 0):.1f}")
            
        except Exception as e:
            print(f"  ✗ Error processing {date}: {e}")
    
    print("\n" + "="*60)
    print("Quality metrics regeneration complete!")
    print("="*60 + "\n")

def regenerate_cross_cycle_validation():
    """Regenerate cross-cycle validation report."""
    print("Running cross-cycle validation...\n")
    
    validator = CrossCycleValidator(output_dir="data/validated")
    report = validator.generate_cross_cycle_report()
    
    # Save report
    report_path = Path("reports/cross_cycle_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Cross-cycle report saved: {report_path}")
    print(f"✓ Analyzed {report['cycles_analyzed']} cycles")
    print(f"✓ Date range: {report['date_range']['start']} to {report['date_range']['end']}")
    
    # Print summary
    print("\n--- Continuity Analysis ---")
    if 'continuity_trends' in report['continuity_analysis']:
        for trend in report['continuity_analysis']['continuity_trends']:
            print(f"Cycle {trend['from_cycle']} → {trend['to_cycle']}: "
                  f"Retained {trend['retained_count']} ({trend['retention_rate']:.1%}), "
                  f"New: {trend['new_count']}, Churned: {trend['churned_count']}")
    
    print("\n--- Stability Analysis ---")
    issues = report['stability_analysis'].get('volume_issues', [])
    if issues:
        print(f"Found {len(issues)} volume anomalies:")
        for issue in issues:
            print(f"  - {issue['metric']} changed by {issue['change_pct']:.1%} in {issue['cycle']}")
    else:
        print("No volume anomalies detected.")
    
    print("\n" + "="*60)
    print("Cross-cycle validation complete!")
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("REGENERATING ALL METRICS AND VALIDATIONS")
    print("="*60 + "\n")
    
    # Step 1: Regenerate quality metrics
    regenerate_quality_metrics()
    
    # Step 2: Regenerate cross-cycle validation
    regenerate_cross_cycle_validation()
    
    print("\n✓ All regeneration tasks complete!")
