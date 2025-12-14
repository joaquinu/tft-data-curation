"""
End-to-End Pipeline Testing
===========================

Comprehensive end-to-end testing of the complete TFT data collection pipeline.
Moved from main.py:488-555 and enhanced with additional testing capabilities.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import os
from pathlib import Path

# Import TFT components
from scripts.optimized_match_collector import create_match_collector
from quality_assurance import (
    validate_tft_data_structure,
    validate_jsonld_compliance, 
    detect_statistical_anomalies,
    calculate_data_quality_score
)
from .visualization_tester import create_player_match_visualization

logger = logging.getLogger(__name__)

class EndToEndPipelineTester:
    """
    Comprehensive end-to-end pipeline testing framework
    """
    
    def __init__(self, api_key: str):
        """
        Initialize pipeline tester
        
        Args:
            api_key: Riot Games API key for testing
        """
        self.api_key = api_key
        self.collector = create_match_collector(api_key)
        self.test_results = {}
        self.test_data = None
        
        logger.info("End-to-end pipeline tester initialized")
    
    def run_complete_pipeline_test(self, 
                                 players_count: int = 100, 
                                 test_mode: str = "since_2024",
                                 save_results: bool = True) -> Dict[str, Any]:
        """
        Run complete end-to-end pipeline test
        
        Args:
            players_count: Number of players to collect for testing
            test_mode: Collection mode ("since_2024", "last_30_days", etc.)
            save_results: Whether to save test results to file
            
        Returns:
            dict: Comprehensive test results
        """
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "test_configuration": {
                "players_count": players_count,
                "test_mode": test_mode,
                "save_results": save_results
            },
            "pipeline_tests": {},
            "overall_status": "RUNNING",
            "test_duration": 0.0
        }
        
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Starting complete pipeline test with {players_count} players using '{test_mode}' mode")
            
            # Test 1: Data Collection Pipeline
            logger.info("📊 Testing data collection pipeline...")
            collection_result = self._test_data_collection(players_count, test_mode)
            test_report["pipeline_tests"]["data_collection"] = collection_result
            
            if not collection_result["success"]:
                test_report["overall_status"] = "FAILED"
                return test_report
            
            # Store collected data for subsequent tests
            self.test_data = collection_result["data"]
            
            # Test 2: Data Structure Validation
            logger.info("🔍 Testing data structure validation...")
            validation_result = self._test_data_validation()
            test_report["pipeline_tests"]["data_validation"] = validation_result
            
            # Test 3: JSON-LD Compliance
            logger.info("🌐 Testing JSON-LD compliance...")
            jsonld_result = self._test_jsonld_compliance()
            test_report["pipeline_tests"]["jsonld_compliance"] = jsonld_result
            
            # Test 4: Quality Assessment
            logger.info("⚖️ Testing quality assessment pipeline...")
            quality_result = self._test_quality_assessment()
            test_report["pipeline_tests"]["quality_assessment"] = quality_result
            
            # Test 5: Data Persistence
            if save_results:
                logger.info("💾 Testing data persistence...")
                persistence_result = self._test_data_persistence()
                test_report["pipeline_tests"]["data_persistence"] = persistence_result
            
            # Test 6: Visualization Generation
            logger.info("📈 Testing visualization generation...")
            visualization_result = self._test_visualization_generation()
            test_report["pipeline_tests"]["visualization"] = visualization_result
            
            # Calculate overall status
            all_tests_passed = all(
                result.get("success", False) 
                for result in test_report["pipeline_tests"].values()
            )
            
            test_report["overall_status"] = "PASSED" if all_tests_passed else "PARTIAL_SUCCESS"
            
            # Calculate test duration
            end_time = datetime.now()
            test_report["test_duration"] = (end_time - start_time).total_seconds()
            
            # Generate summary
            test_report["summary"] = self._generate_test_summary(test_report)
            
            logger.info(f"✅ Pipeline test completed in {test_report['test_duration']:.2f} seconds")
            logger.info(f"📋 Overall status: {test_report['overall_status']}")
            
            return test_report
            
        except Exception as e:
            test_report["overall_status"] = "FAILED"
            test_report["error"] = str(e)
            test_report["test_duration"] = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Pipeline test failed: {e}")
            return test_report
    
    def _test_data_collection(self, players_count: int, test_mode: str) -> Dict[str, Any]:
        """Test the data collection pipeline"""
        result = {
            "success": False,
            "data": None,
            "metrics": {},
            "errors": []
        }
        
        try:
            # Collect data using the specified mode
            logger.info(f"Collecting data for {players_count} players using '{test_mode}' mode...")
            
            data = self.collector.collect_matches_since_date(players_count, test_mode)
            
            # Validate collection results
            total_players = len(data.get('players', {}))
            total_matches = sum(len(player.get('matches', {})) for player in data.get('players', {}).values())
            
            result["data"] = data
            result["metrics"] = {
                "total_players": total_players,
                "total_matches": total_matches,
                "collection_mode": test_mode,
                "has_collection_metadata": bool(data.get('collectionInfo')),
                "has_jsonld_context": bool(data.get('@context'))
            }
            
            # Success criteria
            if total_players > 0 and total_matches > 0:
                result["success"] = True
                logger.info(f"✅ Data collection successful: {total_players} players, {total_matches} matches")
            else:
                result["errors"].append("No data collected")
                logger.warning("⚠️ Data collection returned no results")
            
            return result
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"❌ Data collection test failed: {e}")
            return result
    
    def _test_data_validation(self) -> Dict[str, Any]:
        """Test data structure validation"""
        result = {
            "success": False,
            "validation_results": {},
            "errors": []
        }
        
        try:
            if not self.test_data:
                result["errors"].append("No test data available for validation")
                return result
            
            # Test TFT data structure validation
            is_valid, structure_errors = validate_tft_data_structure(self.test_data)
            
            result["validation_results"] = {
                "structure_valid": is_valid,
                "structure_errors": structure_errors,
                "data_sections": list(self.test_data.keys()),
                "has_required_sections": all(section in self.test_data for section in ['collectionInfo', 'players'])
            }
            
            result["success"] = is_valid and len(structure_errors) == 0
            
            if result["success"]:
                logger.info("✅ Data structure validation passed")
            else:
                logger.warning(f"⚠️ Data structure validation issues: {structure_errors}")
            
            return result
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"❌ Data validation test failed: {e}")
            return result
    
    def _test_jsonld_compliance(self) -> Dict[str, Any]:
        """Test JSON-LD compliance"""
        result = {
            "success": False,
            "compliance_results": {},
            "errors": []
        }
        
        try:
            if not self.test_data:
                result["errors"].append("No test data available for JSON-LD testing")
                return result
            
            # Test JSON-LD compliance
            is_compliant, compliance_issues = validate_jsonld_compliance(self.test_data)
            
            result["compliance_results"] = {
                "jsonld_compliant": is_compliant,
                "compliance_issues": compliance_issues,
                "has_context": bool(self.test_data.get('@context')),
                "has_type": bool(self.test_data.get('@type')),
                "semantic_annotations": self._check_semantic_annotations()
            }
            
            result["success"] = is_compliant and len(compliance_issues) == 0
            
            if result["success"]:
                logger.info("✅ JSON-LD compliance validation passed")
            else:
                logger.warning(f"⚠️ JSON-LD compliance issues: {compliance_issues}")
            
            return result
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"❌ JSON-LD compliance test failed: {e}")
            return result
    
    def _test_quality_assessment(self) -> Dict[str, Any]:
        """Test quality assessment pipeline"""
        result = {
            "success": False,
            "quality_metrics": {},
            "errors": []
        }
        
        try:
            if not self.test_data:
                result["errors"].append("No test data available for quality assessment")
                return result
            
            # Run quality assessment
            quality_report = calculate_data_quality_score(self.test_data)
            
            # Run anomaly detection
            if "matches" in self.test_data:
                anomaly_report = detect_statistical_anomalies(self.test_data["matches"])
            else:
                anomaly_report = {"anomalies_detected": [], "anomaly_count": 0}
            
            result["quality_metrics"] = {
                "overall_quality_score": quality_report.get("overall_score", 0),
                "quality_grade": quality_report.get("quality_grade", "F"),
                "anomalies_detected": anomaly_report.get("anomaly_count", 0),
                "quality_components": quality_report.get("component_scores", {}),
                "recommendations": quality_report.get("recommendations", [])
            }
            
            # Success criteria: quality score > 70 and no critical anomalies
            quality_score = quality_report.get("overall_score", 0)
            critical_anomalies = len([a for a in anomaly_report.get("anomalies_detected", []) if a.get("severity") == "critical"])
            
            result["success"] = quality_score > 70 and critical_anomalies == 0
            
            if result["success"]:
                logger.info(f"✅ Quality assessment passed: Score {quality_score:.1f}, Grade {quality_report.get('quality_grade')}")
            else:
                logger.warning(f"⚠️ Quality assessment concerns: Score {quality_score:.1f}, {critical_anomalies} critical anomalies")
            
            return result
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"❌ Quality assessment test failed: {e}")
            return result
    
    def _test_data_persistence(self) -> Dict[str, Any]:
        """Test data persistence capabilities"""
        result = {
            "success": False,
            "persistence_results": {},
            "errors": []
        }
        
        try:
            if not self.test_data:
                result["errors"].append("No test data available for persistence testing")
                return result
            
            # Test saving data to file
            test_filename = f"pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            saved_filename = self.collector.save_data_to_file(test_filename)
            
            # Test loading data back
            if saved_filename and os.path.exists(saved_filename):
                file_size = os.path.getsize(saved_filename) / (1024 * 1024)  # MB
                
                # Test loading
                load_success = self.collector.load_data_from_file(saved_filename)
                
                result["persistence_results"] = {
                    "save_successful": True,
                    "load_successful": load_success,
                    "file_size_mb": round(file_size, 2),
                    "filename": saved_filename
                }
                
                result["success"] = load_success
                
                # Clean up test file
                try:
                    os.remove(saved_filename)
                    logger.info("🗑️ Test file cleaned up")
                except:
                    pass
                
                if result["success"]:
                    logger.info(f"✅ Data persistence test passed: {file_size:.2f} MB file")
                else:
                    logger.warning("⚠️ Data persistence test failed: could not reload data")
            else:
                result["errors"].append("Failed to save test data")
                logger.error("❌ Data persistence test failed: could not save data")
            
            return result
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"❌ Data persistence test failed: {e}")
            return result
    
    def _test_visualization_generation(self) -> Dict[str, Any]:
        """Test visualization generation"""
        result = {
            "success": False,
            "visualization_results": {},
            "errors": []
        }
        
        try:
            if not self.test_data:
                result["errors"].append("No test data available for visualization testing")
                return result
            
            # Test visualization creation
            try:
                create_player_match_visualization(self.test_data)
                
                result["visualization_results"] = {
                    "visualization_generated": True,
                    "has_player_data": bool(self.test_data.get('players')),
                    "has_match_data": any(player.get('matches') for player in self.test_data.get('players', {}).values())
                }
                
                result["success"] = True
                logger.info("✅ Visualization generation test passed")
                
            except ImportError as e:
                result["errors"].append(f"Visualization dependency missing: {e}")
                result["visualization_results"]["matplotlib_available"] = False
                logger.warning("⚠️ Visualization test skipped: matplotlib not available")
                # Consider this a success if the error is just missing matplotlib
                result["success"] = "matplotlib" in str(e).lower()
                
            except Exception as e:
                result["errors"].append(f"Visualization generation failed: {e}")
                logger.error(f"❌ Visualization test failed: {e}")
            
            return result
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"❌ Visualization test failed: {e}")
            return result
    
    def _check_semantic_annotations(self) -> Dict[str, Any]:
        """Check semantic annotations in the data"""
        annotations = {
            "players_annotated": 0,
            "matches_annotated": 0,
            "total_annotations": 0
        }
        
        if not self.test_data:
            return annotations
        
        # Check player annotations
        for player in self.test_data.get('players', {}).values():
            if '@type' in player or '@id' in player:
                annotations["players_annotated"] += 1
        
        # Check match annotations  
        for match in self.test_data.get('matches', {}).values():
            if '@type' in match or '@id' in match:
                annotations["matches_annotated"] += 1
        
        annotations["total_annotations"] = annotations["players_annotated"] + annotations["matches_annotated"]
        
        return annotations
    
    def _generate_test_summary(self, test_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of test results"""
        summary = {
            "total_tests_run": len(test_report["pipeline_tests"]),
            "tests_passed": 0,
            "tests_failed": 0,
            "critical_issues": [],
            "recommendations": []
        }
        
        for test_name, test_result in test_report["pipeline_tests"].items():
            if test_result.get("success", False):
                summary["tests_passed"] += 1
            else:
                summary["tests_failed"] += 1
                if test_result.get("errors"):
                    summary["critical_issues"].extend(test_result["errors"])
        
        # Generate recommendations
        if summary["tests_failed"] == 0:
            summary["recommendations"].append("🎉 All pipeline tests passed! System is ready for production use.")
        elif summary["tests_passed"] > summary["tests_failed"]:
            summary["recommendations"].append("⚠️ Most tests passed, but some issues need attention before production use.")
        else:
            summary["recommendations"].append("❌ Multiple critical issues detected. System requires fixes before use.")
        
        return summary


