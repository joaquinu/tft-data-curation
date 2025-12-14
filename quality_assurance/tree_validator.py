"""
Tree Validator Module

Hierarchical/tree-based data validation for TFT match structures.
Validates the hierarchical relationships and data integrity in TFT data structures.
"""

import logging
import networkx as nx
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


def should_skip_match(match: Dict[str, Any]) -> bool:
    """
    Determine if a match should be skipped for validation.
    
    Args:
        match: Match data to check
        
    Returns:
        bool: True if match should be skipped
    """
    if "info" not in match:
        return True
    
    if "participants" not in match["info"]:
        return True
    
    participants = match["info"]["participants"]
    if not isinstance(participants, list) or len(participants) < 2:
        return True
    
    return False


def calculate_tree_validation_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a tree validation score for quality assessment.
    
    Args:
        data: TFT dataset to validate
        
    Returns:
        dict: Tree validation score and details
    """
    result = {
        "tree_score": 100.0,
        "tree_grade": "A",
        "structure_valid": True,
        "hierarchy_issues_count": 0,
        "relationship_integrity_score": 100.0,
        "details": {}
    }
    
    try:
        hierarchy_report = validate_hierarchical_structure(data)
        result["details"]["hierarchy"] = hierarchy_report
        result["structure_valid"] = hierarchy_report["structure_valid"]
        result["hierarchy_issues_count"] = len(hierarchy_report.get("hierarchy_issues", []))
        
        if "relationship_integrity" in hierarchy_report:
            result["relationship_integrity_score"] = hierarchy_report["relationship_integrity"].get(
                "relationship_integrity_score", 100.0
            )
        
        # Calculate overall tree score: 60% structure, 40% relationships
        structure_score = 100.0 if result["structure_valid"] else 50.0
        issue_penalty = min(30, result["hierarchy_issues_count"] * 5)
        structure_score -= issue_penalty
        
        result["tree_score"] = (
            structure_score * 0.6 + 
            result["relationship_integrity_score"] * 0.4
        )
        result["tree_grade"] = _get_grade(result["tree_score"])
        
        logger.info(f"Tree validation score: {result['tree_score']:.1f} (Grade: {result['tree_grade']})")
        return result
        
    except Exception as e:
        result["tree_score"] = 0.0
        result["structure_valid"] = False
        result["error"] = str(e)
        logger.error(f"Tree validation score calculation failed: {e}")
        return result


def validate_hierarchical_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate hierarchical structure of TFT data.
    
    Args:
        data: TFT dataset with hierarchical structure
        
    Returns:
        dict: Hierarchical structure validation report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "structure_valid": True,
        "hierarchy_issues": [],
        "tree_analysis": {},
        "relationship_integrity": {},
        "structural_recommendations": []
    }
    
    try:
        # Build and analyze tree structure
        tree = _build_data_tree(data)
        report["tree_analysis"] = _analyze_tree_structure(tree)
        
        # Validate root structure
        if "collectionInfo" not in data:
            report["hierarchy_issues"].append({
                "level": "root",
                "issue": "Missing collection info root node",
                "severity": "critical"
            })
            report["structure_valid"] = False
        
        # Validate players
        if "players" in data:
            player_issues = validate_player_hierarchy(data["players"])
            report["hierarchy_issues"].extend(player_issues)
            critical = [i for i in player_issues if i.get("severity") in ("critical", "high")]
            if critical:
                report["structure_valid"] = False
        
        # Validate matches
        if "matches" in data:
            match_issues = validate_match_hierarchy(data["matches"])
            report["hierarchy_issues"].extend(match_issues)
            critical = [i for i in match_issues if i.get("severity") == "critical"]
            if critical:
                report["structure_valid"] = False
        
        # Validate cross-hierarchy relationships
        report["relationship_integrity"] = _validate_cross_hierarchy_relationships(data)
        
        # Generate recommendations
        critical = [i for i in report["hierarchy_issues"] if i.get("severity") == "critical"]
        high = [i for i in report["hierarchy_issues"] if i.get("severity") == "high"]
        
        if critical:
            report["structural_recommendations"].append("Fix critical hierarchical structure issues")
        if high:
            report["structural_recommendations"].append("Review high-severity hierarchy issues")
        if report["structure_valid"] and not critical:
            report["structural_recommendations"].append("Hierarchical structure is valid")
        
        logger.info(f"Hierarchical validation complete. Valid: {report['structure_valid']}")
        return report
        
    except Exception as e:
        report["hierarchy_issues"].append({
            "level": "system",
            "issue": f"Validation error: {str(e)}",
            "severity": "critical"
        })
        report["structure_valid"] = False
        logger.error(f"Hierarchical structure validation failed: {e}")
        return report


def validate_player_hierarchy(players_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate player-level hierarchy structure.
    
    Args:
        players_data: Dictionary of player data
        
    Returns:
        list: List of hierarchy issues found
    """
    issues = []
    
    try:
        if not players_data:
            issues.append({
                "level": "players",
                "issue": "Empty players section",
                "severity": "high"
            })
            return issues
        
        # Sample validation to avoid excessive processing
        sample_size = min(100, len(players_data))
        sampled = list(players_data.items())[:sample_size]
        
        invalid_puuid = 0
        invalid_structure = 0
        
        for puuid, player_data in sampled:
            if not isinstance(puuid, str) or len(puuid) < 20:
                invalid_puuid += 1
            
            if not isinstance(player_data, dict):
                invalid_structure += 1
                continue
            
            if "matches" in player_data:
                if not isinstance(player_data["matches"], (dict, list)):
                    issues.append({
                        "level": "players",
                        "issue": f"Player {puuid[:8]}... has invalid matches structure",
                        "severity": "high"
                    })
        
        if invalid_puuid > 0:
            issues.append({
                "level": "players",
                "issue": f"{invalid_puuid} players have invalid PUUID format",
                "severity": "medium"
            })
        
        if invalid_structure > 0:
            issues.append({
                "level": "players",
                "issue": f"{invalid_structure} players have invalid data structure",
                "severity": "high"
            })
        
        return issues
        
    except Exception as e:
        issues.append({
            "level": "players",
            "issue": f"Player hierarchy validation error: {str(e)}",
            "severity": "critical"
        })
        return issues


