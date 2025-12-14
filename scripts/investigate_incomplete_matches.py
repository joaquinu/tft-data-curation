#!/usr/bin/env python3
"""
Investigate Incomplete Matches
==============================

This script analyzes matches with incomplete participant data to determine:
1. Why some matches have only 1 participant (expected 8)
2. Whether this is an API issue or data processing issue
3. Patterns in incomplete matches (timestamps, regions, etc.)

Usage:
    python3 scripts/investigate_incomplete_matches.py data/validated/tft_collection_20251101.json
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import identify_incomplete_matches, load_data_from_file, save_data_to_file

def analyze_match_participants(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze participant counts across all matches"""
    matches = data.get('matches', {})
    
    participant_counts = defaultdict(int)
    incomplete_matches = []
    complete_matches = []
    
    # Use shared function to identify incomplete matches
    incomplete_matches_list = identify_incomplete_matches(data)
    incomplete_match_ids = {m['match_id'] for m in incomplete_matches_list}
    
    for match_id, match_data in matches.items():
        if 'info' not in match_data:
            continue
            
        info = match_data['info']
        participants = info.get('participants', [])
        participant_count = len(participants)
        
        participant_counts[participant_count] += 1
        
        match_info = {
            'match_id': match_id,
            'participant_count': participant_count,
            'has_info': 'info' in match_data,
            'has_metadata': 'metadata' in match_data,
            'game_datetime': info.get('game_datetime'),
            'game_length': info.get('game_length'),
            'queue_id': info.get('queueId'),
            'game_version': info.get('gameVersion'),
            'participants': participants
        }
        
        if match_id in incomplete_match_ids:
            incomplete_matches.append(match_info)
        else:
            complete_matches.append(match_info)
    
    return {
        'total_matches': len(matches),
        'complete_matches': len(complete_matches),
        'incomplete_matches': len(incomplete_matches),
        'participant_count_distribution': dict(participant_counts),
        'incomplete_match_details': incomplete_matches,
        'sample_complete_match': complete_matches[0] if complete_matches else None
    }

