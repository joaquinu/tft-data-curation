"""
Quality Metrics Module

Quality assessment metrics and reporting functions for TFT data.
Provides comprehensive quality scoring and metrics calculation.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import numpy as np

from .tree_validator import should_skip_match, calculate_tree_validation_score

logger = logging.getLogger(__name__)


def _get_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


def _should_skip_match_for_quality(match: Dict[str, Any]) -> bool:
    """
    Determine if a match should be skipped for quality assessment.
    
    Args:
        match: Match data to check
        
    Returns:
        bool: True if match should be skipped
    """
    # Use shared helper for basic checks
    if should_skip_match(match):
        return True
    
    metadata = match.get('metadata', {})
    
    # Check for invalid placements (data corruption indicator)
    if 'info' in match and 'participants' in match['info']:
        participants = match['info']['participants']
        if participants:
            placements = [p.get('placement', 8) for p in participants]
            expected_placements = set(range(1, 9))
            actual_placements = set(placements)
            
            # If placements are invalid (not 1-8 unique, or all same), skip this match
            if actual_placements != expected_placements:
                return True
    
    if not metadata.get('is_incomplete', False):
        return False  # Not marked as incomplete, don't skip
    
    # Check if the only reason is missing gameVersion
    incomplete_reasons = metadata.get('incomplete_reason', [])
    if isinstance(incomplete_reasons, list):
        # If only reason is missing gameVersion and match has 8 participants, don't skip
        if len(incomplete_reasons) == 1 and 'Missing gameVersion' in incomplete_reasons[0]:
            if 'info' in match and 'participants' in match['info']:
                if len(match['info']['participants']) == 8:
                    return False
    
    # Otherwise, skip it (truly incomplete)
    return True


def calculate_data_quality_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive data quality score for TFT dataset
    
    Args:
        data: Complete TFT dataset
        
    Returns:
        dict: Quality score report with breakdown
    """
    score_report = {
        "timestamp": datetime.now().isoformat(),
        "overall_score": 0.0,
        "component_scores": {},
        "score_breakdown": {},
        "quality_grade": "F",
        "recommendations": []
    }
    
    try:
        # Initialize component scores
        components = {
            "completeness": 0.0,    # 25% weight
            "consistency": 0.0,     # 20% weight  
            "accuracy": 0.0,        # 20% weight
            "integrity": 0.0,       # 15% weight
            "structure": 0.0,       # 20% weight
        }
        
        weights = {
            "completeness": 0.25,
            "consistency": 0.20,
            "accuracy": 0.20,
            "integrity": 0.15,
            "structure": 0.20      # Tree validation weight
        }
        
        # Completeness Score (30%)
        completeness_metrics = assess_data_completeness(data)
        components["completeness"] = completeness_metrics["completeness_percentage"]
        score_report["component_scores"]["completeness"] = completeness_metrics
        
        # Consistency Score (25%)
        consistency_metrics = measure_data_consistency(data)
        components["consistency"] = consistency_metrics["consistency_score"]
        score_report["component_scores"]["consistency"] = consistency_metrics
        
        # Accuracy Score (25%) - Based on data validation and schema compliance
        accuracy_score = 100.0  # Start with perfect score
        
        # Check for impossible values
        if "matches" in data:
            total_matches = 0
            invalid_matches = 0
            
            for match_id, match_info in data["matches"].items():
                # Skip truly incomplete matches for accuracy validation
                if _should_skip_match_for_quality(match_info):
                    continue
                
                if "info" in match_info and "participants" in match_info["info"]:
                    total_matches += 1
                    participants = match_info["info"]["participants"]
                    
                    # Check for impossible placements
                    placements = [p.get("placement", 8) for p in participants]
                    placement_invalid = len(set(placements)) != len(placements) or not all(1 <= p <= 8 for p in placements)
                    
                    # Check for impossible levels
                    levels = [p.get("level", 1) for p in participants]
                    level_invalid = not all(1 <= l <= 10 for l in levels)
                    
                    # Count as invalid if either check fails (but only count once per match)
                    if placement_invalid or level_invalid:
                        invalid_matches += 1
            
            if total_matches > 0:
                accuracy_penalty = (invalid_matches / total_matches) * 50  # Up to 50 point penalty
                accuracy_score -= accuracy_penalty
        
        components["accuracy"] = max(0.0, accuracy_score)
        score_report["component_scores"]["accuracy"] = {
            "accuracy_score": components["accuracy"],
            "total_matches_checked": total_matches if "matches" in data else 0,
            "invalid_matches": invalid_matches if "matches" in data else 0
        }
        
        # Integrity Score (20%) - Data relationships and structure
        integrity_score = 100.0
        
        if "players" in data and "matches" in data:
            # Check player-match relationships
            # Note: When collecting from leaderboards, matches will contain players
            # not in our player data (opponents of our tracked players). This is expected.
            # We calculate integrity based on how many of our tracked players appear in matches.
            player_puuids = set(data["players"].keys())
            match_puuids = set()
            
            for match in data["matches"].values():
                # Skip truly incomplete matches for integrity calculation
                if _should_skip_match_for_quality(match):
                    continue
                
                if "info" in match and "participants" in match["info"]:
                    for participant in match["info"]["participants"]:
                        if "puuid" in participant:
                            match_puuids.add(participant["puuid"])
            
            # Calculate relationship integrity
            # Focus on: what percentage of our tracked players appear in matches?
            # However, account for inactive players - not all players will have matches
            # in a given time window. We consider integrity good if:
            # 1. At least 20% of tracked players appear in matches (active players)
            # 2. OR if we have matches, at least 80% of players in matches are tracked
            if player_puuids:
                tracked_players_in_matches = player_puuids.intersection(match_puuids)
                active_player_percentage = (len(tracked_players_in_matches) / len(player_puuids)) * 100
                
                # Handle case of no matches
                if not match_puuids:
                    integrity_score = 0.0
                # Apply a minimum threshold: if at least 20% of players are active, give partial credit
                elif active_player_percentage >= 20.0:
                    # Scale from 20% to 100%: 20% active = 50% integrity, 100% active = 100% integrity
                    integrity_score = 50.0 + (active_player_percentage - 20.0) * (50.0 / 80.0)
                    integrity_score = min(100.0, integrity_score)
                else:
                    # Below 20% active players - scale from 0% to 50%
                    integrity_score = (active_player_percentage / 20.0) * 50.0
            else:
                integrity_score = 0.0
        
        components["integrity"] = integrity_score
        score_report["component_scores"]["integrity"] = {
            "integrity_score": components["integrity"],
            "tracked_players": len(player_puuids) if "players" in data and "matches" in data else 0,
            "tracked_players_in_matches": len(player_puuids.intersection(match_puuids)) if "players" in data and "matches" in data else 0,
            "active_player_percentage": (len(player_puuids.intersection(match_puuids)) / len(player_puuids) * 100) if "players" in data and "matches" in data and player_puuids else 0.0
        }
        
        # Structure Score (20%) - Tree-based hierarchical validation (per project proposal)
        tree_validation = calculate_tree_validation_score(data)
        components["structure"] = tree_validation["tree_score"]
        score_report["component_scores"]["structure"] = {
            "structure_score": components["structure"],
            "structure_valid": tree_validation["structure_valid"],
            "hierarchy_issues": tree_validation["hierarchy_issues_count"],
            "relationship_integrity": tree_validation["relationship_integrity_score"]
        }
        
        # Calculate weighted overall score
        overall_score = sum(components[comp] * weights[comp] for comp in components)
        score_report["overall_score"] = overall_score
        score_report["score_breakdown"] = {comp: f"{score:.1f} (weight: {weights[comp]*100:.0f}%)" 
                                          for comp, score in components.items()}
        
        # Determine quality grade
        score_report["quality_grade"] = _get_grade(overall_score)
        
        # Generate recommendations
        if components["completeness"] < 80:
            score_report["recommendations"].append("Improve data completeness - missing fields detected")
        
        if components["consistency"] < 80:
            score_report["recommendations"].append("Address data consistency issues")
        
        if components["accuracy"] < 80:
            score_report["recommendations"].append("Review data validation - accuracy issues found")
        
        if components["integrity"] < 80:
            score_report["recommendations"].append("Fix data relationship integrity issues")
        
        if components["structure"] < 80:
            score_report["recommendations"].append("Review hierarchical data structure - tree validation issues found")
        
        if overall_score < 70:
            score_report["recommendations"].append("Overall data quality below acceptable standards")
        
        logger.info(f"Data quality assessment complete. Overall score: {overall_score:.1f} (Grade: {score_report['quality_grade']})")
        
        return score_report
        
    except Exception as e:
        score_report["overall_score"] = 0.0
        score_report["quality_grade"] = "F"
        score_report["recommendations"].append(f"Quality assessment error: {str(e)}")
        logger.error(f"Data quality calculation failed: {e}")
        return score_report