def validate_match_hierarchy(matches_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate match-level hierarchy including participant structure.
    
    Args:
        matches_data: Dictionary of match data
        
    Returns:
        list: List of hierarchy issues found (aggregated)
    """
    issues = []
    
    try:
        if not matches_data:
            issues.append({
                "level": "matches",
                "issue": "Empty matches section",
                "severity": "high"
            })
            return issues
        
        # Track counts for aggregation
        missing_info = 0
        missing_participants = 0
        wrong_participant_count = 0
        invalid_placement = 0
        invalid_units = 0
        invalid_traits = 0
        
        total = len(matches_data)
        
        for match_id, match_data in matches_data.items():
            if "info" not in match_data:
                missing_info += 1
                continue
            
            match_info = match_data["info"]
            
            if "participants" not in match_info:
                missing_participants += 1
                continue
            
            participants = match_info["participants"]
            
            # Valid participant count is 2-8 (handles special modes)
            if len(participants) < 2 or len(participants) > 8:
                wrong_participant_count += 1
            
            for p in participants:
                placement = p.get("placement")
                if placement is None or not isinstance(placement, int) or placement < 1 or placement > 8:
                    invalid_placement += 1
                
                if "units" in p and not isinstance(p["units"], list):
                    invalid_units += 1
                
                if "traits" in p and not isinstance(p["traits"], list):
                    invalid_traits += 1
        
        # Report aggregated issues
        if missing_info > 0:
            issues.append({
                "level": "matches",
                "issue": f"{missing_info} matches missing info section",
                "severity": "critical",
                "percentage": (missing_info / total) * 100
            })
        
        if missing_participants > 0:
            issues.append({
                "level": "matches",
                "issue": f"{missing_participants} matches missing participants",
                "severity": "critical",
                "percentage": (missing_participants / total) * 100
            })
        
        if wrong_participant_count > 0:
            issues.append({
                "level": "matches",
                "issue": f"{wrong_participant_count} matches have invalid participant count",
                "severity": "high",
                "percentage": (wrong_participant_count / total) * 100
            })
        
        if invalid_placement > 0:
            issues.append({
                "level": "participants",
                "issue": f"{invalid_placement} participants have invalid placement",
                "severity": "high"
            })
        
        if invalid_units > 0:
            issues.append({
                "level": "participants",
                "issue": f"{invalid_units} participants have invalid units structure",
                "severity": "medium"
            })
        
        if invalid_traits > 0:
            issues.append({
                "level": "participants",
                "issue": f"{invalid_traits} participants have invalid traits structure",
                "severity": "medium"
            })
        
        return issues
        
    except Exception as e:
        issues.append({
            "level": "matches",
            "issue": f"Match hierarchy validation error: {str(e)}",
            "severity": "critical"
        })
        return issues


def _validate_cross_hierarchy_relationships(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate relationships across hierarchy levels.
    
    For leaderboard-based collection:
    - Orphaned players (no matches) are expected for inactive players
    - Orphaned participants (not in player list) are expected (opponents)
    
    Args:
        data: Complete TFT dataset
        
    Returns:
        dict: Cross-hierarchy relationship validation report
    """
    report = {
        "relationships_valid": True,
        "player_match_links": {},
        "orphaned_data": {},
        "relationship_integrity_score": 100.0,
        "cross_reference_issues": []
    }
    
    try:
        player_puuids = set(data.get("players", {}).keys())
        match_puuids = set()
        
        for match_data in data.get("matches", {}).values():
            if "info" in match_data and "participants" in match_data["info"]:
                for p in match_data["info"]["participants"]:
                    if "puuid" in p:
                        match_puuids.add(p["puuid"])
        
        linked = player_puuids.intersection(match_puuids)
        
        report["orphaned_data"] = {
            "players_without_matches": len(player_puuids - match_puuids),
            "opponents_in_matches": len(match_puuids - player_puuids),
            "linked_players": len(linked)
        }
        
        # Calculate integrity score based on player coverage
        if player_puuids:
            coverage = len(linked) / len(player_puuids)
            
            if coverage >= 0.20:
                report["relationship_integrity_score"] = 80.0 + (coverage - 0.20) * (20.0 / 0.80)
            else:
                report["relationship_integrity_score"] = (coverage / 0.20) * 80.0
                report["cross_reference_issues"].append({
                    "type": "low_player_coverage",
                    "severity": "medium",
                    "description": f"Only {coverage*100:.1f}% of tracked players appear in matches"
                })
        
        if report["relationship_integrity_score"] < 60:
            report["relationships_valid"] = False
        
        report["player_match_links"] = {
            "total_players": len(player_puuids),
            "total_match_participants": len(match_puuids),
            "linked_players": len(linked),
            "player_coverage_percentage": (len(linked) / max(1, len(player_puuids))) * 100
        }
        
        logger.info(f"Cross-hierarchy validation: integrity score {report['relationship_integrity_score']:.1f}")
        return report
        
    except Exception as e:
        report["cross_reference_issues"].append({
            "type": "validation_error",
            "description": str(e),
            "severity": "critical"
        })
        report["relationships_valid"] = False
        logger.error(f"Cross-hierarchy validation failed: {e}")
        return report


def _build_data_tree(data: Dict[str, Any]) -> nx.DiGraph:
    """
    Build a directed graph representing the data hierarchy.
    
    Args:
        data: TFT dataset
        
    Returns:
        nx.DiGraph: Tree representation
    """
    tree = nx.DiGraph()
    
    try:
        tree.add_node("collection", type="root")
        
        if "players" in data:
            tree.add_node("players", type="container")
            tree.add_edge("collection", "players")
            
            # Sample players for large datasets
            player_items = list(data["players"].items())
            sample = player_items[:min(500, len(player_items))]
            
            for puuid, _ in sample:
                node = f"player_{puuid[:8]}"
                tree.add_node(node, type="player")
                tree.add_edge("players", node)
        
        if "matches" in data:
            tree.add_node("matches", type="container")
            tree.add_edge("collection", "matches")
            
            # Sample matches for large datasets
            match_items = list(data["matches"].items())
            sample = match_items[:min(200, len(match_items))]
            
            for match_id, match_data in sample:
                match_node = f"match_{match_id[:20]}"
                tree.add_node(match_node, type="match")
                tree.add_edge("matches", match_node)
                
                participants = match_data.get("info", {}).get("participants", [])
                for i in range(len(participants)):
                    p_node = f"participant_{match_id[:10]}_{i}"
                    tree.add_node(p_node, type="participant")
                    tree.add_edge(match_node, p_node)
        
        return tree
        
    except Exception as e:
        logger.error(f"Failed to build data tree: {e}")
        return nx.DiGraph()


def _analyze_tree_structure(tree: nx.DiGraph) -> Dict[str, Any]:
    """
    Analyze tree structure properties.
    
    Args:
        tree: NetworkX directed graph
        
    Returns:
        dict: Tree structure analysis
    """
    analysis = {
        "node_count": tree.number_of_nodes(),
        "edge_count": tree.number_of_edges(),
        "max_depth": 0,
        "branching_factor": {},
        "tree_properties": {}
    }
    
    try:
        if tree.number_of_nodes() == 0:
            return analysis
        
        roots = [n for n in tree.nodes() if tree.in_degree(n) == 0]
        
        if not roots:
            analysis["tree_properties"]["has_cycles"] = True
            return analysis
        
        analysis["tree_properties"]["root_count"] = len(roots)
        analysis["tree_properties"]["has_cycles"] = not nx.is_directed_acyclic_graph(tree)
        
        if roots:
            depths = nx.single_source_shortest_path_length(tree, roots[0])
            analysis["max_depth"] = max(depths.values()) if depths else 0
        
        # Calculate branching factors by node type
        node_types = defaultdict(list)
        for node, attrs in tree.nodes(data=True):
            node_types[attrs.get("type", "unknown")].append(node)
        
        for ntype, nodes in node_types.items():
            degrees = [tree.out_degree(n) for n in nodes]
            if degrees:
                analysis["branching_factor"][ntype] = {
                    "avg": sum(degrees) / len(degrees),
                    "max": max(degrees),
                    "min": min(degrees)
                }
        
        return analysis
        
    except Exception as e:
        analysis["error"] = str(e)
        logger.error(f"Tree analysis failed: {e}")
        return analysis


# Legacy function aliases for backward compatibility
def check_tree_data_integrity(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive tree-based data integrity check.
    
    Note: For new code, use calculate_tree_validation_score() instead.
    
    Args:
        data: Complete TFT dataset
        
    Returns:
        dict: Tree data integrity report
    """
    result = calculate_tree_validation_score(data)
    
    # Transform to legacy format
    return {
        "timestamp": datetime.now().isoformat(),
        "tree_integrity_score": result["tree_score"],
        "structural_integrity": result["structure_valid"],
        "data_consistency": result["structure_valid"],
        "hierarchy_health": result.get("details", {}),
        "integrity_recommendations": []
    }


def analyze_data_relationships(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze data relationships within the hierarchical structure.
    
    Note: For new code, use validate_hierarchical_structure() instead.
    
    Args:
        data: Complete TFT dataset
        
    Returns:
        dict: Data relationships analysis report
    """
    hierarchy = validate_hierarchical_structure(data)
    rel = hierarchy.get("relationship_integrity", {})
    
    return {
        "timestamp": datetime.now().isoformat(),
        "relationship_summary": rel.get("player_match_links", {}),
        "network_metrics": {
            "total_nodes": hierarchy.get("tree_analysis", {}).get("node_count", 0),
            "total_edges": hierarchy.get("tree_analysis", {}).get("edge_count", 0)
        },
        "relationship_quality": {
            "connectivity_score": rel.get("relationship_integrity_score", 0)
        },
        "insights": rel.get("cross_reference_issues", [])
    }
