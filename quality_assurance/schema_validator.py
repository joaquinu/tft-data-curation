"""
Schema Validator Module

JSON-LD schema validation and compliance verification for TFT data.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_schema_structure(schema_generator) -> bool:
    """
    Validate that the schema has all required components
    
    Args:
        schema_generator: TFTSchemaGenerator instance
        
    Returns:
        bool: True if schema is valid, False otherwise
    """
    try:
        schema = schema_generator.create_comprehensive_schema()
        
        # Check required top-level keys
        required_keys = ["@context", "@graph"]
        if not all(key in schema for key in required_keys):
            return False
            
        # Check context has required namespaces
        context = schema["@context"]
        required_namespaces = ["xsd", "rdf", "rdfs", "dcterms"]
        if not all(ns in context for ns in required_namespaces):
            return False
            
        # Check TFT entities are defined
        tft_entities = ["TFTDataCollection", "TFTPlayer", "TFTMatch", "TFTParticipant"]
        if not all(entity in context for entity in tft_entities):
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        return False


def validate_jsonld_compliance(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate JSON-LD compliance of TFT data
    
    Args:
        data: TFT data to validate for JSON-LD compliance
        
    Returns:
        tuple: (is_compliant, list_of_issues)
    """
    issues = []
    
    try:
        # Check for @context
        if "@context" not in data:
            issues.append("Missing @context field required for JSON-LD")
        
        # Check for proper IDs
        if "collectionInfo" in data:
            collection_info = data["collectionInfo"]
            if "@id" not in collection_info:
                issues.append("Collection info missing @id field")
        
        # Check namespace usage
        if "@context" in data:
            context = data["@context"]
            required_namespaces = ["tft", "dcterms", "rdf", "rdfs"]
            
            for ns in required_namespaces:
                if ns not in context:
                    issues.append(f"Missing namespace: {ns}")
        
        # Check semantic relationships and types
        if "players" in data:
            for puuid, player_data in data["players"].items():
                if "@type" not in player_data:
                    issues.append(f"Player {puuid} missing @type field")
                elif player_data["@type"] != "TFTPlayer":
                    issues.append(f"Player {puuid} has incorrect @type: {player_data['@type']} (expected TFTPlayer)")
                
                if "@id" not in player_data:
                    issues.append(f"Player {puuid} missing @id field")
        
        # Check match semantic structure
        if "matches" in data:
            for match_id, match_data in data["matches"].items():
                if "@type" not in match_data:
                    issues.append(f"Match {match_id} missing @type field")
                elif match_data["@type"] != "TFTMatch":
                    issues.append(f"Match {match_id} has incorrect @type: {match_data['@type']} (expected TFTMatch)")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        issues.append(f"JSON-LD validation error: {str(e)}")
        return False, issues


def check_schema_completeness(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check completeness of TFT schema definition
    
    Args:
        schema: Schema dictionary to check
        
    Returns:
        dict: Completeness report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "completeness_score": 0.0,
        "required_elements": [],
        "missing_elements": [],
        "optional_elements": [],
        "recommendations": []
    }
    
    try:
        # Required schema elements
        required_elements = [
            "@context",
            "@graph", 
            "TFTDataCollection",
            "TFTPlayer",
            "TFTMatch",
            "TFTParticipant",
            "TFTUnit",
            "TFTTrait"
        ]
        
        # Check presence of required elements
        present_count = 0
        
        if "@context" in schema:
            context = schema["@context"]
            
            for element in required_elements:
                if element in context or element in schema:
                    present_count += 1
                    report["required_elements"].append(element)
                else:
                    report["missing_elements"].append(element)
        
        # Calculate completeness score
        total_required = len(required_elements)
        report["completeness_score"] = (present_count / total_required) * 100 if total_required > 0 else 0
        
        # Check optional elements
        optional_elements = [
            "TFTItem",
            "TFTChampion",
            "TFTSynergy",
            "TFTLeaderboard",
            "TFTRanking"
        ]
        
        if "@context" in schema:
            context = schema["@context"]
            for element in optional_elements:
                if element in context:
                    report["optional_elements"].append(element)
        
        # Generate recommendations
        if report["completeness_score"] < 80:
            report["recommendations"].append("Schema missing critical elements - review implementation")
        
        if len(report["missing_elements"]) > 2:
            report["recommendations"].append("Consider implementing missing schema elements for full compliance")
        
        if len(report["optional_elements"]) < 2:
            report["recommendations"].append("Add optional elements to enhance semantic richness")
        
        logger.info(f"Schema completeness check: {report['completeness_score']:.1f}% complete")
        
        return report
        
    except Exception as e:
        report["missing_elements"].append(f"Schema check error: {str(e)}")
        logger.error(f"Schema completeness check failed: {e}")
        return report


def validate_semantic_relationships(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate semantic relationships in TFT data structure
    
    Args:
        data: TFT data with semantic annotations
        
    Returns:
        dict: Validation report for relationships
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "relationship_validity": True,
        "validated_relationships": [],
        "broken_relationships": [],
        "missing_relationships": [],
        "recommendations": []
    }
    
    try:
        # Check player-match relationships
        if "players" in data and "matches" in data:
            for puuid, player_data in data["players"].items():
                if "matches" in player_data:
                    for match_id in player_data["matches"].keys():
                        if match_id in data["matches"]:
                            report["validated_relationships"].append(f"player:{puuid} -> match:{match_id}")
                        else:
                            report["broken_relationships"].append(f"Player {puuid} references non-existent match {match_id}")
        
        # Check match-participant relationships
        if "matches" in data:
            for match_id, match_data in data["matches"].items():
                if "info" in match_data and "participants" in match_data["info"]:
                    for participant in match_data["info"]["participants"]:
                        if "puuid" in participant:
                            puuid = participant["puuid"]
                            if puuid in data.get("players", {}):
                                report["validated_relationships"].append(f"match:{match_id} -> player:{puuid}")
                            else:
                                report["missing_relationships"].append(f"Match {match_id} participant {puuid} not in player data")
        
        # Determine overall validity
        total_issues = len(report["broken_relationships"]) + len(report["missing_relationships"])
        report["relationship_validity"] = total_issues == 0
        
        # Generate recommendations
        if total_issues > 0:
            report["recommendations"].append("Fix broken or missing relationships for data integrity")
        
        if len(report["validated_relationships"]) < 10:
            report["recommendations"].append("Data may be incomplete - verify collection process")
        
        logger.info(f"Semantic relationship validation: {len(report['validated_relationships'])} valid, {total_issues} issues")
        
        return report
        
    except Exception as e:
        report["broken_relationships"].append(f"Relationship validation error: {str(e)}")
        logger.error(f"Semantic relationship validation failed: {e}")
        return report