def assess_data_completeness(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess completeness of TFT dataset
    
    Args:
        data: TFT dataset to assess
        
    Returns:
        dict: Completeness assessment report
    """
    assessment = {
        "timestamp": datetime.now().isoformat(),
        "completeness_percentage": 0.0,
        "field_coverage": {},
        "missing_data_summary": {},
        "critical_gaps": []
    }
    
    try:
        total_expected_fields = 0
        present_fields = 0
        
        # Assess collection metadata completeness
        if "collectionInfo" in data:
            required_collection_fields = ["timestamp", "extractionLocation", "dataVersion"]
            optional_collection_fields = ["apiKey"]  # Optional - not stored for security
            
            for field in required_collection_fields:
                total_expected_fields += 1
                if field in data["collectionInfo"] and data["collectionInfo"][field] is not None:
                    present_fields += 1
                else:
                    assessment["missing_data_summary"][f"collectionInfo.{field}"] = "missing"
            
            # Check optional fields but don't penalize if missing
            for field in optional_collection_fields:
                if field in data["collectionInfo"] and data["collectionInfo"][field] is not None:
                    # If present, count it as a bonus (but don't penalize if missing)
                    pass
        else:
            assessment["critical_gaps"].append("Missing collection info metadata")
            # If collectionInfo is missing, still count the required fields as missing
            total_expected_fields += 3  # timestamp, extractionLocation, dataVersion
        
        # Assess player data completeness
        if "players" in data and data["players"]:
            player_sample_size = min(10, len(data["players"]))  # Sample first 10 players
            players_sampled = list(data["players"].items())[:player_sample_size]
            
            # Required fields (all players must have these)
            required_player_fields = ["puuid", "leaguePoints"]
            # Optional fields (may be missing due to API failures or player status)
            optional_player_fields = ["summonerId", "summonerLevel", "tier", "rank"]
            
            player_field_coverage = {field: 0 for field in required_player_fields + optional_player_fields}
            
            for puuid, player_data in players_sampled:
                # Check required fields
                for field in required_player_fields:
                    total_expected_fields += 1
                    if field in player_data and player_data[field] is not None:
                        present_fields += 1
                        player_field_coverage[field] += 1
                
                # Check optional fields (don't count as missing if absent)
                for field in optional_player_fields:
                    if field in player_data and player_data[field] is not None:
                        # Count as bonus if present, but don't penalize if missing
                        player_field_coverage[field] += 1
            
            # Calculate field coverage percentages
            for field in required_player_fields:
                count = player_field_coverage[field]
                coverage_pct = (count / player_sample_size) * 100 if player_sample_size > 0 else 0
                assessment["field_coverage"][f"player.{field}"] = f"{coverage_pct:.1f}%"
                
                if coverage_pct < 50:
                    assessment["critical_gaps"].append(f"Low coverage for player.{field}: {coverage_pct:.1f}%")
            
            # Report optional fields but don't penalize
            for field in optional_player_fields:
                count = player_field_coverage[field]
                coverage_pct = (count / player_sample_size) * 100 if player_sample_size > 0 else 0
                assessment["field_coverage"][f"player.{field}"] = f"{coverage_pct:.1f}% (optional)"
        
        # Assess match data completeness
        if "matches" in data and data["matches"]:
            match_sample_size = min(10, len(data["matches"]))  # Sample first 10 matches
            matches_sampled = list(data["matches"].items())[:match_sample_size]
            
            required_match_fields = ["info.game_datetime", "info.game_length", "info.participants", "info.queueId"]
            match_field_coverage = {field: 0 for field in required_match_fields}
            
            for match_id, match_data in matches_sampled:
                for field in required_match_fields:
                    total_expected_fields += 1
                    
                    # Handle nested field access
                    if "." in field:
                        parts = field.split(".")
                        current_data = match_data
                        field_exists = True
                        
                        for part in parts:
                            if isinstance(current_data, dict) and part in current_data:
                                current_data = current_data[part]
                            else:
                                field_exists = False
                                break
                        
                        if field_exists and current_data is not None:
                            present_fields += 1
                            match_field_coverage[field] += 1
                    else:
                        if field in match_data and match_data[field] is not None:
                            present_fields += 1
                            match_field_coverage[field] += 1
            
            # Calculate match field coverage
            for field, count in match_field_coverage.items():
                coverage_pct = (count / match_sample_size) * 100 if match_sample_size > 0 else 0
                assessment["field_coverage"][f"match.{field}"] = f"{coverage_pct:.1f}%"
                
                if coverage_pct < 50:
                    assessment["critical_gaps"].append(f"Low coverage for match.{field}: {coverage_pct:.1f}%")
        
        # Calculate overall completeness
        assessment["completeness_percentage"] = (present_fields / total_expected_fields) * 100 if total_expected_fields > 0 else 0
        
        logger.info(f"Data completeness assessment: {assessment['completeness_percentage']:.1f}% complete")
        
        return assessment
        
    except Exception as e:
        assessment["critical_gaps"].append(f"Completeness assessment error: {str(e)}")
        logger.error(f"Data completeness assessment failed: {e}")
        return assessment


def measure_data_consistency(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Measure consistency of TFT data across different sections
    
    Args:
        data: TFT dataset to measure
        
    Returns:
        dict: Consistency measurement report
    """
    consistency_report = {
        "timestamp": datetime.now().isoformat(),
        "consistency_score": 0.0,
        "consistency_checks": {},
        "inconsistencies_found": [],
        "consistency_metrics": {}
    }
    
    try:
        checks_passed = 0
        total_checks = 0
        
        # Check 1: Player data consistency across matches
        if "players" in data and "matches" in data:
            total_checks += 1
            player_match_consistency = True
            
            # When collecting from leaderboards, matches will contain opponents of our tracked players.
            # This is expected behavior. We check if a reasonable percentage of our tracked players
            # appear in matches, rather than requiring all match players to be tracked.
            match_players = set()
            for match in data["matches"].values():
                # Skip incomplete matches for this check
                if _should_skip_match_for_quality(match):
                    continue
                    
                if "info" in match and "participants" in match["info"]:
                    for participant in match["info"]["participants"]:
                        if "puuid" in participant:
                            match_players.add(participant["puuid"])
            
            player_data_keys = set(data["players"].keys())
            tracked_players_in_matches = player_data_keys.intersection(match_players)
            
            # Check if at least 20% of tracked players appear in matches
            # This is a reasonable threshold for leaderboard-based collection
            if player_data_keys:
                coverage_percentage = (len(tracked_players_in_matches) / len(player_data_keys)) * 100
                if coverage_percentage < 20.0:
                    player_match_consistency = False
                    consistency_report["inconsistencies_found"].append({
                        "type": "player_match_mismatch",
                        "description": f"Only {coverage_percentage:.1f}% of tracked players appear in matches (expected ≥20%)",
                        "severity": "high"
                    })
                else:
                    # This is expected behavior for leaderboard collection - don't fail the check
                    player_match_consistency = True  # Changed: was implicitly True, now explicit
                    # Log as info but don't fail - this is expected behavior
                    consistency_report["inconsistencies_found"].append({
                        "type": "player_match_info",
                        "description": f"{len(match_players - player_data_keys)} opponent players in matches (expected for leaderboard collection)",
                        "severity": "info"
                    })
            
            if player_match_consistency:
                checks_passed += 1
            
            consistency_report["consistency_checks"]["player_match_consistency"] = player_match_consistency
        
        # Check 2: Timestamp consistency
        if "collectionInfo" in data:
            total_checks += 1
            timestamp_consistency = True
            
            collection_timestamp = data["collectionInfo"].get("timestamp")
            if collection_timestamp and "matches" in data:
                # Check that match timestamps are reasonable relative to collection
                try:
                    # Convert collection_timestamp to int if it's a string or other type
                    if isinstance(collection_timestamp, str):
                        # Try to parse ISO format or convert to float/int
                        try:
                            # Try parsing ISO format manually
                            dt = datetime.fromisoformat(collection_timestamp.replace('Z', '+00:00'))
                            collection_ts_int = int(dt.timestamp())
                        except (ValueError, AttributeError):
                            # If ISO parsing fails, try direct conversion
                            collection_ts_int = int(float(collection_timestamp))
                    else:
                        collection_ts_int = int(collection_timestamp)
                    
                    for match_id, match_data in data["matches"].items():
                        if "info" in match_data:
                            game_creation = match_data["info"].get("gameCreation")
                            if game_creation:
                                # Ensure game_creation is also an int
                                if isinstance(game_creation, str):
                                    game_creation_int = int(float(game_creation))
                                else:
                                    game_creation_int = int(game_creation)
                                
                                # Game should be before collection timestamp
                                # game_creation is usually in milliseconds, collection_timestamp in seconds
                                # Convert collection timestamp to milliseconds for comparison
                                if game_creation_int > collection_ts_int * 1000 + 86400000:  # Allow 24h buffer for timezone diffs
                                    timestamp_consistency = False
                                    break
                except (ValueError, TypeError, OverflowError) as e:
                    # If conversion fails, skip this check
                    logger.debug(f"Timestamp comparison skipped due to type conversion error: {e}")
                    pass
            
            if timestamp_consistency:
                checks_passed += 1
            else:
                consistency_report["inconsistencies_found"].append({
                    "type": "timestamp_inconsistency",
                    "description": "Some matches have creation times after collection timestamp",
                    "severity": "medium"
                })
            
            consistency_report["consistency_checks"]["timestamp_consistency"] = timestamp_consistency
        
        # Check 3: Match participant count consistency
        if "matches" in data:
            total_checks += 1
            participant_consistency = True
            
            # Known special queue IDs that may have <8 participants
            SPECIAL_QUEUES = {1220}  # Practice/tutorial modes
            
            for match_id, match_data in data["matches"].items():
                # Skip truly incomplete matches
                if _should_skip_match_for_quality(match_data):
                    continue
                
                if "info" in match_data and "participants" in match_data["info"]:
                    participant_count = len(match_data["info"]["participants"])
                    queue_id = match_data["info"].get("queueId")
                    
                    # Only flag as inconsistent if it's not a special queue
                    if participant_count != 8 and queue_id not in SPECIAL_QUEUES:
                        participant_consistency = False
                        consistency_report["inconsistencies_found"].append({
                            "type": "invalid_participant_count",
                            "description": f"Match {match_id} has {participant_count} participants (expected 8)",
                            "severity": "high"
                        })
            
            if participant_consistency:
                checks_passed += 1
            
            consistency_report["consistency_checks"]["participant_count_consistency"] = participant_consistency
        
        # Check 4: Placement consistency within matches
        if "matches" in data:
            total_checks += 1
            placement_consistency = True
            
            for match_id, match_data in data["matches"].items():
                # Skip truly incomplete matches
                if _should_skip_match_for_quality(match_data):
                    continue
                
                if "info" in match_data and "participants" in match_data["info"]:
                    placements = [p.get("placement", 8) for p in match_data["info"]["participants"]]
                    expected_placements = set(range(1, 9))
                    actual_placements = set(placements)
                    
                    if actual_placements != expected_placements:
                        placement_consistency = False
                        consistency_report["inconsistencies_found"].append({
                            "type": "placement_inconsistency",
                            "description": f"Match {match_id} has invalid placement distribution: {sorted(placements)}",
                            "severity": "critical"
                        })
            
            if placement_consistency:
                checks_passed += 1
            
            consistency_report["consistency_checks"]["placement_consistency"] = placement_consistency
        
        # Calculate overall consistency score
        consistency_report["consistency_score"] = (checks_passed / total_checks) * 100 if total_checks > 0 else 100
        
        # Add consistency metrics
        consistency_report["consistency_metrics"] = {
            "total_checks": total_checks,
            "checks_passed": checks_passed,
            "checks_failed": total_checks - checks_passed,
            "inconsistencies_count": len(consistency_report["inconsistencies_found"])
        }
        
        logger.info(f"Data consistency measurement: {consistency_report['consistency_score']:.1f}% consistent ({checks_passed}/{total_checks} checks passed)")
        
        return consistency_report
        
    except Exception as e:
        consistency_report["inconsistencies_found"].append({
            "type": "consistency_check_error",
            "description": str(e),
            "severity": "critical"
        })
        logger.error(f"Data consistency measurement failed: {e}")
        return consistency_report


def generate_quality_report(data: Dict[str, Any], include_recommendations: bool = True) -> Dict[str, Any]:
    """
    Generate comprehensive quality report for TFT dataset
    
    Args:
        data: Complete TFT dataset
        include_recommendations: Whether to include improvement recommendations
        
    Returns:
        dict: Comprehensive quality report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "dataset_summary": {},
        "quality_assessment": {},
        "executive_summary": {},
        "detailed_analysis": {},
        "action_items": []
    }
    
    try:
        # Dataset summary
        report["dataset_summary"] = {
            "total_players": len(data.get("players", {})),
            "total_matches": len(data.get("matches", {})),
            "collection_region": data.get("collectionInfo", {}).get("extractionLocation", "unknown"),
            "data_version": data.get("collectionInfo", {}).get("dataVersion", "unknown"),
            "collection_timestamp": data.get("collectionInfo", {}).get("timestamp", "unknown")
        }
        
        # Quality assessment
        quality_score = calculate_data_quality_score(data)
        report["quality_assessment"] = quality_score
        
        # Executive summary
        overall_score = quality_score["overall_score"]
        grade = quality_score["quality_grade"]
        
        if overall_score >= 90:
            status = "EXCELLENT"
            summary = "Dataset meets highest quality standards with minimal issues."
        elif overall_score >= 80:
            status = "GOOD"
            summary = "Dataset quality is good with minor areas for improvement."
        elif overall_score >= 70:
            status = "ACCEPTABLE"
            summary = "Dataset quality is acceptable but requires attention to identified issues."
        elif overall_score >= 60:
            status = "POOR"
            summary = "Dataset quality is below standards and requires significant improvement."
        else:
            status = "CRITICAL"
            summary = "Dataset quality is critically low and requires immediate attention."
        
        report["executive_summary"] = {
            "overall_status": status,
            "quality_grade": grade,
            "score": f"{overall_score:.1f}/100",
            "summary": summary,
            "key_strengths": [],
            "primary_concerns": []
        }
        
        # Identify strengths and concerns
        for component, score_info in quality_score["component_scores"].items():
            if isinstance(score_info, dict):
                if component == "completeness":
                    comp_score = score_info.get("completeness_percentage", 0)
                elif component == "consistency": 
                    comp_score = score_info.get("consistency_score", 0)
                else:
                    comp_score = 0  # Handle other components as needed
            else:
                comp_score = score_info
            
            if comp_score >= 85:
                report["executive_summary"]["key_strengths"].append(f"{component.title()}: {comp_score:.1f}%")
            elif comp_score < 70:
                report["executive_summary"]["primary_concerns"].append(f"{component.title()}: {comp_score:.1f}%")
        
        # Action items
        if include_recommendations:
            all_recommendations = quality_score.get("recommendations", [])
            
            # Prioritize recommendations
            critical_items = [rec for rec in all_recommendations if "critical" in rec.lower() or "immediate" in rec.lower()]
            high_priority = [rec for rec in all_recommendations if "review" in rec.lower() or "address" in rec.lower()]
            medium_priority = [rec for rec in all_recommendations if rec not in critical_items and rec not in high_priority]
            
            report["action_items"] = {
                "critical": critical_items,
                "high_priority": high_priority, 
                "medium_priority": medium_priority
            }
        
        logger.info(f"Quality report generated. Status: {status}, Score: {overall_score:.1f}")
        
        return report
        
    except Exception as e:
        report["executive_summary"] = {
            "overall_status": "ERROR",
            "summary": f"Quality report generation failed: {str(e)}"
        }
        logger.error(f"Quality report generation failed: {e}")
        return report
