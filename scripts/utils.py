"""
This module contains utility functions for data persistence, file operations,
and other general-purpose functionality used across the TFT data collection system.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# Known special queue IDs that may have <8 participants
SPECIAL_QUEUES = {
    1220: "Special queue (practice/tutorial mode)",
    # Add more as discovered
}


def save_data_to_file(data: Dict[str, Any], filename: Optional[Union[str, Path]] = None, 
                      create_dirs: bool = True) -> Optional[str]:
    """
    Save data dictionary to JSON file with automatic timestamping.
    
    Args:
        data: Dictionary to save as JSON
        filename: Output file path (str or Path). If None, auto-generates timestamped filename
        create_dirs: If True, create parent directories if they don't exist
        
    Returns:
        Path to saved file as string, or None on error
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tft_la2_data_{timestamp}.json"
    
    file_path = Path(filename)
    
    try:
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {e}")
        return None


def load_data_from_file(filename: Union[str, Path], default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Load data dictionary from JSON file.
    
    Args:
        filename: Input file path (str or Path)
        default: Default value to return on error (instead of None)
        
    Returns:
        Loaded dictionary, default value, or None on error
    """
    file_path = Path(filename)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Data loaded from {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error loading {file_path}: {e}")
        return default
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error loading {file_path}: {e}")
        return default
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {e}")
        return default


def identify_incomplete_matches(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify matches with incomplete participant data.
    
    A match is considered incomplete if:
    - It has fewer than 8 participants (unless it's a known special queue)
    - It's a special queue type (even if it has 8 participants, for documentation)
    
    Args:
        data: TFT collection data dictionary with 'matches' key
        
    Returns:
        List of incomplete match dictionaries, each containing:
        - match_id: The match identifier
        - participant_count: Number of participants in the match
        - queue_id: Queue ID of the match
        - game_version: Game version string
        - reasons: List of reasons why the match is considered incomplete
    """
    incomplete = []
    matches = data.get('matches', {})
    
    for match_id, match_data in matches.items():
        if 'info' not in match_data:
            continue
        
        info = match_data['info']
        participants = info.get('participants', [])
        participant_count = len(participants)
        
        # Check if match is incomplete
        is_incomplete = False
        reasons = []
        
        queue_id = info.get('queueId')
        
        # Primary check: participant count < 8 (unless it's a known special queue)
        if participant_count < 8:
            # Only mark as incomplete if it's not a known special queue
            if queue_id not in SPECIAL_QUEUES:
                is_incomplete = True
                reasons.append(f"Only {participant_count} participants (expected 8)")
            else:
                # Special queue with <8 participants is expected
                is_incomplete = True
                reasons.append(f"Special queue {queue_id}: {SPECIAL_QUEUES[queue_id]} (expected <8 participants)")
        
        # Secondary check: special queue (even if it has 8 participants, mark it for documentation)
        if queue_id in SPECIAL_QUEUES and participant_count >= 8:
            # This shouldn't happen, but mark it anyway
            is_incomplete = True
            reasons.append(f"Special queue {queue_id}: {SPECIAL_QUEUES[queue_id]} (unexpected 8 participants)")
        
        if is_incomplete:
            incomplete.append({
                'match_id': match_id,
                'participant_count': participant_count,
                'queue_id': queue_id,
                'game_version': info.get('gameVersion'),
                'reasons': reasons
            })
    
    return incomplete

