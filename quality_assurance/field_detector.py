"""
Field Detector Module

Missing field detection and data completeness analysis for TFT data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_completeness_grade(score: float) -> tuple:
    """Convert numeric score to letter grade and status."""
    grades = [
        (95, "A+", "EXCELLENT"), (90, "A", "EXCELLENT"),
        (85, "B+", "GOOD"), (80, "B", "GOOD"),
        (75, "C+", "ACCEPTABLE"), (70, "C", "ACCEPTABLE"),
        (60, "D", "POOR"), (0, "F", "CRITICAL")
    ]
    for threshold, grade, status in grades:
        if score >= threshold:
            return grade, status
    return "F", "CRITICAL"

def detect_missing_fields(data: Dict[str, Any], expected_schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Detect missing fields in TFT data structure
    
    Args:
        data: TFT dataset to analyze
        expected_schema: Optional schema definition for validation
        
    Returns:
        dict: Missing field detection report
    """
    detection_report = {
        "timestamp": datetime.now().isoformat(),
        "missing_fields": [],
        "field_coverage": {},
        "critical_missing": [],
        "optional_missing": [],
        "field_statistics": {}
    }
    
    try:
        # Define expected TFT data structure
        if expected_schema is None:
            expected_schema = {
                "collectionInfo": {
                    "required": ["timestamp", "extractionLocation", "dataVersion"],
                    "optional": ["apiKey", "collectionMethod", "regionCode"]
                },
                "players": {
                    "required": ["puuid", "summonerId", "summonerLevel", "tier", "rank", "leaguePoints"],
                    "optional": ["profileIconId", "revisionDate", "riotIdGameName", "riotIdTagline"]
                },
                "matches": {
                    "info": {
                        "required": ["game_datetime", "game_length", "participants", "queueId", "gameVersion"],
                        "optional": ["gameCreation", "gameEndTimestamp", "gameId", "gameName", "gameStartTimestamp"]
                    },
                    "participants": {
                        "required": ["puuid", "placement", "level", "units", "traits"],
                        "optional": ["augments", "companion", "gold_left", "last_round", "total_damage_to_players"]
                    }
                }
            }
        
        # Analyze collection info
        if "collectionInfo" in data:
            collection_info = data["collectionInfo"]
            schema_collection = expected_schema.get("collectionInfo", {})
            
            for field in schema_collection.get("required", []):
                if field not in collection_info or collection_info[field] is None:
                    detection_report["missing_fields"].append(f"collectionInfo.{field}")
                    detection_report["critical_missing"].append(f"collectionInfo.{field}")
            
            for field in schema_collection.get("optional", []):
                if field not in collection_info or collection_info[field] is None:
                    detection_report["optional_missing"].append(f"collectionInfo.{field}")
        else:
            detection_report["critical_missing"].append("collectionInfo (entire section)")
        
        # Analyze player data
        if "players" in data and data["players"]:
            player_schema = expected_schema.get("players", {})
            required_player_fields = player_schema.get("required", [])
            optional_player_fields = player_schema.get("optional", [])
            
            # Field presence tracking
            field_presence = {field: 0 for field in required_player_fields + optional_player_fields}
            total_players = len(data["players"])
            
            for puuid, player_data in data["players"].items():
                # Check required fields
                for field in required_player_fields:
                    if field in player_data and player_data[field] is not None:
                        field_presence[field] += 1
                    else:
                        detection_report["missing_fields"].append(f"player[{puuid[:8]}...].{field}")
                
                # Check optional fields
                for field in optional_player_fields:
                    if field in player_data and player_data[field] is not None:
                        field_presence[field] += 1
            
            # Calculate field coverage percentages
            for field, present_count in field_presence.items():
                coverage_pct = (present_count / total_players) * 100 if total_players > 0 else 0
                detection_report["field_coverage"][f"players.{field}"] = coverage_pct
                
                # Flag fields with low coverage
                if field in required_player_fields and coverage_pct < 80:
                    detection_report["critical_missing"].append(f"players.{field} (coverage: {coverage_pct:.1f}%)")
                elif field in optional_player_fields and coverage_pct < 50:
                    detection_report["optional_missing"].append(f"players.{field} (coverage: {coverage_pct:.1f}%)")
        
        # Analyze match data
        if "matches" in data and data["matches"]:
            match_schema = expected_schema.get("matches", {})
            info_schema = match_schema.get("info", {})
            participant_schema = match_schema.get("participants", {})
            
            required_match_fields = info_schema.get("required", [])
            optional_match_fields = info_schema.get("optional", [])
            required_participant_fields = participant_schema.get("required", [])
            optional_participant_fields = participant_schema.get("optional", [])
            
            # Match-level field tracking
            match_field_presence = {field: 0 for field in required_match_fields + optional_match_fields}
            total_matches = len(data["matches"])
            
            # Participant-level field tracking
            participant_field_presence = {field: 0 for field in required_participant_fields + optional_participant_fields}
            total_participants = 0
            
            for match_id, match_data in data["matches"].items():
                # Check match info fields
                match_info = match_data.get("info", {})
                
                for field in required_match_fields + optional_match_fields:
                    if field in match_info and match_info[field] is not None:
                        match_field_presence[field] += 1
                    elif field in required_match_fields:
                        detection_report["missing_fields"].append(f"match[{match_id}].info.{field}")
                
                # Check participant fields
                participants = match_info.get("participants", [])
                for i, participant in enumerate(participants):
                    total_participants += 1
                    
                    for field in required_participant_fields:
                        if field in participant and participant[field] is not None:
                            participant_field_presence[field] += 1
                        else:
                            detection_report["missing_fields"].append(f"match[{match_id}].participants[{i}].{field}")
                    
                    for field in optional_participant_fields:
                        if field in participant and participant[field] is not None:
                            participant_field_presence[field] += 1
            
            # Calculate match field coverage
            for field, present_count in match_field_presence.items():
                coverage_pct = (present_count / total_matches) * 100 if total_matches > 0 else 0
                detection_report["field_coverage"][f"matches.info.{field}"] = coverage_pct
                
                if field in required_match_fields and coverage_pct < 80:
                    detection_report["critical_missing"].append(f"matches.info.{field} (coverage: {coverage_pct:.1f}%)")
                elif field in optional_match_fields and coverage_pct < 50:
                    detection_report["optional_missing"].append(f"matches.info.{field} (coverage: {coverage_pct:.1f}%)")
            
            # Calculate participant field coverage
            for field, present_count in participant_field_presence.items():
                coverage_pct = (present_count / total_participants) * 100 if total_participants > 0 else 0
                detection_report["field_coverage"][f"participants.{field}"] = coverage_pct
                
                if field in required_participant_fields and coverage_pct < 80:
                    detection_report["critical_missing"].append(f"participants.{field} (coverage: {coverage_pct:.1f}%)")
                elif field in optional_participant_fields and coverage_pct < 50:
                    detection_report["optional_missing"].append(f"participants.{field} (coverage: {coverage_pct:.1f}%)")
        
        # Generate field statistics
        detection_report["field_statistics"] = {
            "total_missing_fields": len(detection_report["missing_fields"]),
            "critical_missing_count": len(detection_report["critical_missing"]),
            "optional_missing_count": len(detection_report["optional_missing"]),
            "field_coverage_average": sum(detection_report["field_coverage"].values()) / len(detection_report["field_coverage"]) if detection_report["field_coverage"] else 0
        }
        
        logger.info(f"Missing field detection complete. Found {detection_report['field_statistics']['total_missing_fields']} missing fields")
        
        return detection_report
        
    except Exception as e:
        detection_report["missing_fields"].append(f"Detection error: {str(e)}")
        logger.error(f"Missing field detection failed: {e}")
        return detection_report