def analyze_incomplete_match_patterns(incomplete_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in incomplete matches"""
    patterns = {
        'by_participant_count': defaultdict(int),
        'by_queue_id': defaultdict(int),
        'by_game_version': defaultdict(int),
        'timestamp_ranges': [],
        'game_length_stats': [],
        'participant_data_quality': {
            'has_puuid': 0,
            'has_placement': 0,
            'has_units': 0,
            'has_traits': 0,
            'has_level': 0
        }
    }
    
    for match in incomplete_matches:
        count = match['participant_count']
        patterns['by_participant_count'][count] += 1
        patterns['by_queue_id'][match.get('queue_id')] += 1
        patterns['by_game_version'][match.get('game_version')] += 1
        
        if match.get('game_datetime'):
            patterns['timestamp_ranges'].append(match['game_datetime'])
        
        if match.get('game_length'):
            patterns['game_length_stats'].append(match['game_length'])
        
        # Analyze participant data quality
        for participant in match.get('participants', []):
            if 'puuid' in participant:
                patterns['participant_data_quality']['has_puuid'] += 1
            if 'placement' in participant:
                patterns['participant_data_quality']['has_placement'] += 1
            if 'units' in participant:
                patterns['participant_data_quality']['has_units'] += 1
            if 'traits' in participant:
                patterns['participant_data_quality']['has_traits'] += 1
            if 'level' in participant:
                patterns['participant_data_quality']['has_level'] += 1
    
    # Calculate statistics
    if patterns['timestamp_ranges']:
        patterns['timestamp_stats'] = {
            'min': min(patterns['timestamp_ranges']),
            'max': max(patterns['timestamp_ranges']),
            'count': len(patterns['timestamp_ranges'])
        }
    else:
        patterns['timestamp_stats'] = None
    
    if patterns['game_length_stats']:
        patterns['game_length_analysis'] = {
            'min': min(patterns['game_length_stats']),
            'max': max(patterns['game_length_stats']),
            'avg': sum(patterns['game_length_stats']) / len(patterns['game_length_stats']),
            'count': len(patterns['game_length_stats'])
        }
    else:
        patterns['game_length_analysis'] = None
    
    return patterns

def compare_with_complete_matches(incomplete_matches: List[Dict[str, Any]], 
                                  complete_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare incomplete matches with complete matches to find differences"""
    comparison = {
        'queue_id_differences': {},
        'game_version_differences': {},
        'timestamp_differences': {},
        'game_length_differences': {}
    }
    
    # Analyze queue IDs
    incomplete_queues = defaultdict(int)
    complete_queues = defaultdict(int)
    
    for match in incomplete_matches:
        queue_id = match.get('queue_id')
        if queue_id:
            incomplete_queues[queue_id] += 1
    
    for match in complete_matches[:100]:  # Sample of complete matches
        queue_id = match.get('queue_id')
        if queue_id:
            complete_queues[queue_id] += 1
    
    comparison['queue_id_differences'] = {
        'incomplete': dict(incomplete_queues),
        'complete': dict(complete_queues)
    }
    
    # Analyze game versions
    incomplete_versions = defaultdict(int)
    complete_versions = defaultdict(int)
    
    for match in incomplete_matches:
        version = match.get('game_version')
        if version:
            incomplete_versions[version] += 1
    
    for match in complete_matches[:100]:
        version = match.get('game_version')
        if version:
            complete_versions[version] += 1
    
    comparison['game_version_differences'] = {
        'incomplete': dict(incomplete_versions),
        'complete': dict(complete_versions)
    }
    
    return comparison

def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on analysis"""
    recommendations = []
    
    incomplete_count = analysis['incomplete_matches']
    total_count = analysis['total_matches']
    incomplete_percentage = (incomplete_count / total_count * 100) if total_count > 0 else 0
    
    # Check if this is a significant issue
    if incomplete_percentage > 5:
        recommendations.append(
            f"[WARNING] High percentage of incomplete matches: {incomplete_percentage:.1f}% "
            f"({incomplete_count}/{total_count})"
        )
    
    # Check participant count distribution
    dist = analysis['participant_count_distribution']
    if 1 in dist and dist[1] > 0:
        recommendations.append(
            f"[INFO] {dist[1]} matches have only 1 participant - investigate API response structure"
        )
    
    # Check patterns
    patterns = analysis.get('patterns', {})
    if patterns:
        by_count = patterns.get('by_participant_count', {})
        if 1 in by_count:
            recommendations.append(
                f"[INFO] {by_count[1]} matches with exactly 1 participant - "
                "likely API returning incomplete data or abandoned matches"
            )
        
        # Check if there are patterns by queue ID
        by_queue = patterns.get('by_queue_id', {})
        if len(by_queue) > 1:
            recommendations.append(
                f"🎮 Incomplete matches span multiple queue types: {list(by_queue.keys())}"
            )
    
    # Data quality recommendations
    participant_quality = patterns.get('participant_data_quality', {})
    if participant_quality.get('has_puuid', 0) < incomplete_count:
        recommendations.append(
            "[WARNING] Some incomplete matches have participants without PUUIDs - "
            "this may indicate API data corruption"
        )
    
    return recommendations

def main():
    parser = argparse.ArgumentParser(
        description='Investigate incomplete matches in collected TFT data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single collection file
  python3 scripts/investigate_incomplete_matches.py data/validated/tft_collection_20251101.json
  
  # Save detailed report to file
  python3 scripts/investigate_incomplete_matches.py data/validated/tft_collection_20251101.json --output report.json
        """
    )
    parser.add_argument('data_file', help='Path to collected data JSON file')
    parser.add_argument('--output', '-o', help='Save detailed report to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed match information')
    parser.add_argument('--sample-size', type=int, default=5, help='Number of sample matches to show (default: 5)')
    
    args = parser.parse_args()
    
    data_file = Path(args.data_file)
    if not data_file.exists():
        print(f"[ERROR] File not found: {data_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing matches in: {data_file}")
    print("=" * 70)
    
    # Load data
    data = load_data_from_file(data_file)
    if data is None:
        print(f"[ERROR] Error loading data file: {data_file}", file=sys.stderr)
        sys.exit(1)
    
    # Analyze matches
    print("\nAnalyzing participant counts...")
    analysis = analyze_match_participants(data)
    
    # Analyze patterns in incomplete matches
    incomplete_matches_list = analysis['incomplete_match_details']
    if incomplete_matches_list:
        print(f"\nAnalyzing {len(incomplete_matches_list)} incomplete matches...")
        patterns = analyze_incomplete_match_patterns(incomplete_matches_list)
        analysis['patterns'] = patterns
        
        # Compare with complete matches
        complete_matches_list = [m for m in analysis.get('complete_match_details', [])]
        if not complete_matches_list and analysis['complete_matches'] > 0:
            # Need to rebuild complete matches list
            matches = data.get('matches', {})
            complete_matches_list = []
            for match_id, match_data in matches.items():
                if 'info' in match_data:
                    info = match_data['info']
                    participants = info.get('participants', [])
                    if len(participants) == 8:
                        complete_matches_list.append({
                            'match_id': match_id,
                            'participant_count': 8,
                            'queue_id': info.get('queueId'),
                            'game_version': info.get('gameVersion'),
                            'game_datetime': info.get('game_datetime'),
                            'game_length': info.get('game_length')
                        })
                        if len(complete_matches_list) >= 100:  # Sample size
                            break
        
        if complete_matches_list:
            comparison = compare_with_complete_matches(
                incomplete_matches_list,
                complete_matches_list
            )
            analysis['comparison'] = comparison
    
    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Total Matches: {analysis['total_matches']}")
    print(f"Complete Matches (8 participants): {analysis['complete_matches']}")
    print(f"Incomplete Matches (<8 participants): {analysis['incomplete_matches']}")
    
    if analysis['incomplete_matches'] > 0:
        incomplete_pct = (analysis['incomplete_matches'] / analysis['total_matches'] * 100)
        print(f"Incomplete Percentage: {incomplete_pct:.2f}%")
    
    print("\nParticipant Count Distribution:")
    for count in sorted(analysis['participant_count_distribution'].keys()):
        num_matches = analysis['participant_count_distribution'][count]
        pct = (num_matches / analysis['total_matches'] * 100) if analysis['total_matches'] > 0 else 0
        print(f"  {count} participants: {num_matches} matches ({pct:.2f}%)")
    
    # Show patterns if available
    if 'patterns' in analysis:
        patterns = analysis['patterns']
        print("\nPatterns in Incomplete Matches:")
        
        if patterns.get('by_participant_count'):
            print("  By Participant Count:")
            for count in sorted(patterns['by_participant_count'].keys()):
                print(f"    {count} participants: {patterns['by_participant_count'][count]} matches")
        
        if patterns.get('by_queue_id'):
            print("  By Queue ID:")
            for queue_id, count in patterns['by_queue_id'].items():
                print(f"    Queue {queue_id}: {count} matches")
        
        if patterns.get('by_game_version'):
            print("  By Game Version:")
            for version, count in list(patterns['by_game_version'].items())[:5]:
                print(f"    {version}: {count} matches")
            if len(patterns['by_game_version']) > 5:
                print(f"    ... and {len(patterns['by_game_version']) - 5} more versions")
        
        if patterns.get('game_length_analysis'):
            gl = patterns['game_length_analysis']
            print(f"  Game Length Stats:")
            print(f"    Average: {gl['avg']:.2f} seconds")
            print(f"    Range: {gl['min']:.2f} - {gl['max']:.2f} seconds")
        
        if patterns.get('participant_data_quality'):
            pq = patterns['participant_data_quality']
            print(f"  Participant Data Quality (for incomplete matches):")
            print(f"    Has PUUID: {pq['has_puuid']} participants")
            print(f"    Has Placement: {pq['has_placement']} participants")
            print(f"    Has Units: {pq['has_units']} participants")
            print(f"    Has Traits: {pq['has_traits']} participants")
            print(f"    Has Level: {pq['has_level']} participants")
    
    # Show sample incomplete matches
    incomplete_matches_list = analysis.get('incomplete_match_details', [])
    if args.verbose and incomplete_matches_list:
        print(f"\nSample Incomplete Matches (showing {min(args.sample_size, len(incomplete_matches_list))}):")
        for i, match in enumerate(incomplete_matches_list[:args.sample_size]):
            print(f"\n  Match {i+1}: {match['match_id']}")
            print(f"    Participants: {match['participant_count']}")
            print(f"    Queue ID: {match.get('queue_id', 'N/A')}")
            print(f"    Game Version: {match.get('game_version', 'N/A')}")
            print(f"    Game DateTime: {match.get('game_datetime', 'N/A')}")
            print(f"    Game Length: {match.get('game_length', 'N/A')} seconds")
            if match.get('participants'):
                participant = match['participants'][0]
                print(f"    Sample Participant:")
                print(f"      PUUID: {participant.get('puuid', 'N/A')[:16]}...")
                print(f"      Placement: {participant.get('placement', 'N/A')}")
                print(f"      Level: {participant.get('level', 'N/A')}")
                print(f"      Has Units: {bool(participant.get('units'))}")
                print(f"      Has Traits: {bool(participant.get('traits'))}")
    
    # Generate recommendations
    recommendations = generate_recommendations(analysis)
    if recommendations:
        print("\nRECOMMENDATIONS:")
        print("=" * 70)
        for rec in recommendations:
            print(f"  {rec}")
    
    # Save detailed report if requested
    if args.output:
        saved_path = save_data_to_file(analysis, args.output, create_dirs=True)
        if saved_path:
            print(f"\n[INFO] Detailed report saved to: {saved_path}")
        else:
            print(f"\n[ERROR] Error saving report to: {args.output}", file=sys.stderr)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Analysis complete")
    print("=" * 70)

if __name__ == "__main__":
    main()

