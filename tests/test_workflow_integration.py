#!/usr/bin/env python3
"""
Workflow Integration Test Script
=================================

Automates comprehensive testing of the Snakemake workflow pipeline.
Tests all stages: collection, validation, transformation, quality, provenance, backup, and cross-cycle validation.
"""

import subprocess
import json
import os
import sys
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

class WorkflowIntegrationTester:
    def __init__(self, test_dates: List[str], project_root: str = "."):
        self.test_dates = test_dates
        self.project_root = Path(project_root)
        self.results = {
            'test_run_timestamp': datetime.now().isoformat(),
            'test_dates': test_dates,
            'scenarios': {},
            'overall_status': 'pending'
        }
        
    def run_workflow(self, dates: List[str], parallel_jobs: int = 1, dry_run: bool = False) -> Tuple[bool, str]:
        """Execute Snakemake workflow with specified dates"""
        dates_str = ','.join(dates) if len(dates) > 1 else dates[0]
        
        cmd = [
            'snakemake',
            '--config', f'collection_date=[{dates_str}]',
            '-j', str(parallel_jobs)
        ]
        
        if dry_run:
            cmd.append('-n')
            
        print(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            success = result.returncode == 0
            output = result.stdout + "\n" + result.stderr
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "Workflow execution timed out after 30 minutes"
        except Exception as e:
            return False, f"Workflow execution failed: {str(e)}"
    
    def verify_file_exists(self, filepath: Path) -> Tuple[bool, str]:
        """Verify a file exists and is not empty"""
        if not filepath.exists():
            return False, f"File does not exist: {filepath}"
        
        if filepath.stat().st_size == 0:
            return False, f"File is empty: {filepath}"
            
        return True, f"File exists ({filepath.stat().st_size} bytes)"
    
    def verify_json_file(self, filepath: Path, required_keys: List[str] = None) -> Tuple[bool, str]:
        """Verify a JSON file is valid and contains required keys"""
        exists, msg = self.verify_file_exists(filepath)
        if not exists:
            return False, msg
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            if required_keys:
                missing_keys = [key for key in required_keys if key not in data]
                if missing_keys:
                    return False, f"Missing required keys: {missing_keys}"
                    
            return True, f"Valid JSON with {len(data)} top-level keys"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    def verify_tarball(self, filepath: Path) -> Tuple[bool, str]:
        """Verify a tar.gz archive is valid"""
        exists, msg = self.verify_file_exists(filepath)
        if not exists:
            return False, msg
            
        try:
            with tarfile.open(filepath, 'r:gz') as tar:
                members = tar.getmembers()
                return True, f"Valid tar.gz with {len(members)} files"
        except Exception as e:
            return False, f"Invalid tar.gz: {str(e)}"
    
    def verify_outputs(self, date: str) -> Dict[str, Any]:
        """Verify all expected outputs for a date"""
        results = {
            'date': date,
            'outputs': {},
            'all_passed': True
        }
        
        # 1. Raw data
        raw_file = self.project_root / f"data/raw/tft_collection_{date}.json"
        success, msg = self.verify_json_file(raw_file, ['@context', 'players', 'matches'])
        results['outputs']['raw_data'] = {'passed': success, 'message': msg, 'file': str(raw_file)}
        results['all_passed'] = results['all_passed'] and success
        
        # 2. Validated data
        validated_file = self.project_root / f"data/validated/tft_collection_{date}.json"
        success, msg = self.verify_json_file(validated_file)
        results['outputs']['validated_data'] = {'passed': success, 'message': msg, 'file': str(validated_file)}
        results['all_passed'] = results['all_passed'] and success
        
        # 3. Validation report
        validation_report = self.project_root / f"reports/validation_{date}.json"
        success, msg = self.verify_json_file(validation_report, ['validation', 'quality_score'])
        results['outputs']['validation_report'] = {'passed': success, 'message': msg, 'file': str(validation_report)}
        results['all_passed'] = results['all_passed'] and success
        
        # 4. Transformed data
        transformed_file = self.project_root / f"data/transformed/tft_collection_{date}.jsonld"
        success, msg = self.verify_json_file(transformed_file, ['@context'])
        results['outputs']['transformed_data'] = {'passed': success, 'message': msg, 'file': str(transformed_file)}
        results['all_passed'] = results['all_passed'] and success
        
        # 5. Quality report
        quality_report = self.project_root / f"reports/quality_{date}.json"
        success, msg = self.verify_json_file(quality_report)
        results['outputs']['quality_report'] = {'passed': success, 'message': msg, 'file': str(quality_report)}
        results['all_passed'] = results['all_passed'] and success
        
        # 6. Provenance
        provenance_file = self.project_root / f"provenance/workflow_{date}.prov.json"
        success, msg = self.verify_json_file(provenance_file)
        results['outputs']['provenance'] = {'passed': success, 'message': msg, 'file': str(provenance_file)}
        results['all_passed'] = results['all_passed'] and success
        
        # 7. Backup
        backup_file = self.project_root / f"backups/backup_{date}.tar.gz"
        success, msg = self.verify_tarball(backup_file)
        results['outputs']['backup'] = {'passed': success, 'message': msg, 'file': str(backup_file)}
        results['all_passed'] = results['all_passed'] and success
        
        # 8. Cross-cycle validation
        cross_cycle_file = self.project_root / f"reports/cross_cycle_{date}.json"
        success, msg = self.verify_json_file(cross_cycle_file, ['cycles_analyzed', 'continuity_analysis', 'stability_analysis'])
        results['outputs']['cross_cycle_validation'] = {'passed': success, 'message': msg, 'file': str(cross_cycle_file)}
        results['all_passed'] = results['all_passed'] and success
        
        return results
    
    def test_single_date(self, date: str) -> Dict[str, Any]:
        """Test Scenario 1: Single date execution"""
        print(f"\n{'='*60}")
        print(f"Test Scenario 1: Single Date Execution ({date})")
        print(f"{'='*60}")
        
        scenario_results = {
            'scenario': 'single_date',
            'date': date,
            'workflow_execution': {},
            'output_verification': {},
            'passed': False
        }
        
        # Execute workflow
        success, output = self.run_workflow([date], parallel_jobs=1)
        scenario_results['workflow_execution'] = {
            'success': success,
            'output_preview': output[:500] if output else ""
        }
        
        if not success:
            print(f"❌ Workflow execution failed")
            return scenario_results
        
        print(f"✅ Workflow execution succeeded")
        
        # Verify outputs
        verification = self.verify_outputs(date)
        scenario_results['output_verification'] = verification
        scenario_results['passed'] = verification['all_passed']
        
        # Print results
        for output_name, output_result in verification['outputs'].items():
            status = "✅" if output_result['passed'] else "❌"
            print(f"{status} {output_name}: {output_result['message']}")
        
        return scenario_results
    
    def test_multiple_dates(self, dates: List[str]) -> Dict[str, Any]:
        """Test Scenario 2: Multiple date execution"""
        print(f"\n{'='*60}")
        print(f"Test Scenario 2: Multiple Date Execution ({', '.join(dates)})")
        print(f"{'='*60}")
        
        scenario_results = {
            'scenario': 'multiple_dates',
            'dates': dates,
            'workflow_execution': {},
            'output_verification': {},
            'passed': False
        }
        
        # Execute workflow with parallel jobs
        success, output = self.run_workflow(dates, parallel_jobs=2)
        scenario_results['workflow_execution'] = {
            'success': success,
            'output_preview': output[:500] if output else ""
        }
        
        if not success:
            print(f"❌ Workflow execution failed")
            return scenario_results
        
        print(f"✅ Workflow execution succeeded")
        
        # Verify outputs for each date
        all_passed = True
        for date in dates:
            print(f"\nVerifying outputs for {date}:")
            verification = self.verify_outputs(date)
            scenario_results['output_verification'][date] = verification
            all_passed = all_passed and verification['all_passed']
            
            for output_name, output_result in verification['outputs'].items():
                status = "✅" if output_result['passed'] else "❌"
                print(f"  {status} {output_name}: {output_result['message']}")
        
        scenario_results['passed'] = all_passed
        return scenario_results
    
    def test_dry_run(self, dates: List[str]) -> Dict[str, Any]:
        """Test Scenario: Dry run validation"""
        print(f"\n{'='*60}")
        print(f"Test Scenario: Dry Run Validation")
        print(f"{'='*60}")
        
        scenario_results = {
            'scenario': 'dry_run',
            'dates': dates,
            'passed': False
        }
        
        success, output = self.run_workflow(dates, dry_run=True)
        scenario_results['success'] = success
        scenario_results['output_preview'] = output[:500] if output else ""
        scenario_results['passed'] = success
        
        status = "✅" if success else "❌"
        print(f"{status} Dry run {'succeeded' if success else 'failed'}")
        
        return scenario_results
    
    def generate_report(self, output_file: str = "Documents/WORKFLOW_INTEGRATION_TEST_RESULTS.md"):
        """Generate comprehensive test report"""
        report_path = self.project_root / output_file
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine overall status
        all_scenarios_passed = all(
            scenario.get('passed', False) 
            for scenario in self.results['scenarios'].values()
        )
        self.results['overall_status'] = 'PASSED' if all_scenarios_passed else 'FAILED'
        
        # Generate markdown report
        with open(report_path, 'w') as f:
            f.write("# Workflow Integration Test Results\n\n")
            f.write(f"**Test Run**: {self.results['test_run_timestamp']}\n")
            f.write(f"**Test Dates**: {', '.join(self.results['test_dates'])}\n")
            f.write(f"**Overall Status**: {'✅ PASSED' if all_scenarios_passed else '❌ FAILED'}\n\n")
            f.write("---\n\n")
            
            # Scenario results
            for scenario_name, scenario_data in self.results['scenarios'].items():
                status = "✅ PASSED" if scenario_data.get('passed', False) else "❌ FAILED"
                f.write(f"## {scenario_name.replace('_', ' ').title()}\n\n")
                f.write(f"**Status**: {status}\n\n")
                
                # Workflow execution
                if 'workflow_execution' in scenario_data:
                    exec_status = "✅" if scenario_data['workflow_execution'].get('success', False) else "❌"
                    f.write(f"**Workflow Execution**: {exec_status}\n\n")
                
                # Output verification
                if 'output_verification' in scenario_data:
                    f.write("**Output Verification**:\n\n")
                    
                    # Handle single date vs multiple dates
                    verifications = scenario_data['output_verification']
                    if 'outputs' in verifications:
                        # Single date
                        verifications = {scenario_data.get('date', 'unknown'): verifications}
                    
                    for date, verification in verifications.items():
                        f.write(f"### Date: {date}\n\n")
                        f.write("| Output | Status | Message |\n")
                        f.write("|--------|--------|----------|\n")
                        
                        for output_name, output_result in verification.get('outputs', {}).items():
                            status_icon = "✅" if output_result['passed'] else "❌"
                            f.write(f"| {output_name} | {status_icon} | {output_result['message']} |\n")
                        
                        f.write("\n")
                
                f.write("---\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            total_scenarios = len(self.results['scenarios'])
            passed_scenarios = sum(1 for s in self.results['scenarios'].values() if s.get('passed', False))
            f.write(f"- **Total Scenarios**: {total_scenarios}\n")
            f.write(f"- **Passed**: {passed_scenarios}\n")
            f.write(f"- **Failed**: {total_scenarios - passed_scenarios}\n")
            f.write(f"- **Success Rate**: {(passed_scenarios/total_scenarios*100):.1f}%\n")
        
        print(f"\n📄 Test report generated: {report_path}")
        
        # Also save JSON results
        json_path = report_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 JSON results saved: {json_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Integration Testing")
    parser.add_argument('--dates', required=True, help='Comma-separated list of test dates (YYYYMMDD)')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--skip-dry-run', action='store_true', help='Skip dry run test')
    
    args = parser.parse_args()
    
    test_dates = [d.strip() for d in args.dates.split(',')]
    
    print(f"{'='*60}")
    print(f"WORKFLOW INTEGRATION TESTING")
    print(f"{'='*60}")
    print(f"Test Dates: {', '.join(test_dates)}")
    print(f"Project Root: {args.project_root}")
    print(f"{'='*60}\n")
    
    tester = WorkflowIntegrationTester(test_dates, args.project_root)
    
    # Test Scenario: Dry Run
    if not args.skip_dry_run:
        dry_run_result = tester.test_dry_run(test_dates)
        tester.results['scenarios']['dry_run'] = dry_run_result
        
        if not dry_run_result['passed']:
            print("\n⚠️  Dry run failed. Stopping tests.")
            tester.generate_report()
            sys.exit(1)
    
    # Test Scenario 1: Single Date
    if len(test_dates) >= 1:
        single_result = tester.test_single_date(test_dates[0])
        tester.results['scenarios']['single_date'] = single_result
    
    # Test Scenario 2: Multiple Dates
    if len(test_dates) >= 3:
        multiple_result = tester.test_multiple_dates(test_dates[:3])
        tester.results['scenarios']['multiple_dates'] = multiple_result
    
    # Generate report
    tester.generate_report()
    
    # Exit with appropriate code
    if tester.results['overall_status'] == 'PASSED':
        print("\n✅ All tests PASSED")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