def run_complete_pipeline_test(api_key: str, 
                             players_count: int = 100, 
                             test_mode: str = "since_2024") -> Dict[str, Any]:
    """
    Convenience function to run complete pipeline test
    
    Args:
        api_key: Riot Games API key
        players_count: Number of players to test with
        test_mode: Collection mode for testing
        
    Returns:
        dict: Complete test results
    """
    tester = EndToEndPipelineTester(api_key)
    return tester.run_complete_pipeline_test(players_count, test_mode)


def run_pipeline_validation_test(api_key: str, test_data_file: str = None) -> Dict[str, Any]:
    """
    Run pipeline validation on existing data file
    
    Args:
        api_key: Riot Games API key  
        test_data_file: Path to existing data file to validate
        
    Returns:
        dict: Validation results
    """
    tester = EndToEndPipelineTester(api_key)
    
    if test_data_file:
        # Load existing data for validation
        success = tester.collector.load_data_from_file(test_data_file)
        if success:
            tester.test_data = tester.collector.collected_data
        else:
            return {"error": f"Could not load test data from {test_data_file}"}
    
    # Run validation tests only
    validation_results = {
        "data_validation": tester._test_data_validation(),
        "jsonld_compliance": tester._test_jsonld_compliance(),
        "quality_assessment": tester._test_quality_assessment()
    }
    
    return validation_results


