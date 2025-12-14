#!/usr/bin/env python3
"""
Transforms validated JSON data into JSON-LD format with proper @type annotations
and semantic context.
"""

import json
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.schema import TFTSchemaGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def transform_to_jsonld(input_file: Path, output_file: Path) -> None:
    """
    Transform validated JSON data to JSON-LD format.
    """
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
            
        logger.info(f"Loaded {len(data) if isinstance(data, list) else 1} records from {input_file}")
        
        generator = TFTSchemaGenerator()
        context = generator.get_schema_context()
        
        jsonld_data = {
            "@context": context,
            "@type": "TFTDataCollection",
            "collectionInfo": data.get("collectionInfo", {}),
            "players": {},
            "matches": {}
        }
        
        if "collectionInfo" in jsonld_data:
            timestamp = jsonld_data["collectionInfo"].get("timestamp", "")
            region = jsonld_data["collectionInfo"].get("extractionLocation", "unknown")
            jsonld_data["collectionInfo"]["@id"] = f"urn:tft:collection:{region}:{timestamp}"
        
        if "players" in data:
            for puuid, player_data in data["players"].items():
                transformed_player = player_data.copy()
                transformed_player["@type"] = "TFTPlayer"
                transformed_player["@id"] = f"urn:tft:player:{puuid}"
                jsonld_data["players"][puuid] = transformed_player
                
        if "matches" in data:
            for match_id, match_data in data["matches"].items():
                transformed_match = match_data.copy()
                transformed_match["@type"] = "TFTMatch"
                transformed_match["@id"] = f"urn:tft:match:{match_id}"
                
                if "info" in transformed_match and "participants" in transformed_match["info"]:
                    participants = []
                    for p in transformed_match["info"]["participants"]:
                        p_copy = p.copy()
                        p_copy["@type"] = "TFTParticipant"
                        if "puuid" in p_copy:
                            p_copy["@id"] = f"urn:tft:participant:{match_id}:{p_copy['puuid']}"
                        participants.append(p_copy)
                    transformed_match["info"]["participants"] = participants
                    
                jsonld_data["matches"][match_id] = transformed_match
                
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(jsonld_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Successfully transformed data to JSON-LD at {output_file}")
        
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Transform validated JSON to JSON-LD")
    parser.add_argument("input_file", type=Path, help="Input validated JSON file")
    parser.add_argument("output_file", type=Path, help="Output JSON-LD file")
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
        
    try:
        transform_to_jsonld(args.input_file, args.output_file)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
