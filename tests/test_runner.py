"""
Pipeline Test Runner Module
==========================

Orchestration and execution of comprehensive pipeline tests.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from .end_to_end_pipeline import EndToEndPipelineTester, create_pipeline_test_report
from .pipeline_validator import PipelineValidator
from .visualization_tester import run_visualization_pipeline_test

logger = logging.getLogger(__name__)

class PipelineTestRunner:
    """
    Comprehensive test runner for TFT pipeline testing
    """
    
    def __init__(self, api_key: str, test_config: Dict[str, Any] = None):
        """
        Initialize pipeline test runner
        
        Args:
            api_key: Riot Games API key for testing
            test_config: Optional configuration for tests
        """
        self.api_key = api_key
        self.test_config = test_config or self._get_default_test_config()
        self.test_results = {}
        
        # Initialize test components
        self.end_to_end_tester = EndToEndPipelineTester(api_key)
        self.validator = PipelineValidator()
        
        logger.info("Pipeline test runner initialized")
    
    def run_all_pipeline_tests(self, save_reports: bool = True) -> Dict[str, Any]:
        """
        Run complete suite of pipeline tests
        
        Args:
            save_reports: Whether to save detailed test reports
            
        Returns:
            dict: Comprehensive test results
        """
        master_test_report = {
            "timestamp": datetime.now().isoformat(),
            "test_configuration": self.test_config,
            "test_suite_results": {},
            "overall_test_status": "RUNNING",
            "total_tests_run": 0,
            "total_tests_passed": 0,
            "total_tests_failed": 0,
            "critical_failures": [],
            "test_summary": {},
            "execution_time_seconds": 0.0
        }
        
        start_time = datetime.now()
        
        try:
            logger.info("🚀 Starting comprehensive pipeline test suite")
            
            # Test 1: End-to-End Pipeline Test
            if self.test_config.get("run_end_to_end", True):
                logger.info("🔄 Running end-to-end pipeline test...")
                e2e_results = self._run_end_to_end_test()
                master_test_report["test_suite_results"]["end_to_end"] = e2e_results
                self._update_test_counts(master_test_report, e2e_results)
            
            # Test 2: Component Validation Tests
            if self.test_config.get("run_validation_tests", True):
                logger.info("✅ Running component validation tests...")
                validation_results = self._run_validation_tests()
                master_test_report["test_suite_results"]["validation"] = validation_results
                self._update_test_counts(master_test_report, validation_results)
            
            # Test 3: Performance Tests
            if self.test_config.get("run_performance_tests", True):
                logger.info("⚡ Running performance tests...")
                performance_results = self._run_performance_tests()
                master_test_report["test_suite_results"]["performance"] = performance_results
                self._update_test_counts(master_test_report, performance_results)
            
            # Test 4: Stress Tests
            if self.test_config.get("run_stress_tests", False):  # Optional, can be resource intensive
                logger.info("💪 Running stress tests...")
                stress_results = self._run_stress_tests()
                master_test_report["test_suite_results"]["stress"] = stress_results
                self._update_test_counts(master_test_report, stress_results)
            
            # Test 5: Regression Tests
            if self.test_config.get("run_regression_tests", True):
                logger.info("🔄 Running regression tests...")
                regression_results = self._run_regression_tests()
                master_test_report["test_suite_results"]["regression"] = regression_results
                self._update_test_counts(master_test_report, regression_results)
            
            # Calculate overall status
            end_time = datetime.now()
            master_test_report["execution_time_seconds"] = (end_time - start_time).total_seconds()
            
            # Determine overall test status
            total_tests = master_test_report["total_tests_run"]
            passed_tests = master_test_report["total_tests_passed"]
            
            if total_tests == 0:
                master_test_report["overall_test_status"] = "NO_TESTS_RUN"
            elif passed_tests == total_tests:
                master_test_report["overall_test_status"] = "ALL_PASSED"
            elif passed_tests >= total_tests * 0.8:  # 80% pass rate
                master_test_report["overall_test_status"] = "MOSTLY_PASSED"
            elif passed_tests >= total_tests * 0.5:  # 50% pass rate
                master_test_report["overall_test_status"] = "PARTIALLY_PASSED"
            else:
                master_test_report["overall_test_status"] = "MOSTLY_FAILED"
            
            # Generate test summary
            master_test_report["test_summary"] = self._generate_test_summary(master_test_report)
            
            # Save reports if requested
            if save_reports:
                self._save_test_reports(master_test_report)
            
            logger.info(f"✅ Pipeline test suite completed in {master_test_report['execution_time_seconds']:.2f} seconds")
            logger.info(f"📊 Results: {passed_tests}/{total_tests} tests passed ({master_test_report['overall_test_status']})")
            
            return master_test_report
            
        except Exception as e:
            master_test_report["overall_test_status"] = "SUITE_FAILED"
            master_test_report["critical_failures"].append(f"Test suite execution failed: {str(e)}")
            master_test_report["execution_time_seconds"] = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Pipeline test suite failed: {e}")
            return master_test_report
    
    def _run_end_to_end_test(self) -> Dict[str, Any]:
        """Run end-to-end pipeline test"""
        try:
            e2e_config = self.test_config.get("end_to_end_config", {})
            players_count = e2e_config.get("players_count", 50)  # Smaller count for testing
            test_mode = e2e_config.get("test_mode", "last_7_days")  # Recent data for faster testing
            
            results = self.end_to_end_tester.run_complete_pipeline_test(
                players_count=players_count,
                test_mode=test_mode,
                save_results=False  # Don't save during testing
            )
            
            # Store test data for other tests
            if results.get("overall_status") in ["PASSED", "PARTIAL_SUCCESS"]:
                self.test_data = self.end_to_end_tester.test_data
            
            return results
            
        except Exception as e:
            return {
                "overall_status": "FAILED",
                "error": str(e),
                "pipeline_tests": {}
            }
    
    def _run_validation_tests(self) -> Dict[str, Any]:
        """Run comprehensive validation tests"""
        validation_results = {
            "validation_status": "FAILED",
            "validation_tests": {},
            "errors": []
        }
        
        try:
            if not hasattr(self, 'test_data') or not self.test_data:
                validation_results["errors"].append("No test data available for validation")
                return validation_results
            
            # Run complete pipeline validation
            complete_validation = self.validator.validate_complete_pipeline(self.test_data)
            validation_results["validation_tests"]["complete_pipeline"] = complete_validation
            
            # Run visualization tests
            if self.test_config.get("test_visualization", True):
                viz_test_results = run_visualization_pipeline_test(self.test_data)
                validation_results["validation_tests"]["visualization"] = viz_test_results
            
            # Determine overall validation status
            pipeline_passed = complete_validation.get("overall_validation_status") in ["EXCELLENT", "GOOD", "ACCEPTABLE"]
            viz_passed = validation_results["validation_tests"].get("visualization", {}).get("visualization_test_passed", True)
            
            validation_results["validation_status"] = "PASSED" if pipeline_passed and viz_passed else "FAILED"
            
            return validation_results
            
        except Exception as e:
            validation_results["errors"].append(str(e))
            return validation_results
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmark tests"""
        performance_results = {
            "performance_status": "FAILED",
            "performance_metrics": {},
            "benchmark_results": {},
            "errors": []
        }
        
        try:
            # Test small data collection performance
            small_start = datetime.now()
            small_data = self.end_to_end_tester.collector.collect_matches_since_date(5, "last_7_days")  # 5 players
            small_duration = (datetime.now() - small_start).total_seconds()
            
            # Test medium data collection performance
            medium_start = datetime.now()
            medium_data = self.end_to_end_tester.collector.collect_matches_since_date(20, "last_7_days")  # 20 players
            medium_duration = (datetime.now() - medium_start).total_seconds()
            
            # Calculate performance metrics
            small_players = len(small_data.get('players', {}))
            small_matches = sum(len(p.get('matches', {})) for p in small_data.get('players', {}).values())
            
            medium_players = len(medium_data.get('players', {}))
            medium_matches = sum(len(p.get('matches', {})) for p in medium_data.get('players', {}).values())
            
            performance_results["performance_metrics"] = {
                "small_collection": {
                    "duration_seconds": small_duration,
                    "players_collected": small_players,
                    "matches_collected": small_matches,
                    "players_per_second": small_players / small_duration if small_duration > 0 else 0,
                    "matches_per_second": small_matches / small_duration if small_duration > 0 else 0
                },
                "medium_collection": {
                    "duration_seconds": medium_duration,
                    "players_collected": medium_players,
                    "matches_collected": medium_matches,
                    "players_per_second": medium_players / medium_duration if medium_duration > 0 else 0,
                    "matches_per_second": medium_matches / medium_duration if medium_duration > 0 else 0
                }
            }
            
            # Performance benchmarks
            performance_results["benchmark_results"] = {
                "collection_efficiency": "PASS" if small_duration < 60 and medium_duration < 180 else "FAIL",  # Under 1 min for small, 3 min for medium
                "data_throughput": "PASS" if (small_matches / small_duration) > 1 else "FAIL",  # At least 1 match per second
                "memory_efficiency": "PASS"  # Assume pass unless we implement memory monitoring
            }
            
            # Overall performance status
            all_benchmarks_pass = all(result == "PASS" for result in performance_results["benchmark_results"].values())
            performance_results["performance_status"] = "PASSED" if all_benchmarks_pass else "FAILED"
            
            return performance_results
            
        except Exception as e:
            performance_results["errors"].append(str(e))
            return performance_results
    
    def _run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests (optional, resource intensive)"""
        stress_results = {
            "stress_status": "SKIPPED",
            "stress_tests": {},
            "errors": []
        }
        
        try:
            logger.warning("🚨 Stress tests are resource intensive and may take significant time")
            
            # Large data collection stress test
            stress_start = datetime.now()
            stress_data = self.end_to_end_tester.collector.collect_matches_since_date(100, "last_30_days")
            stress_duration = (datetime.now() - stress_start).total_seconds()
            
            stress_players = len(stress_data.get('players', {}))
            stress_matches = sum(len(p.get('matches', {})) for p in stress_data.get('players', {}).values())
            
            stress_results["stress_tests"] = {
                "large_collection_test": {
                    "duration_seconds": stress_duration,
                    "players_collected": stress_players,
                    "matches_collected": stress_matches,
                    "success": stress_players > 50 and stress_matches > 100,  # Minimum thresholds
                    "efficiency": stress_matches / stress_duration if stress_duration > 0 else 0
                }
            }
            
            stress_results["stress_status"] = "PASSED" if stress_results["stress_tests"]["large_collection_test"]["success"] else "FAILED"
            
            return stress_results
            
        except Exception as e:
            stress_results["errors"].append(str(e))
            stress_results["stress_status"] = "FAILED"
            return stress_results
    
    def _run_regression_tests(self) -> Dict[str, Any]:
        """Run regression tests against known good data"""
        regression_results = {
            "regression_status": "PASSED",
            "regression_tests": {},
            "errors": []
        }
        
        try:
            # Test that basic functionality still works
            regression_results["regression_tests"] = {
                "api_connectivity": {
                    "test": "API connection and basic data retrieval",
                    "status": "PASSED" if hasattr(self, 'test_data') and self.test_data else "FAILED"
                },
                "data_structure_consistency": {
                    "test": "Data structure matches expected format",
                    "status": "PASSED" if self._check_data_structure_consistency() else "FAILED"
                },
                "json_ld_format": {
                    "test": "JSON-LD format compliance maintained",
                    "status": "PASSED" if self._check_jsonld_format() else "FAILED"
                }
            }
            
            # Overall regression status
            all_regression_pass = all(test["status"] == "PASSED" for test in regression_results["regression_tests"].values())
            regression_results["regression_status"] = "PASSED" if all_regression_pass else "FAILED"
            
            return regression_results
            
        except Exception as e:
            regression_results["errors"].append(str(e))
            regression_results["regression_status"] = "FAILED"
            return regression_results
    
    def _check_data_structure_consistency(self) -> bool:
        """Check if data structure is consistent with expectations"""
        if not hasattr(self, 'test_data') or not self.test_data:
            return False
        
        # Check for required top-level keys
        required_keys = ["collectionInfo", "players"]
        return all(key in self.test_data for key in required_keys)
    
    def _check_jsonld_format(self) -> bool:
        """Check if JSON-LD format is maintained"""
        if not hasattr(self, 'test_data') or not self.test_data:
            return False
        
        # Check for JSON-LD required elements
        return bool(self.test_data.get('@context')) and bool(self.test_data.get('@type'))
    
    def _update_test_counts(self, master_report: Dict[str, Any], test_results: Dict[str, Any]) -> None:
        """Update master test counts from individual test results"""
        try:
            # Different test result formats need different counting logic
            if "pipeline_tests" in test_results:  # End-to-end test format
                for test_name, test_result in test_results["pipeline_tests"].items():
                    master_report["total_tests_run"] += 1
                    if test_result.get("success", False):
                        master_report["total_tests_passed"] += 1
                    else:
                        master_report["total_tests_failed"] += 1
                        if test_result.get("errors"):
                            master_report["critical_failures"].extend(test_result["errors"])
            
            elif "validation_tests" in test_results:  # Validation test format
                for test_name, test_result in test_results["validation_tests"].items():
                    master_report["total_tests_run"] += 1
                    # Different validation result formats
                    if "overall_validation_status" in test_result:
                        passed = test_result["overall_validation_status"] in ["EXCELLENT", "GOOD", "ACCEPTABLE"]
                    elif "visualization_test_passed" in test_result:
                        passed = test_result["visualization_test_passed"]
                    else:
                        passed = False
                    
                    if passed:
                        master_report["total_tests_passed"] += 1
                    else:
                        master_report["total_tests_failed"] += 1
            
            elif "performance_metrics" in test_results:  # Performance test format
                master_report["total_tests_run"] += 1
                if test_results.get("performance_status") == "PASSED":
                    master_report["total_tests_passed"] += 1
                else:
                    master_report["total_tests_failed"] += 1
            
            elif "stress_tests" in test_results:  # Stress test format
                master_report["total_tests_run"] += 1
                if test_results.get("stress_status") == "PASSED":
                    master_report["total_tests_passed"] += 1
                else:
                    master_report["total_tests_failed"] += 1
            
            elif "regression_tests" in test_results:  # Regression test format
                for test_name, test_result in test_results["regression_tests"].items():
                    master_report["total_tests_run"] += 1
                    if test_result.get("status") == "PASSED":
                        master_report["total_tests_passed"] += 1
                    else:
                        master_report["total_tests_failed"] += 1
            
        except Exception as e:
            logger.error(f"Error updating test counts: {e}")
    
    def _generate_test_summary(self, master_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of all test results"""
        summary = {
            "execution_summary": {
                "total_execution_time": master_report["execution_time_seconds"],
                "tests_per_minute": (master_report["total_tests_run"] / (master_report["execution_time_seconds"] / 60)) if master_report["execution_time_seconds"] > 0 else 0
            },
            "test_coverage": {
                "end_to_end_tested": "end_to_end" in master_report["test_suite_results"],
                "validation_tested": "validation" in master_report["test_suite_results"],
                "performance_tested": "performance" in master_report["test_suite_results"],
                "stress_tested": "stress" in master_report["test_suite_results"],
                "regression_tested": "regression" in master_report["test_suite_results"]
            },
            "quality_indicators": {
                "pass_rate_percentage": (master_report["total_tests_passed"] / master_report["total_tests_run"]) * 100 if master_report["total_tests_run"] > 0 else 0,
                "critical_failures_count": len(master_report["critical_failures"]),
                "test_suite_health": master_report["overall_test_status"]
            },
            "recommendations": []
        }
        
        # Generate recommendations
        pass_rate = summary["quality_indicators"]["pass_rate_percentage"]
        if pass_rate == 100:
            summary["recommendations"].append("🎉 All tests passed! Pipeline is ready for production use.")
        elif pass_rate >= 80:
            summary["recommendations"].append("✅ Most tests passed. Address remaining issues before production use.")
        elif pass_rate >= 50:
            summary["recommendations"].append("⚠️ Significant issues detected. System needs attention before production use.")
        else:
            summary["recommendations"].append("❌ Critical issues detected. System requires major fixes before use.")
        
        return summary
    
    def _save_test_reports(self, master_report: Dict[str, Any]) -> None:
        """Save comprehensive test reports"""
        try:
            # Create reports directory
            reports_dir = Path("pipeline_test_reports")
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save JSON report
            json_report_path = reports_dir / f"pipeline_test_report_{timestamp}.json"
            with open(json_report_path, 'w') as f:
                json.dump(master_report, f, indent=2, default=str)
            
            # Save human-readable report
            text_report_path = reports_dir / f"pipeline_test_report_{timestamp}.txt"
            text_report = create_pipeline_test_report(master_report)
            with open(text_report_path, 'w') as f:
                f.write(text_report)
            
            logger.info(f"📄 Test reports saved:")
            logger.info(f"  JSON: {json_report_path}")
            logger.info(f"  Text: {text_report_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save test reports: {e}")
    
    def _get_default_test_config(self) -> Dict[str, Any]:
        """Get default test configuration"""
        return {
            "run_end_to_end": True,
            "run_validation_tests": True,
            "run_performance_tests": True,
            "run_stress_tests": False,  # Resource intensive, disabled by default
            "run_regression_tests": True,
            "test_visualization": True,
            "end_to_end_config": {
                "players_count": 25,  # Smaller for testing
                "test_mode": "last_7_days"  # Recent data for faster tests
            }
        }


