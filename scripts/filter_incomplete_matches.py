#!/usr/bin/env python3
"""
Filter Incomplete Matches
=========================

This script filters out or marks incomplete matches (those with <8 participants)
from collected data. Incomplete matches are typically:
- Queue 1220 (special queue types like practice/tutorial)
- Matches with missing gameVersion
- Matches with <8 participants

Usage:
    # Filter out incomplete matches (remove them)
    python3 scripts/filter_incomplete_matches.py data/validated/tft_collection_20251101.json --filter-out
    
    # Mark incomplete matches in metadata (keep them but flag them)
    python3 scripts/filter_incomplete_matches.py data/validated/tft_collection_20251101.json --mark-incomplete
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import identify_incomplete_matches, SPECIAL_QUEUES, load_data_from_file, save_data_to_file

def filter_out_incomplete_matches(data: Dict[str, Any], incomplete_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Remove incomplete matches from data"""
    incomplete_match_ids = {m['match_id'] for m in incomplete_matches}
    
    # Remove from matches
    filtered_matches = {
        match_id: match_data
        for match_id, match_data in data.get('matches', {}).items()
        if match_id not in incomplete_match_ids
    }
    
    data['matches'] = filtered_matches
    
    # Update collectionInfo
    if 'collectionInfo' in data:
        original_count = data['collectionInfo'].get('matches_count', len(data.get('matches', {})))
        data['collectionInfo']['matches_count'] = len(filtered_matches)
        data['collectionInfo']['filtered_matches'] = len(incomplete_match_ids)
        data['collectionInfo']['filter_reason'] = 'Removed incomplete matches (<8 participants or special queues)'
    
    return data

def mark_incomplete_matches(data: Dict[str, Any], incomplete_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Mark incomplete matches in metadata but keep them"""
    incomplete_match_ids = {m['match_id'] for m in incomplete_matches}
    
    # Add metadata to incomplete matches
    for match_id in incomplete_match_ids:
        if match_id in data.get('matches', {}):
            match_data = data['matches'][match_id]
            if 'metadata' not in match_data:
                match_data['metadata'] = {}
            
            match_data['metadata']['is_incomplete'] = True
            match_data['metadata']['incomplete_reason'] = next(
                (m['reasons'] for m in incomplete_matches if m['match_id'] == match_id),
                ['Unknown reason']
            )
    
    # Update collectionInfo
    if 'collectionInfo' in data:
        data['collectionInfo']['incomplete_matches_count'] = len(incomplete_match_ids)
        data['collectionInfo']['incomplete_matches'] = [
            {
                'match_id': m['match_id'],
                'participant_count': m['participant_count'],
                'queue_id': m['queue_id'],
                'reasons': m['reasons']
            }
            for m in incomplete_matches
        ]
    
    return data

def main():
    parser = argparse.ArgumentParser(
        description='Filter or mark incomplete matches in collected TFT data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Filter out incomplete matches (remove them)
  python3 scripts/filter_incomplete_matches.py data/validated/tft_collection_20251101.json --filter-out --output data/filtered/tft_collection_20251101.json
  
  # Mark incomplete matches but keep them
  python3 scripts/filter_incomplete_matches.py data/validated/tft_collection_20251101.json --mark-incomplete --output data/marked/tft_collection_20251101.json
  
  # Just analyze without modifying
  python3 scripts/filter_incomplete_matches.py data/validated/tft_collection_20251101.json
        """
    )
    parser.add_argument('data_file', help='Path to collected data JSON file')
    parser.add_argument('--output', '-o', help='Output file path (default: overwrite input)')
    parser.add_argument('--filter-out', action='store_true', help='Remove incomplete matches from data')
    parser.add_argument('--mark-incomplete', action='store_true', help='Mark incomplete matches in metadata but keep them')
    parser.add_argument('--backup', action='store_true', help='Create backup of original file')
    
    args = parser.parse_args()
    
    data_file = Path(args.data_file)
    if not data_file.exists():
        print(f"[ERROR] File not found: {data_file}", file=sys.stderr)
        sys.exit(1)
    
    output_file = Path(args.output) if args.output else data_file
    
    print(f"Processing: {data_file}")
    print("=" * 70)
    
    # Load data
    data = load_data_from_file(data_file)
    if data is None:
        print(f"[ERROR] Error loading data file: {data_file}", file=sys.stderr)
        sys.exit(1)
    
    # Identify incomplete matches
    print("\nIdentifying incomplete matches...")
    incomplete_matches = identify_incomplete_matches(data)
    
    print(f"\nFound {len(incomplete_matches)} incomplete matches out of {len(data.get('matches', {}))} total")
    
    if incomplete_matches:
        print("\nIncomplete Match Summary:")
        by_queue = {}
        by_participant_count = {}
        
        for match in incomplete_matches:
            queue_id = match.get('queue_id', 'unknown')
            by_queue[queue_id] = by_queue.get(queue_id, 0) + 1
            count = match['participant_count']
            by_participant_count[count] = by_participant_count.get(count, 0) + 1
        
        print("  By Queue ID:")
        for queue_id, count in sorted(by_queue.items()):
            queue_desc = SPECIAL_QUEUES.get(queue_id, "Unknown queue")
            print(f"    Queue {queue_id} ({queue_desc}): {count} matches")
        
        print("  By Participant Count:")
        for count, num_matches in sorted(by_participant_count.items()):
            print(f"    {count} participants: {num_matches} matches")
        
        # Show sample
        print("\n  Sample incomplete matches:")
        for i, match in enumerate(incomplete_matches[:5]):
            print(f"    {i+1}. {match['match_id']}: {', '.join(match['reasons'])}")
        if len(incomplete_matches) > 5:
            print(f"    ... and {len(incomplete_matches) - 5} more")
    
    # Process based on action
    if args.filter_out:
        if not incomplete_matches:
            print("\n[SUCCESS] No incomplete matches to filter out")
        else:
            print(f"\nFiltering out {len(incomplete_matches)} incomplete matches...")
            data = filter_out_incomplete_matches(data, incomplete_matches)
            print(f"[SUCCESS] Removed {len(incomplete_matches)} matches. Remaining: {len(data.get('matches', {}))} matches")
    
    elif args.mark_incomplete:
        if not incomplete_matches:
            print("\n[SUCCESS] No incomplete matches to mark")
        else:
            print(f"\nMarking {len(incomplete_matches)} incomplete matches in metadata...")
            data = mark_incomplete_matches(data, incomplete_matches)
            print(f"[SUCCESS] Marked {len(incomplete_matches)} matches as incomplete")
    
    else:
        print("\n[INFO] No action specified. Use --filter-out or --mark-incomplete to modify data.")
        print("   This was an analysis-only run.")
        return
    
    # Create backup if requested
    if args.backup and not args.output:
        backup_file = data_file.with_suffix('.json.backup')
        import shutil
        shutil.copy(data_file, backup_file)
        print(f"[INFO] Backup created: {backup_file}")
    
    # Save output
    saved_path = save_data_to_file(data, output_file, create_dirs=True)
    if saved_path:
        print(f"\n[INFO] Saved to: {saved_path}")
    else:
        print(f"\n[ERROR] Error saving to: {output_file}", file=sys.stderr)
        sys.exit(1)
    print("=" * 70)
    print("[SUCCESS] Processing complete")
    print("=" * 70)

if __name__ == "__main__":
    main()

