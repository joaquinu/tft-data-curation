"""
Data Validator Module

Core data structure validation and integrity checking for TFT data.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_json_structure(data: Dict[str, Any], required_keys: list) -> bool:
    """
    Validate that a JSON structure contains required keys
    
    Args:
        data: Dictionary to validate
        required_keys: List of required top-level keys
        
    Returns:
        bool: True if all required keys present, False otherwise
    """
    try:
        return all(key in data for key in required_keys)
    except Exception:
        return False


def validate_tft_data_structure(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate TFT data collection structure for completeness and integrity.
    
    Args:
        data: TFT data dictionary to validate
        
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        # Check core structure
        required_top_level = ["collectionInfo", "players", "matches"]
        if not validate_json_structure(data, required_top_level):
            missing = [key for key in required_top_level if key not in data]
            errors.append(f"Missing required top-level keys: {missing}")
        
        # Validate collection info
        if "collectionInfo" in data:
            required = ["timestamp", "extractionLocation", "dataVersion"]
            missing = [k for k in required if k not in data["collectionInfo"]]
            if missing:
                errors.append(f"Missing required collection info keys: {missing}")
        else:
            errors.append("Missing 'collectionInfo' key")
        
        # Validate players structure
        if "players" in data and data["players"]:
            try:
                player_sample = next(iter(data["players"].values()))
                if "puuid" not in player_sample:
                    errors.append("Missing required player keys: ['puuid']")
            except (StopIteration, AttributeError):
                pass
        else:
            errors.append("Missing or empty 'players' key")
        
        # Validate matches structure
        if "matches" in data and data["matches"]:
            try:
                match_sample = next(iter(data["matches"].values()))
                if "info" in match_sample:
                    match_info = match_sample["info"]
                    required = ["game_datetime", "game_length", "participants"]
                    missing = [k for k in required if k not in match_info]
                    if missing:
                        errors.append(f"Missing required match info keys: {missing}")
                    elif "participants" in match_info:
                        if not isinstance(match_info["participants"], list):
                            errors.append("Match participants must be a list")
                elif "game_datetime" not in match_sample and "participants" not in match_sample:
                    errors.append("Match missing 'info' key and required fields")
            except (StopIteration, AttributeError):
                pass
        else:
            errors.append("Missing or empty 'matches' key")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        logger.error(f"Validation error: {e}", exc_info=True)
        return False, errors


def validate_match_data_completeness(match_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate completeness of individual match data
    
    Args:
        match_data: Single match data dictionary
        
    Returns:
        tuple: (is_complete, completeness_report)
    """
    report = {
        "overall_completeness": 0.0,
        "missing_fields": [],
        "participant_completeness": [],
        "critical_errors": []
    }
    
    try:
        total_fields = 0
        present_fields = 0
        
        # Check match info completeness
        if "info" in match_data:
            info = match_data["info"]
            match_fields = ["game_datetime", "game_length", "participants", "queueId", "gameVersion"]
            
            for field in match_fields:
                total_fields += 1
                if field in info and info[field] is not None:
                    present_fields += 1
                else:
                    report["missing_fields"].append(f"match.info.{field}")
            
            # Check participants completeness
            if "participants" in info:
                for i, participant in enumerate(info["participants"]):
                    participant_fields = ["puuid", "placement", "level", "units", "traits"]
                    p_present = 0
                    p_total = len(participant_fields)
                    
                    for field in participant_fields:
                        total_fields += 1
                        if field in participant and participant[field] is not None:
                            present_fields += 1
                            p_present += 1
                        else:
                            report["missing_fields"].append(f"participant[{i}].{field}")
                    
                    report["participant_completeness"].append({
                        "participant_index": i,
                        "completeness": (p_present / p_total) * 100 if p_total > 0 else 0
                    })
        
        # Calculate overall completeness
        report["overall_completeness"] = (present_fields / total_fields) * 100 if total_fields > 0 else 0
        
        # Identify critical errors
        if report["overall_completeness"] < 50:
            report["critical_errors"].append("Match data less than 50% complete")
        
        if len(report["missing_fields"]) > 10:
            report["critical_errors"].append("Too many missing fields")
        
        is_complete = report["overall_completeness"] >= 80 and len(report["critical_errors"]) == 0
        
        return is_complete, report
        
    except Exception as e:
        report["critical_errors"].append(f"Validation error: {str(e)}")
        return False, report


def check_data_integrity(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive data integrity check for TFT dataset
    
    Args:
        data: Complete TFT dataset
        
    Returns:
        dict: Integrity report with statistics and findings
    """
    integrity_report = {
        "timestamp": datetime.now().isoformat(),
        "dataset_size": len(str(data)),
        "structure_valid": False,
        "player_count": 0,
        "match_count": 0,
        "data_quality_score": 0.0,
        "integrity_issues": [],
        "recommendations": []
    }
    
    try:
        # Structure validation
        is_valid, structure_errors = validate_tft_data_structure(data)
        integrity_report["structure_valid"] = is_valid
        if structure_errors:
            integrity_report["integrity_issues"].extend(structure_errors)
        
        # Count data elements
        integrity_report["player_count"] = len(data.get("players", {}))
        integrity_report["match_count"] = len(data.get("matches", {}))
        
        # Check data relationships
        if "players" in data and "matches" in data:
            player_puuids = set(data["players"].keys())
            match_puuids = set()
            
            for match in data["matches"].values():
                if "info" in match and "participants" in match["info"]:
                    for participant in match["info"]["participants"]:
                        if "puuid" in participant:
                            match_puuids.add(participant["puuid"])
            
            # Check for orphaned data
            orphaned_players = player_puuids - match_puuids
            orphaned_matches = match_puuids - player_puuids
            
            if orphaned_players:
                integrity_report["integrity_issues"].append(
                    f"{len(orphaned_players)} players have no associated matches"
                )
            
            if orphaned_matches:
                integrity_report["integrity_issues"].append(
                    f"{len(orphaned_matches)} match participants not in player list"
                )
        
        # Calculate quality score
        base_score = 100.0
        if not is_valid:
            base_score -= 30.0
        
        penalty_per_issue = min(10.0, 50.0 / len(integrity_report["integrity_issues"]) if integrity_report["integrity_issues"] else 0)
        base_score -= len(integrity_report["integrity_issues"]) * penalty_per_issue
        
        integrity_report["data_quality_score"] = max(0.0, base_score)
        
        # Generate recommendations
        if integrity_report["data_quality_score"] < 70:
            integrity_report["recommendations"].append("Review data collection process")
        
        if len(integrity_report["integrity_issues"]) > 5:
            integrity_report["recommendations"].append("Implement stricter validation during collection")
        
        logger.info(f"Data integrity check complete. Quality score: {integrity_report['data_quality_score']:.1f}")
        
        return integrity_report
        
    except Exception as e:
        integrity_report["integrity_issues"].append(f"Integrity check error: {str(e)}")
        logger.error(f"Data integrity check failed: {e}")
        return integrity_report