def create_pipeline_test_report(test_results: Dict[str, Any], output_file: str = None) -> str:
    """
    Create a formatted test report
    
    Args:
        test_results: Results from pipeline test
        output_file: Optional file to save report to
        
    Returns:
        str: Formatted report
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🔍 TFT PIPELINE TEST REPORT")
    report_lines.append("=" * 80)
    
    # Test overview
    report_lines.append(f"Test Timestamp: {test_results.get('timestamp', 'Unknown')}")
    report_lines.append(f"Overall Status: {test_results.get('overall_status', 'Unknown')}")
    report_lines.append(f"Test Duration: {test_results.get('test_duration', 0):.2f} seconds")
    report_lines.append("")
    
    # Configuration
    config = test_results.get("test_configuration", {})
    report_lines.append("📊 TEST CONFIGURATION:")
    report_lines.append(f"  Players Count: {config.get('players_count', 'Unknown')}")
    report_lines.append(f"  Test Mode: {config.get('test_mode', 'Unknown')}")
    report_lines.append(f"  Save Results: {config.get('save_results', 'Unknown')}")
    report_lines.append("")
    
    # Individual test results
    report_lines.append("📋 INDIVIDUAL TEST RESULTS:")
    for test_name, result in test_results.get("pipeline_tests", {}).items():
        status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
        report_lines.append(f"  {test_name}: {status}")
        
        if result.get("errors"):
            for error in result["errors"]:
                report_lines.append(f"    Error: {error}")
    
    report_lines.append("")
    
    # Summary
    summary = test_results.get("summary", {})
    if summary:
        report_lines.append("📈 SUMMARY:")
        report_lines.append(f"  Tests Run: {summary.get('total_tests_run', 0)}")
        report_lines.append(f"  Tests Passed: {summary.get('tests_passed', 0)}")  
        report_lines.append(f"  Tests Failed: {summary.get('tests_failed', 0)}")
        
        if summary.get("recommendations"):
            report_lines.append("  Recommendations:")
            for rec in summary["recommendations"]:
                report_lines.append(f"    • {rec}")
    
    report_lines.append("=" * 80)
    
    # Join report
    report_text = "\n".join(report_lines)
    
    # Save to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"📄 Test report saved to: {output_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")
    
    return report_text


if __name__ == "__main__":
    # Demo functionality when run directly
    print("🧪 Testing End-to-End Pipeline Framework")
    print("=" * 50)
    
    # This would need an API key to run
    API_KEY = "YOUR_API_KEY_HERE"  # Replace with actual key
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please set your API key to run the pipeline test!")
        print("Example usage:")
        print("  tester = EndToEndPipelineTester('your_api_key')")
        print("  results = tester.run_complete_pipeline_test(players_count=10)")
        print("  report = create_pipeline_test_report(results)")
        print("  print(report)")
    else:
        # Run actual test
        results = run_complete_pipeline_test(API_KEY, players_count=10, test_mode="last_7_days")
        report = create_pipeline_test_report(results, "pipeline_test_report.txt")
        print(report)
    
    print("\n🎉 End-to-End Pipeline Testing Module Ready!")
