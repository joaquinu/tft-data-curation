"""
Anomaly Detector Module

Statistical analysis and outlier detection algorithms for TFT data.
"""

import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


def _get_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


def detect_statistical_anomalies(match_data: Dict[str, Any], threshold_std: float = 3.0) -> Dict[str, Any]:
    """
    Detect data quality anomalies in match data.
    
    Focuses on impossible/corrupted values rather than normal statistical variance.
    Statistical outliers are reported in summary but not as anomalies.
    
    Args:
        match_data: Dictionary containing match information
        threshold_std: Standard deviation threshold for outlier detection
        
    Returns:
        dict: Anomaly detection report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "anomalies_detected": [],
        "statistical_summary": {},
        "outlier_summary": {},
        "threshold_used": threshold_std,
        "anomaly_count": 0,
        "data_quality_flags": []
    }
    
    try:
        # Extract match metrics for analysis
        placements = []
        game_lengths = []
        levels = []
        damage_values = []
        
        # Track impossible values (actual anomalies)
        invalid_placements = 0
        invalid_levels = 0
        negative_damage = 0
        impossible_game_lengths = 0
        
        for match_id, match_info in match_data.items():
            if "info" in match_info:
                info = match_info["info"]
                
                # Game length analysis (in minutes)
                game_length = info.get("game_length", 0) / 60
                if game_length > 0:
                    game_lengths.append(game_length)
                    # Flag impossible game lengths (< 5 min or > 60 min)
                    if game_length < 5 or game_length > 60:
                        impossible_game_lengths += 1
                
                # Participant analysis
                if "participants" in info:
                    for participant in info["participants"]:
                        placement = participant.get("placement", 8)
                        level = participant.get("level", 1)
                        damage = participant.get("total_damage_to_players", 0)
                        
                        placements.append(placement)
                        levels.append(level)
                        damage_values.append(damage)
                        
                        # Flag impossible values
                        if placement < 1 or placement > 8:
                            invalid_placements += 1
                        if level < 1 or level > 10:
                            invalid_levels += 1
                        if damage < 0:
                            negative_damage += 1
        
        # Record impossible value anomalies (aggregated)
        if invalid_placements > 0:
            report["anomalies_detected"].append({
                "type": "invalid_placement",
                "count": invalid_placements,
                "description": f"{invalid_placements} participants with placement outside 1-8",
                "severity": "high"
            })
        
        if invalid_levels > 0:
            report["anomalies_detected"].append({
                "type": "invalid_level",
                "count": invalid_levels,
                "description": f"{invalid_levels} participants with level outside 1-10",
                "severity": "high"
            })
        
        if negative_damage > 0:
            report["anomalies_detected"].append({
                "type": "negative_damage",
                "count": negative_damage,
                "description": f"{negative_damage} participants with negative damage",
                "severity": "critical"
            })
        
        if impossible_game_lengths > 0:
            report["anomalies_detected"].append({
                "type": "impossible_game_length",
                "count": impossible_game_lengths,
                "description": f"{impossible_game_lengths} matches with game length <5min or >60min",
                "severity": "medium"
            })
        
        # Calculate statistical summaries (informational, not anomalies)
        if placements:
            report["statistical_summary"]["placements"] = {
                "mean": float(np.mean(placements)),
                "std": float(np.std(placements)),
                "min": min(placements),
                "max": max(placements),
                "count": len(placements)
            }
        
        if game_lengths:
            report["statistical_summary"]["game_lengths"] = {
                "mean": float(np.mean(game_lengths)),
                "std": float(np.std(game_lengths)),
                "min": min(game_lengths),
                "max": max(game_lengths),
                "count": len(game_lengths)
            }
        
        if levels:
            report["statistical_summary"]["levels"] = {
                "mean": float(np.mean(levels)),
                "std": float(np.std(levels)),
                "min": min(levels),
                "max": max(levels),
                "count": len(levels)
            }
        
        if damage_values:
            damage_mean = np.mean(damage_values)
            damage_std = np.std(damage_values)
            report["statistical_summary"]["damage"] = {
                "mean": float(damage_mean),
                "std": float(damage_std),
                "min": min(damage_values),
                "max": max(damage_values),
                "count": len(damage_values)
            }
            
            # Count statistical outliers (informational only)
            high_damage_outliers = sum(1 for d in damage_values 
                                       if d > damage_mean + threshold_std * damage_std)
            report["outlier_summary"]["high_damage_outliers"] = high_damage_outliers
        
        if game_lengths:
            length_mean = np.mean(game_lengths)
            length_std = np.std(game_lengths)
            length_outliers = sum(1 for g in game_lengths 
                                  if abs(g - length_mean) > threshold_std * length_std)
            report["outlier_summary"]["game_length_outliers"] = length_outliers
        
        report["anomaly_count"] = len(report["anomalies_detected"])
        
        # Data quality flags
        if len(game_lengths) < len(match_data) * 0.8:
            report["data_quality_flags"].append("Missing game length data in >20% of matches")
        
        if len(placements) < len(match_data) * 8 * 0.8:
            report["data_quality_flags"].append("Missing participant data detected")
        
        logger.info(f"Statistical anomaly detection complete. Found {report['anomaly_count']} data quality issues")
        
        return report
        
    except Exception as e:
        report["anomalies_detected"].append({
            "type": "analysis_error",
            "value": str(e),
            "severity": "critical"
        })
        logger.error(f"Statistical anomaly detection failed: {e}")
        return report


def identify_performance_outliers(player_data: Dict[str, Any], outlier_threshold: float = 3.0) -> Dict[str, Any]:
    """
    Identify data quality issues in player data.
    
    Focuses on impossible values and data integrity issues rather than
    performance variance (which is normal player skill distribution).
    
    Args:
        player_data: Dictionary containing player performance data
        outlier_threshold: Z-score threshold for statistical outlier detection
        
    Returns:
        dict: Outlier detection report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "outliers_detected": [],
        "performance_metrics": {},
        "performance_distribution": {},
        "threshold_used": outlier_threshold,
        "total_players": 0,
        "data_quality_issues": 0
    }
    
    try:
        # Collect performance metrics across all players
        all_placements = []
        all_levels = []
        all_points = []
        
        # Track data quality issues
        invalid_puuids = 0
        negative_lp = 0
        impossible_lp = 0  # LP > 2000 is suspicious
        
        report["total_players"] = len(player_data)
        
        for puuid, player_info in player_data.items():
            # Check for data quality issues
            if not isinstance(puuid, str) or len(puuid) < 20:
                invalid_puuids += 1
            
            league_points = player_info.get("leaguePoints", 0)
            if league_points is not None:
                if league_points < 0:
                    negative_lp += 1
                elif league_points > 2000:
                    impossible_lp += 1
                all_points.append(league_points)
            
            # Collect match statistics
            if "matches" in player_info:
                for match_id, match_data in player_info["matches"].items():
                    if "info" in match_data and "participants" in match_data["info"]:
                        for participant in match_data["info"]["participants"]:
                            if participant.get("puuid") == puuid:
                                placement = participant.get("placement", 8)
                                level = participant.get("level", 1)
                                all_placements.append(placement)
                                all_levels.append(level)
        
        # Record data quality anomalies (aggregated)
        if invalid_puuids > 0:
            report["outliers_detected"].append({
                "outlier_type": "invalid_puuid",
                "count": invalid_puuids,
                "description": f"{invalid_puuids} players with invalid PUUID format",
                "severity": "high"
            })
        
        if negative_lp > 0:
            report["outliers_detected"].append({
                "outlier_type": "negative_lp",
                "count": negative_lp,
                "description": f"{negative_lp} players with negative LP",
                "severity": "critical"
            })
        
        if impossible_lp > 0:
            report["outliers_detected"].append({
                "outlier_type": "impossible_lp",
                "count": impossible_lp,
                "description": f"{impossible_lp} players with LP > 2000 (suspicious)",
                "severity": "medium"
            })
        
        # Calculate performance metrics (informational only)
        if all_placements:
            report["performance_metrics"]["placements"] = {
                "mean": float(np.mean(all_placements)),
                "std": float(np.std(all_placements)),
                "total_games": len(all_placements)
            }
        
        if all_levels:
            report["performance_metrics"]["levels"] = {
                "mean": float(np.mean(all_levels)),
                "std": float(np.std(all_levels))
            }
        
        if all_points:
            report["performance_metrics"]["league_points"] = {
                "mean": float(np.mean(all_points)),
                "std": float(np.std(all_points)),
                "min": min(all_points),
                "max": max(all_points)
            }
        
        report["data_quality_issues"] = len(report["outliers_detected"])
        
        logger.info(f"Player data analysis complete. Found {report['data_quality_issues']} data quality issues")
        
        return report
        
    except Exception as e:
        report["outliers_detected"].append({
            "outlier_type": "analysis_error",
            "value": str(e),
            "severity": "critical"
        })
        logger.error(f"Player data analysis failed: {e}")
        return report


