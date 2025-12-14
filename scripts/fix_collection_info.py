#!/usr/bin/env python3
"""
Fix Missing collectionInfo in Collected Data Files
==================================================

This script adds the missing `collectionInfo` field to existing collected data files
that were created before the fix was implemented.

Usage:
    python3 scripts/fix_collection_info.py data/raw/tft_collection_20251101.json
    python3 scripts/fix_collection_info.py data/raw/*.json
    python3 scripts/fix_collection_info.py --directory data/raw
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import load_data_from_file, save_data_to_file

def extract_date_from_filename(filename: str) -> Optional[str]:
    """Extract date string from filename like tft_collection_20251101_*.json"""
    try:
        # Pattern: tft_collection_YYYYMMDD_*.json
        parts = Path(filename).stem.split('_')
        if len(parts) >= 3 and parts[0] == 'tft' and parts[1] == 'collection':
            date_str = parts[2]
            if len(date_str) == 8 and date_str.isdigit():
                return date_str
    except:
        pass
    return None

def create_collection_info(data: Dict[str, Any], date_str: Optional[str] = None) -> Dict[str, Any]:
    """Create collectionInfo structure from existing data"""
    matches_count = len(data.get('matches', {}))
    players_count = len(data.get('players', {}))
    
    # Try to extract timestamp from data
    timestamp = data.get('extractionTimestamp') or data.get('timestamp')
    if isinstance(timestamp, str):
        try:
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            dt = datetime.now()
    else:
        dt = datetime.now()
    
    # Extract date from filename if not provided
    if not date_str:
        date_str = dt.strftime('%Y%m%d')
    
    collection_info = {
        "@type": "CollectionInfo",
        "@id": f"collection:{dt.isoformat()}",
        'timestamp': dt.isoformat(),
        'extractionLocation': data.get('extractionLocation', 'LA2'),
        'dataVersion': data.get('dataVersion', '1.0.0'),
        'collection_type': 'date_mode',
        'collection_date': date_str,
        'players_count': players_count,
        'matches_count': matches_count,
    }
    
    # Add collection stats if available
    if 'collection_stats' in data:
        stats = data['collection_stats']
        collection_info['collection_duration_seconds'] = stats.get('collection_time_seconds', 0)
        collection_info['total_match_ids_collected'] = stats.get('total_match_ids_collected', 0)
        collection_info['unique_matches'] = stats.get('unique_matches_fetched', matches_count)
        collection_info['api_calls_saved'] = stats.get('api_calls_saved', 0)
    
    # Add time range if available in collection_config
    if 'collection_config' in data:
        config = data['collection_config']
        if 'start_time' in config:
            collection_info['start_time'] = config['start_time']
        if 'end_time' in config:
            collection_info['end_time'] = config['end_time']
    
    return collection_info

def fix_file(file_path: Path, backup: bool = True) -> bool:
    """Fix a single data file by adding collectionInfo"""
    try:
        print(f"Processing: {file_path}")
        
        # Read existing data
        data = load_data_from_file(file_path)
        if data is None:
            print(f"  [ERROR] Error reading file: {file_path}", file=sys.stderr)
            return False
        
        # Check if collectionInfo already exists
        if 'collectionInfo' in data:
            print(f"  [WARNING] collectionInfo already exists, skipping")
            return False
        
        # Create backup if requested
        if backup:
            backup_path = file_path.with_suffix('.json.backup')
            if not backup_path.exists():
                import shutil
                shutil.copy(file_path, backup_path)
                print(f"  [INFO] Backup created: {backup_path}")
        
        # Extract date from filename
        date_str = extract_date_from_filename(file_path.name)
        
        # Create and add collectionInfo
        collection_info = create_collection_info(data, date_str)
        data['collectionInfo'] = collection_info
        
        # Write fixed data
        saved_path = save_data_to_file(data, file_path, create_dirs=False)
        if saved_path is None:
            print(f"  [ERROR] Error writing file: {file_path}", file=sys.stderr)
            return False
        
        print(f"  [SUCCESS] Added collectionInfo: {collection_info['collection_date']} ({collection_info['matches_count']} matches, {collection_info['players_count']} players)")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error processing {file_path}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Fix missing collectionInfo in collected data files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fix a single file
  python3 scripts/fix_collection_info.py data/raw/tft_collection_20251101.json
  
  # Fix all files in a directory
  python3 scripts/fix_collection_info.py --directory data/raw
  
  # Fix multiple files (no backup)
  python3 scripts/fix_collection_info.py --no-backup data/raw/*.json
        """
    )
    parser.add_argument('files', nargs='*', help='Data files to fix')
    parser.add_argument('--directory', '-d', help='Directory containing files to fix')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup files')
    parser.add_argument('--pattern', default='tft_collection_*.json', help='File pattern to match (default: tft_collection_*.json)')
    
    args = parser.parse_args()
    
    files_to_process = []
    
    # Collect files from arguments
    if args.files:
        for file_pattern in args.files:
            files_to_process.extend(Path('.').glob(file_pattern))
    
    # Collect files from directory
    if args.directory:
        dir_path = Path(args.directory)
        if dir_path.is_dir():
            files_to_process.extend(dir_path.glob(args.pattern))
        else:
            print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
            sys.exit(1)
    
    if not files_to_process:
        print("No files to process. Use --help for usage information.", file=sys.stderr)
        sys.exit(1)
    
    # Remove duplicates and sort
    files_to_process = sorted(set(files_to_process))
    
    print(f"Found {len(files_to_process)} file(s) to process\n")
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in files_to_process:
        if not file_path.is_file():
            continue
        
        success = fix_file(file_path, backup=not args.no_backup)
        if success:
            fixed_count += 1
        else:
            # Check if collectionInfo exists without modifying file
            check_data = load_data_from_file(file_path)
            if check_data and 'collectionInfo' in check_data:
                skipped_count += 1
            else:
                error_count += 1
        print()
    
    print("=" * 60)
    print(f"Summary: {fixed_count} fixed, {skipped_count} skipped, {error_count} errors")
    print("=" * 60)
    
    if fixed_count > 0:
        print("\n[SUCCESS] Files fixed successfully!")
        print("   You can now re-run validation:")
        print("   snakemake --cores 8 --config collection_date=20251101")

if __name__ == "__main__":
    main()

