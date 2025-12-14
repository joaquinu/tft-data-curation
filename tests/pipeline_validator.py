"""
Pipeline Validator Module
========================

Validation utilities for pipeline components and data integrity testing.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path

# Import quality assurance modules
from quality_assurance import (
    validate_tft_data_structure,
    validate_jsonld_compliance,
    detect_statistical_anomalies,
    calculate_data_quality_score,
    detect_missing_fields
)

logger = logging.getLogger(__name__)

class PipelineValidator:
    """
    Comprehensive pipeline validation framework
    """
    
    def __init__(self):
        """Initialize pipeline validator"""
        self.validation_results = {}
        logger.info("Pipeline validator initialized")
    
    def validate_complete_pipeline(self, data: Dict[str, Any], 
                                 expected_components: List[str] = None) -> Dict[str, Any]:
        """
        Validate complete pipeline execution results
        
        Args:
            data: Pipeline output data to validate
            expected_components: List of expected data components
            
        Returns:
            dict: Complete validation results
        """
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_validation_status": "RUNNING",
            "component_validations": {},
            "pipeline_health_score": 0.0,
            "critical_issues": [],
            "recommendations": []
        }
        
        try:
            # Default expected components
            if expected_components is None:
                expected_components = ["collectionInfo", "players", "matches", "@context", "@type"]
            
            # Validate data structure
            structure_validation = self._validate_pipeline_structure(data, expected_components)
            validation_report["component_validations"]["structure"] = structure_validation
            
            # Validate collection process
            collection_validation = self._validate_collection_process(data)
            validation_report["component_validations"]["collection"] = collection_validation
            
            # Validate data quality
            quality_validation = self._validate_pipeline_quality(data)
            validation_report["component_validations"]["quality"] = quality_validation
            
            # Validate output formats
            format_validation = self._validate_output_formats(data)
            validation_report["component_validations"]["formats"] = format_validation
            
            # Calculate overall health score
            validation_report["pipeline_health_score"] = self._calculate_pipeline_health_score(
                validation_report["component_validations"]
            )
            
            # Determine overall status
            if validation_report["pipeline_health_score"] >= 90:
                validation_report["overall_validation_status"] = "EXCELLENT"
            elif validation_report["pipeline_health_score"] >= 80:
                validation_report["overall_validation_status"] = "GOOD"
            elif validation_report["pipeline_health_score"] >= 70:
                validation_report["overall_validation_status"] = "ACCEPTABLE"
            elif validation_report["pipeline_health_score"] >= 60:
                validation_report["overall_validation_status"] = "POOR"
            else:
                validation_report["overall_validation_status"] = "CRITICAL"
            
            # Collect critical issues and recommendations
            validation_report = self._collect_issues_and_recommendations(validation_report)
            
            logger.info(f"Pipeline validation complete: {validation_report['overall_validation_status']} "
                       f"(Score: {validation_report['pipeline_health_score']:.1f})")
            
            return validation_report
            
        except Exception as e:
            validation_report["overall_validation_status"] = "FAILED"
            validation_report["critical_issues"].append(f"Validation error: {str(e)}")
            logger.error(f"❌ Pipeline validation failed: {e}")
            return validation_report
    
    def _validate_pipeline_structure(self, data: Dict[str, Any], 
                                   expected_components: List[str]) -> Dict[str, Any]:
        """Validate pipeline data structure"""
        structure_validation = {
            "structure_valid": False,
            "component_analysis": {},
            "missing_components": [],
            "unexpected_components": [],
            "structure_score": 0.0
        }
        
        try:
            # Check for expected components
            present_components = list(data.keys())
            
            for component in expected_components:
                is_present = component in data
                structure_validation["component_analysis"][component] = {
                    "present": is_present,
                    "type": type(data.get(component)).__name__ if is_present else "missing",
                    "size": len(data[component]) if is_present and hasattr(data[component], '__len__') else 0
                }
                
                if not is_present:
                    structure_validation["missing_components"].append(component)
            
            # Check for unexpected components
            for component in present_components:
                if component not in expected_components:
                    structure_validation["unexpected_components"].append(component)
            
            # Calculate structure score
            present_count = len([c for c in expected_components if c in data])
            structure_validation["structure_score"] = (present_count / len(expected_components)) * 100
            
            # Determine validity
            structure_validation["structure_valid"] = len(structure_validation["missing_components"]) == 0
            
            return structure_validation
            
        except Exception as e:
            structure_validation["error"] = str(e)
            return structure_validation
    
    def _validate_collection_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data collection process metadata"""
        collection_validation = {
            "collection_valid": False,
            "metadata_analysis": {},
            "timing_analysis": {},
            "collection_score": 0.0
        }
        
        try:
            collection_info = data.get("collectionInfo", {})
            
            # Validate collection metadata
            required_metadata = ["timestamp", "extractionLocation", "dataVersion"]
            metadata_score = 0
            
            for field in required_metadata:
                is_present = field in collection_info
                collection_validation["metadata_analysis"][field] = {
                    "present": is_present,
                    "value": collection_info.get(field, "missing")
                }
                if is_present:
                    metadata_score += 1
            
            # Validate timing information
            if "extractionTimestamp" in data and "extractionCompletedTimestamp" in data:
                try:
                    start_time = datetime.fromisoformat(data["extractionTimestamp"].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(data["extractionCompletedTimestamp"].replace('Z', '+00:00'))
                    duration = (end_time - start_time).total_seconds()
                    
                    collection_validation["timing_analysis"] = {
                        "has_timing_data": True,
                        "collection_duration_seconds": duration,
                        "start_time": data["extractionTimestamp"],
                        "end_time": data["extractionCompletedTimestamp"],
                        "timing_reasonable": 0 < duration < 3600  # Between 0 and 1 hour
                    }
                except Exception as e:
                    collection_validation["timing_analysis"] = {
                        "has_timing_data": False,
                        "error": str(e)
                    }
            
            # Calculate collection score
            timing_score = 1 if collection_validation["timing_analysis"].get("has_timing_data", False) else 0
            collection_validation["collection_score"] = ((metadata_score + timing_score) / (len(required_metadata) + 1)) * 100
            
            collection_validation["collection_valid"] = collection_validation["collection_score"] > 75
            
            return collection_validation
            
        except Exception as e:
            collection_validation["error"] = str(e)
            return collection_validation
    
    def _validate_pipeline_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality using quality assurance modules"""
        quality_validation = {
            "quality_valid": False,
            "quality_metrics": {},
            "anomaly_analysis": {},
            "completeness_analysis": {},
            "quality_score": 0.0
        }
        
        try:
            # Use quality assurance framework
            quality_report = calculate_data_quality_score(data)
            quality_validation["quality_metrics"] = quality_report
            
            # Anomaly detection
            if "matches" in data:
                anomaly_report = detect_statistical_anomalies(data["matches"])
                quality_validation["anomaly_analysis"] = anomaly_report
            
            # Field completeness analysis
            field_report = detect_missing_fields(data)
            quality_validation["completeness_analysis"] = field_report
            
            # Calculate overall quality score
            base_quality_score = quality_report.get("overall_score", 0)
            anomaly_penalty = len(anomaly_report.get("anomalies_detected", [])) * 5  # 5 points per anomaly
            completeness_bonus = (100 - len(field_report.get("missing_fields", []))) / 100 * 10  # Up to 10 bonus points
            
            quality_validation["quality_score"] = max(0, min(100, base_quality_score - anomaly_penalty + completeness_bonus))
            
            quality_validation["quality_valid"] = quality_validation["quality_score"] > 70
            
            return quality_validation
            
        except Exception as e:
            quality_validation["error"] = str(e)
            return quality_validation
    
    def _validate_output_formats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output formats and JSON-LD compliance"""
        format_validation = {
            "formats_valid": False,
            "jsonld_compliance": {},
            "data_structure_compliance": {},
            "format_score": 0.0
        }
        
        try:
            # JSON-LD compliance
            jsonld_compliant, jsonld_issues = validate_jsonld_compliance(data)
            format_validation["jsonld_compliance"] = {
                "compliant": jsonld_compliant,
                "issues": jsonld_issues,
                "has_context": bool(data.get('@context')),
                "has_type": bool(data.get('@type'))
            }
            
            # Data structure compliance
            structure_valid, structure_errors = validate_tft_data_structure(data)
            format_validation["data_structure_compliance"] = {
                "valid": structure_valid,
                "errors": structure_errors
            }
            
            # Calculate format score
            jsonld_score = 50 if jsonld_compliant else 0
            structure_score = 50 if structure_valid else 0
            format_validation["format_score"] = jsonld_score + structure_score
            
            format_validation["formats_valid"] = jsonld_compliant and structure_valid
            
            return format_validation
            
        except Exception as e:
            format_validation["error"] = str(e)
            return format_validation
    
    def _calculate_pipeline_health_score(self, component_validations: Dict[str, Any]) -> float:
        """Calculate overall pipeline health score"""
        try:
            # Weight different components
            weights = {
                "structure": 0.25,
                "collection": 0.20,
                "quality": 0.35,
                "formats": 0.20
            }
            
            total_score = 0.0
            total_weight = 0.0
            
            for component, weight in weights.items():
                if component in component_validations:
                    component_data = component_validations[component]
                    
                    # Get component score
                    if "structure_score" in component_data:
                        score = component_data["structure_score"]
                    elif "collection_score" in component_data:
                        score = component_data["collection_score"]
                    elif "quality_score" in component_data:
                        score = component_data["quality_score"]
                    elif "format_score" in component_data:
                        score = component_data["format_score"]
                    else:
                        score = 0.0
                    
                    total_score += score * weight
                    total_weight += weight
            
            return total_score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating pipeline health score: {e}")
            return 0.0
    
    def _collect_issues_and_recommendations(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Collect critical issues and recommendations from all validations"""
        try:
            for component, validation_data in validation_report["component_validations"].items():
                # Collect critical issues
                if not validation_data.get("structure_valid", True):
                    validation_report["critical_issues"].append(f"Structure validation failed for {component}")
                
                if not validation_data.get("collection_valid", True):
                    validation_report["critical_issues"].append(f"Collection validation failed for {component}")
                
                if not validation_data.get("quality_valid", True):
                    validation_report["critical_issues"].append(f"Quality validation failed for {component}")
                
                if not validation_data.get("formats_valid", True):
                    validation_report["critical_issues"].append(f"Format validation failed for {component}")
                
                # Collect errors
                if "error" in validation_data:
                    validation_report["critical_issues"].append(f"Validation error in {component}: {validation_data['error']}")
            
            # Generate recommendations
            health_score = validation_report["pipeline_health_score"]
            
            if health_score >= 90:
                validation_report["recommendations"].append("🎉 Pipeline is performing excellently")
            elif health_score >= 80:
                validation_report["recommendations"].append("✅ Pipeline is performing well with minor improvements needed")
            elif health_score >= 70:
                validation_report["recommendations"].append("⚠️ Pipeline is acceptable but needs attention to quality issues")
            elif health_score >= 60:
                validation_report["recommendations"].append("❌ Pipeline has significant issues requiring immediate attention")
            else:
                validation_report["recommendations"].append("🚨 Pipeline is in critical condition and needs comprehensive fixes")
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Error collecting issues and recommendations: {e}")
            return validation_report


def validate_collection_pipeline(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate data collection pipeline
    
    Args:
        data: Collected data to validate
        
    Returns:
        dict: Collection validation results
    """
    validator = PipelineValidator()
    return validator._validate_collection_process(data)


def validate_data_integrity_pipeline(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate data integrity
    
    Args:
        data: Data to validate for integrity
        
    Returns:
        dict: Data integrity validation results
    """
    validator = PipelineValidator()
    quality_validation = validator._validate_pipeline_quality(data)
    structure_validation = validator._validate_pipeline_structure(data, ["collectionInfo", "players", "matches"])
    
    return {
        "quality_validation": quality_validation,
        "structure_validation": structure_validation,
        "integrity_score": (quality_validation.get("quality_score", 0) + 
                          structure_validation.get("structure_score", 0)) / 2
    }


def validate_output_formats(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate output formats
    
    Args:
        data: Data to validate formats for
        
    Returns:
        dict: Format validation results
    """
    validator = PipelineValidator()
    return validator._validate_output_formats(data)


if __name__ == "__main__":
    # Demo functionality when run directly
    print("🧪 Testing Pipeline Validator")
    print("=" * 40)
    
    print("Example usage:")
    print("  # Validate complete pipeline")
    print("  validator = PipelineValidator()")
    print("  results = validator.validate_complete_pipeline(tft_data)")
    print("  ")
    print("  # Validate specific components")
    print("  collection_results = validate_collection_pipeline(tft_data)")
    print("  integrity_results = validate_data_integrity_pipeline(tft_data)")
    print("  format_results = validate_output_formats(tft_data)")
    
    print("\n🎉 Pipeline Validator Module Ready!")