def analyze_data_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze patterns in TFT data for unusual trends or distributions
    
    Args:
        data: Complete TFT dataset
        
    Returns:
        dict: Pattern analysis report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "patterns_identified": [],
        "distribution_analysis": {},
        "temporal_patterns": {},
        "composition_patterns": {},
        "anomalous_patterns": []
    }
    
    try:
        # Analyze match distribution patterns
        if "matches" in data:
            match_times = []
            queue_types = defaultdict(int)
            game_versions = defaultdict(int)
            
            for match_id, match_info in data["matches"].items():
                if "info" in match_info:
                    info = match_info["info"]
                    
                    # Temporal patterns
                    game_creation = info.get("gameCreation", 0)
                    if game_creation:
                        match_times.append(game_creation)
                    
                    # Queue type distribution
                    queue_id = info.get("queueId", "unknown")
                    queue_types[queue_id] += 1
                    
                    # Game version distribution
                    game_version = info.get("gameVersion", "unknown")
                    game_versions[game_version] += 1
            
            # Temporal pattern analysis
            if match_times:
                match_times.sort()
                time_gaps = [match_times[i+1] - match_times[i] for i in range(len(match_times)-1)]
                
                if time_gaps:
                    avg_gap = np.mean(time_gaps)
                    gap_std = np.std(time_gaps)
                    
                    report["temporal_patterns"] = {
                        "total_matches": len(match_times),
                        "time_span_hours": (match_times[-1] - match_times[0]) / (1000 * 3600),
                        "avg_gap_minutes": avg_gap / (1000 * 60),
                        "gap_consistency": gap_std / avg_gap if avg_gap > 0 else 0
                    }
                    
                    # Detect unusual temporal patterns
                    if gap_std / avg_gap > 2.0:  # High variance in gaps
                        report["anomalous_patterns"].append({
                            "type": "irregular_collection_timing",
                            "description": "High variance in match collection timing",
                            "severity": "medium"
                        })
            
            # Queue type analysis
            total_matches = sum(queue_types.values())
            if total_matches > 0:
                queue_distribution = {k: (v/total_matches)*100 for k, v in queue_types.items()}
                report["distribution_analysis"]["queue_types"] = queue_distribution
                
                # Check for unusual queue distributions
                if queue_distribution.get(1100, 0) < 70:  # Ranked TFT should be majority
                    report["anomalous_patterns"].append({
                        "type": "unusual_queue_distribution",
                        "description": f"Low ranked queue percentage: {queue_distribution.get(1100, 0):.1f}%",
                        "severity": "low"
                    })
        
        # Analyze player patterns
        if "players" in data:
            tier_distribution = defaultdict(int)
            rank_distribution = defaultdict(int)
            
            for puuid, player_info in data["players"].items():
                tier = player_info.get("tier", "UNRANKED")
                rank = player_info.get("rank", "")
                
                tier_distribution[tier] += 1
                if rank:
                    rank_distribution[f"{tier}_{rank}"] += 1
            
            total_players = len(data["players"])
            if total_players > 0:
                tier_percentages = {k: (v/total_players)*100 for k, v in tier_distribution.items()}
                report["distribution_analysis"]["tiers"] = tier_percentages
                
                # Check for unusual tier distributions
                if tier_percentages.get("CHALLENGER", 0) > 10:  # Too many Challenger players
                    report["anomalous_patterns"].append({
                        "type": "unusual_tier_distribution",
                        "description": f"High Challenger percentage: {tier_percentages.get('CHALLENGER', 0):.1f}%",
                        "severity": "medium"
                    })
        
        # Identify positive patterns
        if len(report["anomalous_patterns"]) == 0:
            report["patterns_identified"].append({
                "type": "healthy_data_distribution",
                "description": "No anomalous patterns detected in data distribution"
            })
        
        logger.info(f"Pattern analysis complete. Found {len(report['anomalous_patterns'])} anomalous patterns")
        
        return report
        
    except Exception as e:
        report["anomalous_patterns"].append({
            "type": "pattern_analysis_error",
            "description": str(e),
            "severity": "critical"
        })
        logger.error(f"Pattern analysis failed: {e}")
        return report


