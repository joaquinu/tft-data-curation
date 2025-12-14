#!/usr/bin/env python3
"""
Convert JSON-LD TFT collection data to optimized Parquet format.
Creates two tables:
1. matches.parquet: Match-level metadata
2. participants.parquet: Participant-level performance data
"""

import json
import argparse
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_match_data(match_id: str, match_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract flat match-level data."""
    info = match_data.get("info", {})
    metadata = match_data.get("metadata", {})
    
    return {
        "match_id": match_id,
        "data_version": metadata.get("data_version"),
        "tft_set_number": info.get("tft_set_number"),
        "game_datetime": pd.to_datetime(info.get("game_datetime"), unit='ms'),
        "game_length": info.get("game_length"),
        "game_version": info.get("game_version"),
        "queue_id": info.get("queue_id"),
        "tft_game_type": info.get("tft_game_type"),
        "end_of_game_result": info.get("endOfGameResult"),
        "creation_date": pd.Timestamp.now()
    }

def extract_participant_data(match_id: str, participant: Dict[str, Any]) -> Dict[str, Any]:
    """Extract flat participant-level data."""
    return {
        "match_id": match_id,
        "puuid": participant.get("puuid"),
        "placement": participant.get("placement"),
        "level": participant.get("level"),
        "gold_left": participant.get("gold_left"),
        "last_round": participant.get("last_round"),
        "time_eliminated": participant.get("time_eliminated"),
        "total_damage_to_players": participant.get("total_damage_to_players"),
        "players_eliminated": participant.get("players_eliminated"),
        "partner_group_id": participant.get("partner_group_id"),
        # Store complex types as JSON strings for compatibility
        "traits": json.dumps(participant.get("traits", [])),
        "units": json.dumps(participant.get("units", [])),
        "augments": json.dumps(participant.get("augments", [])),
        "companion": json.dumps(participant.get("companion", {}))
    }

def convert_to_parquet(input_file: Path, output_dir: Path):
    """Convert JSON-LD file to Parquet tables.
    
    Supports two data formats:
    1. JSON-LD format: matches at top level (data["matches"])
    2. Player-centric format: matches within player objects (data[player]["matches"])
    """
    logger.info(f"Loading {input_file}...")
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON: {e}")
        raise
    
    if not isinstance(data, dict):
        raise ValueError(f"Expected dictionary, got {type(data)}")

    unique_matches = {}
    
    # Handle JSON-LD structure: matches can be at top level or within players
    logger.info("Processing data and deduplicating matches...")
    logger.debug(f"Top-level keys in data: {list(data.keys())[:10]}")
    
    # Check if matches are at top level (JSON-LD transformed format)
    if "matches" in data:
        matches_data = data["matches"]
        if isinstance(matches_data, dict):
            logger.info(f"Found matches at top level (JSON-LD format): {len(matches_data)} matches")
            unique_matches = matches_data
        elif isinstance(matches_data, list):
            logger.info(f"Found matches as list at top level: {len(matches_data)} matches")
            # Convert list to dict using match_id or index
            for idx, match_data in enumerate(matches_data):
                match_id = match_data.get("metadata", {}).get("match_id") or match_data.get("@id") or f"match_{idx}"
                unique_matches[match_id] = match_data
        else:
            logger.warning(f"Matches key exists but has unexpected type: {type(matches_data)}")
    
    # Fallback: check if data is player-centric (old format)
    if len(unique_matches) == 0 and isinstance(data, dict):
        logger.info("No top-level matches found, checking player-centric format...")
        for player_puuid, player_data in data.items():
            if not isinstance(player_data, dict):
                continue
            
            # Check for matches in player data
            if "matches" in player_data:
                matches_in_player = player_data["matches"]
                if isinstance(matches_in_player, dict):
                    for match_id, match_data in matches_in_player.items():
                        if match_id not in unique_matches:
                            unique_matches[match_id] = match_data
                elif isinstance(matches_in_player, list):
                    for match_data in matches_in_player:
                        match_id = match_data.get("metadata", {}).get("match_id") or match_data.get("@id") or f"match_{len(unique_matches)}"
                        if match_id not in unique_matches:
                            unique_matches[match_id] = match_data
            # Also check if player_data itself is a match (edge case)
            elif "@type" in player_data and player_data.get("@type") == "TFTMatch":
                match_id = player_data.get("@id", player_puuid)
                if match_id not in unique_matches:
                    unique_matches[match_id] = player_data

    logger.info(f"Found {len(unique_matches)} unique matches")
    
    if len(unique_matches) == 0:
        logger.error("No matches found in data. Checking data structure...")
        logger.error(f"Top-level keys: {list(data.keys())[:10]}")
        if "matches" in data:
            logger.error(f"Matches key exists but is empty or wrong type: {type(data['matches'])}")
            if isinstance(data["matches"], dict):
                logger.error(f"Matches dict is empty: {len(data['matches'])} entries")
            elif isinstance(data["matches"], list):
                logger.error(f"Matches list is empty: {len(data['matches'])} entries")
        # Check for players structure
        if "players" in data:
            logger.error(f"Found 'players' key with {len(data['players'])} players")
            # Sample first player structure
            if data["players"]:
                first_player = next(iter(data["players"].values()))
                logger.error(f"First player keys: {list(first_player.keys())[:10]}")
        raise ValueError("No matches found in data. Please check the input file structure.")

    matches_list = []
    participants_list = []

    logger.info("Extracting relational data...")
    for match_id, match_data in unique_matches.items():
        # 1. Extract Match Data
        matches_list.append(extract_match_data(match_id, match_data))
        
        # 2. Extract Participant Data
        info = match_data.get("info", {})
        for participant in info.get("participants", []):
            participants_list.append(extract_participant_data(match_id, participant))

    # Create Output Directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save Matches
    if matches_list:
        df_matches = pd.DataFrame(matches_list)
        matches_path = output_dir / "matches.parquet"
        df_matches.to_parquet(matches_path, index=False, compression='snappy')
        logger.info(f"Saved {len(df_matches)} matches to {matches_path}")

    # Save Participants
    if participants_list:
        df_participants = pd.DataFrame(participants_list)
        participants_path = output_dir / "participants.parquet"
        df_participants.to_parquet(participants_path, index=False, compression='snappy')
        logger.info(f"Saved {len(df_participants)} participants to {participants_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert TFT JSON-LD to Parquet")
    parser.add_argument("--input", required=True, help="Input JSON-LD file")
    parser.add_argument("--output", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    convert_to_parquet(Path(args.input), Path(args.output))

if __name__ == "__main__":
    main()