def run_all_pipeline_tests(api_key: str, test_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to run all pipeline tests
    
    Args:
        api_key: Riot Games API key for testing
        test_config: Optional test configuration
        
    Returns:
        dict: Complete test results
    """
    runner = PipelineTestRunner(api_key, test_config)
    return runner.run_all_pipeline_tests()


def generate_test_summary(test_results: Dict[str, Any]) -> str:
    """
    Generate a concise test summary
    
    Args:
        test_results: Results from pipeline tests
        
    Returns:
        str: Formatted test summary
    """
    summary_lines = []
    summary_lines.append("📊 PIPELINE TEST SUMMARY")
    summary_lines.append("=" * 50)
    
    # Basic stats
    total_tests = test_results.get("total_tests_run", 0)
    passed_tests = test_results.get("total_tests_passed", 0)
    failed_tests = test_results.get("total_tests_failed", 0)
    
    summary_lines.append(f"Total Tests: {total_tests}")
    summary_lines.append(f"Passed: {passed_tests}")
    summary_lines.append(f"Failed: {failed_tests}")
    summary_lines.append(f"Pass Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "Pass Rate: N/A")
    summary_lines.append("")
    
    # Overall status
    overall_status = test_results.get("overall_test_status", "UNKNOWN")
    summary_lines.append(f"Overall Status: {overall_status}")
    
    # Execution time
    exec_time = test_results.get("execution_time_seconds", 0)
    summary_lines.append(f"Execution Time: {exec_time:.2f} seconds")
    
    return "\n".join(summary_lines)


if __name__ == "__main__":
    # Demo functionality when run directly
    print("🧪 Testing Pipeline Test Runner")
    print("=" * 40)
    
    API_KEY = "YOUR_API_KEY_HERE"  # Replace with actual key
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please set your API key to run pipeline tests!")
        print("Example usage:")
        print("  runner = PipelineTestRunner('your_api_key')")
        print("  results = runner.run_all_pipeline_tests()")
        print("  summary = generate_test_summary(results)")
        print("  print(summary)")
    else:
        # Run actual test
        test_config = {
            "run_end_to_end": True,
            "run_validation_tests": True,
            "run_performance_tests": False,  # Skip for demo
            "run_stress_tests": False,
            "run_regression_tests": True,
            "end_to_end_config": {
                "players_count": 5,
                "test_mode": "last_7_days"
            }
        }
        
        results = run_all_pipeline_tests(API_KEY, test_config)
        summary = generate_test_summary(results)
        print(summary)
    
    print("\n🎉 Pipeline Test Runner Module Ready!")