def generate_anomaly_report(data: Dict[str, Any], include_details: bool = True) -> Dict[str, Any]:
    """
    Generate comprehensive anomaly detection report
    
    Args:
        data: Complete TFT dataset
        include_details: Whether to include detailed analysis
        
    Returns:
        dict: Comprehensive anomaly report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_health_score": 100.0,
        "health_grade": "A",
        "anomaly_summary": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "recommendations": [],
        "detailed_findings": {}
    }
    
    try:
        # Run all anomaly detection modules
        if include_details:
            # Statistical anomalies
            if "matches" in data:
                stat_report = detect_statistical_anomalies(data["matches"])
                report["detailed_findings"]["statistical_anomalies"] = stat_report
                
                # Count anomalies by severity
                for anomaly in stat_report["anomalies_detected"]:
                    severity = anomaly.get("severity", "low")
                    report["anomaly_summary"][severity] += 1
            
            # Performance outliers
            if "players" in data:
                outlier_report = identify_performance_outliers(data["players"])
                report["detailed_findings"]["performance_outliers"] = outlier_report
                
                # Count outliers by severity
                for outlier in outlier_report["outliers_detected"]:
                    severity = outlier.get("severity", "low")
                    report["anomaly_summary"][severity] += 1
            
            # Data patterns
            pattern_report = analyze_data_patterns(data)
            report["detailed_findings"]["data_patterns"] = pattern_report
            
            # Count pattern anomalies
            for pattern in pattern_report["anomalous_patterns"]:
                severity = pattern.get("severity", "low")
                report["anomaly_summary"][severity] += 1
        
        # Calculate overall health score based on anomaly percentages
        total_matches = len(data.get("matches", {}))
        total_players = len(data.get("players", {}))
        total_data_points = max(1, total_matches + total_players)
        
        # Calculate anomaly rate as percentage of data
        total_anomalies = sum(report["anomaly_summary"].values())
        anomaly_rate = (total_anomalies / total_data_points) * 100
        
        # Weighted severity impact (capped per category)
        severity_max_penalty = {"critical": 40, "high": 25, "medium": 15, "low": 10}
        severity_thresholds = {"critical": 1, "high": 10, "medium": 50, "low": 100}
        
        penalty = 0.0
        for severity, count in report["anomaly_summary"].items():
            if count > 0:
                # Calculate penalty as ratio of count to threshold, capped at max
                ratio = min(1.0, count / severity_thresholds[severity])
                penalty += ratio * severity_max_penalty[severity]
        
        report["overall_health_score"] = max(0.0, 100.0 - penalty)
        report["health_grade"] = _get_grade(report["overall_health_score"])
        report["anomaly_rate"] = anomaly_rate
        
        # Generate recommendations
        if report["anomaly_summary"]["critical"] > 0:
            report["recommendations"].append("Address critical anomalies immediately - data integrity at risk")
        
        if report["anomaly_summary"]["high"] > 5:
            report["recommendations"].append("Review data collection process - high number of severe anomalies")
        
        if report["overall_health_score"] < 70:
            report["recommendations"].append("Data quality below acceptable threshold - comprehensive review needed")
        elif report["overall_health_score"] > 90:
            report["recommendations"].append("Data quality excellent - maintain current standards")
        
        logger.info(f"Anomaly detection complete. Health score: {report['overall_health_score']:.1f}")
        
        return report
        
    except Exception as e:
        report["detailed_findings"]["generation_error"] = str(e)
        report["overall_health_score"] = 0.0
        logger.error(f"Anomaly report generation failed: {e}")
        return report