def analyze_field_coverage(data: Dict[str, Any], sample_size: int = 100) -> Dict[str, Any]:
    """
    Analyze field coverage across dataset with statistical sampling
    
    Args:
        data: TFT dataset to analyze
        sample_size: Number of records to sample for analysis
        
    Returns:
        dict: Field coverage analysis report
    """
    coverage_report = {
        "timestamp": datetime.now().isoformat(),
        "sample_size": sample_size,
        "field_coverage_stats": {},
        "coverage_distribution": {},
        "data_quality_indicators": {},
        "sampling_metadata": {}
    }
    
    try:
        # Sample players for analysis
        if "players" in data and data["players"]:
            player_items = list(data["players"].items())
            player_sample = player_items[:min(sample_size, len(player_items))]
            
            # Analyze all fields present in sampled players
            all_player_fields = set()
            for puuid, player_data in player_sample:
                all_player_fields.update(player_data.keys())
            
            # Calculate coverage for each field
            player_field_stats = {}
            for field in all_player_fields:
                present_count = sum(1 for puuid, player_data in player_sample 
                                  if field in player_data and player_data[field] is not None and str(player_data[field]).strip() != "")
                
                coverage_pct = (present_count / len(player_sample)) * 100
                player_field_stats[field] = {
                    "coverage_percentage": coverage_pct,
                    "present_count": present_count,
                    "total_sampled": len(player_sample),
                    "data_type": type(player_sample[0][1].get(field, None)).__name__ if len(player_sample) > 0 else "unknown"
                }
            
            coverage_report["field_coverage_stats"]["players"] = player_field_stats
            coverage_report["sampling_metadata"]["players_sampled"] = len(player_sample)
        
        # Sample matches for analysis
        if "matches" in data and data["matches"]:
            match_items = list(data["matches"].items())
            match_sample = match_items[:min(sample_size, len(match_items))]
            
            # Analyze match info fields
            all_match_info_fields = set()
            for match_id, match_data in match_sample:
                if "info" in match_data:
                    all_match_info_fields.update(match_data["info"].keys())
            
            match_info_field_stats = {}
            for field in all_match_info_fields:
                present_count = sum(1 for match_id, match_data in match_sample 
                                  if "info" in match_data and field in match_data["info"] 
                                  and match_data["info"][field] is not None)
                
                coverage_pct = (present_count / len(match_sample)) * 100
                match_info_field_stats[field] = {
                    "coverage_percentage": coverage_pct,
                    "present_count": present_count,
                    "total_sampled": len(match_sample)
                }
            
            coverage_report["field_coverage_stats"]["match_info"] = match_info_field_stats
            
            # Analyze participant fields (sample from first few matches)
            participant_sample = []
            for match_id, match_data in match_sample[:10]:  # Sample participants from first 10 matches
                if "info" in match_data and "participants" in match_data["info"]:
                    participant_sample.extend(match_data["info"]["participants"])
            
            if participant_sample:
                all_participant_fields = set()
                for participant in participant_sample:
                    all_participant_fields.update(participant.keys())
                
                participant_field_stats = {}
                for field in all_participant_fields:
                    present_count = sum(1 for participant in participant_sample 
                                      if field in participant and participant[field] is not None)
                    
                    coverage_pct = (present_count / len(participant_sample)) * 100
                    participant_field_stats[field] = {
                        "coverage_percentage": coverage_pct,
                        "present_count": present_count,
                        "total_sampled": len(participant_sample)
                    }
                
                coverage_report["field_coverage_stats"]["participants"] = participant_field_stats
            
            coverage_report["sampling_metadata"]["matches_sampled"] = len(match_sample)
            coverage_report["sampling_metadata"]["participants_sampled"] = len(participant_sample) if participant_sample else 0
        
        # Generate coverage distribution analysis
        all_coverage_values = []
        for section, field_stats in coverage_report["field_coverage_stats"].items():
            for field, stats in field_stats.items():
                all_coverage_values.append(stats["coverage_percentage"])
        
        if all_coverage_values:
            coverage_report["coverage_distribution"] = {
                "mean_coverage": sum(all_coverage_values) / len(all_coverage_values),
                "min_coverage": min(all_coverage_values),
                "max_coverage": max(all_coverage_values),
                "fields_with_full_coverage": sum(1 for cov in all_coverage_values if cov == 100),
                "fields_with_partial_coverage": sum(1 for cov in all_coverage_values if 50 <= cov < 100),
                "fields_with_low_coverage": sum(1 for cov in all_coverage_values if cov < 50)
            }
        
        # Data quality indicators
        coverage_report["data_quality_indicators"] = {
            "overall_completeness": coverage_report["coverage_distribution"].get("mean_coverage", 0),
            "data_consistency": "high" if coverage_report["coverage_distribution"].get("min_coverage", 0) > 80 else "medium" if coverage_report["coverage_distribution"].get("min_coverage", 0) > 50 else "low",
            "field_reliability": coverage_report["coverage_distribution"].get("fields_with_full_coverage", 0) / len(all_coverage_values) * 100 if all_coverage_values else 0
        }
        
        logger.info(f"Field coverage analysis complete. Overall completeness: {coverage_report['data_quality_indicators']['overall_completeness']:.1f}%")
        
        return coverage_report
        
    except Exception as e:
        coverage_report["field_coverage_stats"] = {"error": str(e)}
        logger.error(f"Field coverage analysis failed: {e}")
        return coverage_report


