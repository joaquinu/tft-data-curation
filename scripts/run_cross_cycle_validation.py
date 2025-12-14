#!/usr/bin/env python3
"""
Script to run cross-cycle validation on TFT data collections.
"""

import os
import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from quality_assurance import run_validation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run cross-cycle validation on TFT data collections.")
    parser.add_argument('--input-dir', default='data/validated', help='Directory containing collection files')
    parser.add_argument('--report-file', default='reports/cross_cycle_report.json', help='Path to save the validation report')
    return parser.parse_args()

def main():
    args = parse_arguments()
    output_dir = args.input_dir
    report_file = args.report_file
    
    report_path = Path(report_file)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Running cross-cycle validation on {output_dir}...")
    
    try:
        report = run_validation(output_dir, report_file)
        
        if "error" in report:
            print(f"Error: {report['error']}")
            return
            
        print(f"\nValidation Complete!")
        print(f"Analyzed {report['cycles_analyzed']} cycles from {report['date_range']['start']} to {report['date_range']['end']}")
        
        print("\n--- Continuity Analysis ---")
        if 'continuity_trends' in report['continuity_analysis']:
            for trend in report['continuity_analysis']['continuity_trends']:
                print(f"Cycle {trend['to_cycle']}: Retained {trend['retained_count']} players ({trend['retention_rate']:.1%}), New: {trend['new_count']}, Churned: {trend['churned_count']}")
        else:
            print(report['continuity_analysis'].get('status', 'No continuity data'))
            
        print("\n--- Stability Analysis ---")
        issues = report['stability_analysis'].get('volume_issues', [])
        if issues:
            print(f"Found {len(issues)} volume anomalies:")
            for issue in issues:
                print(f"  - {issue['metric']} changed by {issue['change_pct']:.1%} in {issue['cycle']}")
        else:
            print("No volume anomalies detected.")
            
        print(f"\nFull report saved to {report_file}")
        
    except Exception as e:
        print(f"Failed to run validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