def validate_required_fields(data: Dict[str, Any], field_requirements: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Validate presence of required fields according to specifications
    
    Args:
        data: TFT dataset to validate
        field_requirements: Dictionary defining required fields for each data type
        
    Returns:
        dict: Validation report
    """
    validation_report = {
        "timestamp": datetime.now().isoformat(),
        "validation_passed": True,
        "requirement_violations": [],
        "compliance_score": 0.0,
        "validation_summary": {},
        "field_compliance": {}
    }
    
    try:
        total_validations = 0
        passed_validations = 0
        
        # Validate each data section
        for section, required_fields in field_requirements.items():
            section_violations = []
            
            if section == "collectionInfo":
                if section in data:
                    collection_info = data[section]
                    for field in required_fields:
                        total_validations += 1
                        if field in collection_info and collection_info[field] is not None:
                            passed_validations += 1
                        else:
                            section_violations.append(f"Missing required field: {section}.{field}")
                else:
                    section_violations.append(f"Missing required section: {section}")
                    total_validations += len(required_fields)
            
            elif section == "players":
                if section in data and data[section]:
                    # Validate sample of players
                    player_sample = list(data[section].items())[:10]  # Sample first 10 players
                    
                    for puuid, player_data in player_sample:
                        for field in required_fields:
                            total_validations += 1
                            if field in player_data and player_data[field] is not None:
                                passed_validations += 1
                            else:
                                section_violations.append(f"Player {puuid[:8]}... missing required field: {field}")
                else:
                    section_violations.append(f"Missing or empty section: {section}")
                    total_validations += len(required_fields) * 10  # Assume 10 players for scoring
            
            elif section == "match_info":
                if "matches" in data and data["matches"]:
                    # Validate sample of matches
                    match_sample = list(data["matches"].items())[:5]  # Sample first 5 matches
                    
                    for match_id, match_data in match_sample:
                        match_info = match_data.get("info", {})
                        for field in required_fields:
                            total_validations += 1
                            if field in match_info and match_info[field] is not None:
                                passed_validations += 1
                            else:
                                section_violations.append(f"Match {match_id} missing required field: info.{field}")
                else:
                    section_violations.append("Missing or empty matches section")
                    total_validations += len(required_fields) * 5  # Assume 5 matches for scoring
            
            elif section == "participants":
                if "matches" in data and data["matches"]:
                    # Validate participants from sample matches
                    match_sample = list(data["matches"].items())[:3]  # Sample first 3 matches
                    
                    for match_id, match_data in match_sample:
                        participants = match_data.get("info", {}).get("participants", [])
                        for i, participant in enumerate(participants):
                            for field in required_fields:
                                total_validations += 1
                                if field in participant and participant[field] is not None:
                                    passed_validations += 1
                                else:
                                    section_violations.append(f"Match {match_id}, participant {i} missing required field: {field}")
                else:
                    section_violations.append("Missing matches for participant validation")
                    total_validations += len(required_fields) * 3 * 8  # Assume 3 matches, 8 participants each
            
            # Record violations for this section
            if section_violations:
                validation_report["requirement_violations"].extend(section_violations)
                validation_report["validation_passed"] = False
            
            # Calculate section compliance
            section_compliance = 100.0  # Start with perfect compliance
            if total_validations > 0:
                section_passed = passed_validations  # This is cumulative, need per-section calculation
                # For simplicity, estimate section compliance based on violations
                if section_violations:
                    section_compliance = max(0, 100 - (len(section_violations) / max(1, len(required_fields))) * 100)
            
            validation_report["field_compliance"][section] = section_compliance
        
        # Calculate overall compliance score
        validation_report["compliance_score"] = (passed_validations / total_validations) * 100 if total_validations > 0 else 100
        
        # Generate validation summary
        validation_report["validation_summary"] = {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "failed_validations": total_validations - passed_validations,
            "total_violations": len(validation_report["requirement_violations"]),
            "compliance_level": "high" if validation_report["compliance_score"] > 90 else "medium" if validation_report["compliance_score"] > 70 else "low"
        }
        
        logger.info(f"Required field validation complete. Compliance score: {validation_report['compliance_score']:.1f}%")
        
        return validation_report
        
    except Exception as e:
        validation_report["requirement_violations"].append(f"Validation error: {str(e)}")
        validation_report["validation_passed"] = False
        validation_report["compliance_score"] = 0.0
        logger.error(f"Required field validation failed: {e}")
        return validation_report


def generate_field_report(data: Dict[str, Any], detailed: bool = True) -> Dict[str, Any]:
    """
    Generate comprehensive field analysis report
    
    Args:
        data: TFT dataset to analyze
        detailed: Whether to include detailed field-by-field analysis
        
    Returns:
        dict: Comprehensive field analysis report
    """
    field_report = {
        "timestamp": datetime.now().isoformat(),
        "field_score": 0.0,
        "field_grade": "F",
        "executive_summary": {},
        "field_analysis": {},
        "recommendations": []
    }
    
    try:
        # Run comprehensive field analysis
        missing_fields_report = detect_missing_fields(data)
        coverage_report = analyze_field_coverage(data)
        
        # Define standard requirements for validation
        standard_requirements = {
            "collectionInfo": ["timestamp", "extractionLocation", "dataVersion"],
            "players": ["puuid", "summonerId", "tier", "rank", "leaguePoints"],
            "match_info": ["game_datetime", "game_length", "participants", "queueId"],
            "participants": ["puuid", "placement", "level", "units", "traits"]
        }
        
        validation_report = validate_required_fields(data, standard_requirements)
        
        # Compile executive summary
        total_missing = missing_fields_report["field_statistics"]["total_missing_fields"]
        critical_missing = missing_fields_report["field_statistics"]["critical_missing_count"]
        overall_coverage = coverage_report["data_quality_indicators"]["overall_completeness"]
        compliance_score = validation_report["compliance_score"]
        
        # Calculate composite score and grade
        composite_score = (overall_coverage * 0.4 + compliance_score * 0.6)
        grade, status = _get_completeness_grade(composite_score)
        field_report["field_score"] = composite_score
        field_report["field_grade"] = grade
        field_report["data_completeness_grade"] = grade  # Legacy compatibility
        
        field_report["executive_summary"] = {
            "status": status,
            "composite_score": composite_score,
            "total_missing_fields": total_missing,
            "critical_missing_fields": critical_missing,
            "overall_coverage_percentage": overall_coverage,
            "compliance_score": compliance_score,
            "key_issues": []
        }
        
        # Identify key issues
        if critical_missing > 0:
            field_report["executive_summary"]["key_issues"].append(f"{critical_missing} critical fields missing")
        
        if overall_coverage < 80:
            field_report["executive_summary"]["key_issues"].append(f"Low field coverage: {overall_coverage:.1f}%")
        
        if compliance_score < 80:
            field_report["executive_summary"]["key_issues"].append(f"Low compliance: {compliance_score:.1f}%")
        
        # Include detailed analysis if requested
        if detailed:
            field_report["field_analysis"] = {
                "missing_fields_analysis": missing_fields_report,
                "coverage_analysis": coverage_report,
                "validation_analysis": validation_report
            }
        
        # Generate recommendations
        if critical_missing > 0:
            field_report["recommendations"].append("Address critical missing fields immediately")
        
        if overall_coverage < 85:
            field_report["recommendations"].append("Improve data collection completeness")
        
        if compliance_score < 90:
            field_report["recommendations"].append("Review field requirements compliance")
        
        if len(field_report["recommendations"]) == 0:
            field_report["recommendations"].append("Field completeness is excellent - maintain current standards")
        
        logger.info(f"Field analysis report generated. Status: {status}, Grade: {field_report['data_completeness_grade']}")
        
        return field_report
        
    except Exception as e:
        field_report["executive_summary"] = {
            "status": "ERROR",
            "error": str(e)
        }
        logger.error(f"Field report generation failed: {e}")
        return field_report
