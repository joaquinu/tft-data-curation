#!/usr/bin/env python3
"""
Research Analysis Script for TFT Data
Answers the research questions from the project proposal:
1. How do champion and item meta-games evolve over time?
2. What factors contribute to successful team compositions?
3. How do player strategies adapt to game updates and balance changes?
"""

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

def load_collection(filepath):
    """Load a collection JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not load {filepath.name}: {e}")
        return {'players': {}}

def extract_matches_from_collection(data):
    """Extract all matches from a collection."""
    matches = []
    if 'players' in data:
        for player_id, player_data in data['players'].items():
            if 'matches' in player_data and player_data['matches']:
                for match_id, match_data in player_data['matches'].items():
                    if match_data and 'info' in match_data:
                        matches.append(match_data)
    return matches

def analyze_unit_meta(matches, collection_date):
    """Analyze champion/unit usage and performance."""
    unit_placements = defaultdict(list)  # unit -> list of placements
    unit_counts = Counter()
    
    for match in matches:
        if 'info' not in match or 'participants' not in match['info']:
            continue
        for participant in match['info']['participants']:
            placement = participant.get('placement', 8)
            units = participant.get('units', [])
            for unit in units:
                unit_id = unit.get('character_id', 'Unknown')
                unit_placements[unit_id].append(placement)
                unit_counts[unit_id] += 1
    
    # Calculate average placement per unit (lower is better)
    unit_performance = {}
    for unit_id, placements in unit_placements.items():
        if len(placements) >= 10:  # Minimum sample size
            avg_placement = sum(placements) / len(placements)
            unit_performance[unit_id] = {
                'avg_placement': round(avg_placement, 2),
                'pick_count': unit_counts[unit_id],
                'win_rate': round(sum(1 for p in placements if p <= 4) / len(placements) * 100, 1)
            }
    
    return unit_performance, unit_counts

def analyze_trait_synergies(matches):
    """Analyze which traits contribute to wins."""
    trait_placements = defaultdict(list)
    trait_combinations = defaultdict(list)
    
    for match in matches:
        if 'info' not in match or 'participants' not in match['info']:
            continue
        for participant in match['info']['participants']:
            placement = participant.get('placement', 8)
            traits = participant.get('traits', [])
            
            active_traits = []
            for trait in traits:
                if trait.get('tier_current', 0) > 0:
                    trait_name = trait.get('name', 'Unknown')
                    trait_placements[trait_name].append(placement)
                    active_traits.append(trait_name)
            
            # Track trait combinations for top 4
            if placement <= 4 and len(active_traits) >= 2:
                combo_key = tuple(sorted(active_traits[:3]))  # Top 3 traits
                trait_combinations[combo_key].append(placement)
    
    # Calculate trait performance
    trait_performance = {}
    for trait, placements in trait_placements.items():
        if len(placements) >= 20:
            trait_performance[trait] = {
                'avg_placement': round(sum(placements) / len(placements), 2),
                'pick_count': len(placements),
                'top4_rate': round(sum(1 for p in placements if p <= 4) / len(placements) * 100, 1)
            }
    
    return trait_performance, trait_combinations

def analyze_augments(matches):
    """Analyze augment usage and effectiveness."""
    augment_placements = defaultdict(list)
    
    for match in matches:
        if 'info' not in match or 'participants' not in match['info']:
            continue
        for participant in match['info']['participants']:
            placement = participant.get('placement', 8)
            augments = participant.get('augments', [])
            
            for augment in augments:
                augment_placements[augment].append(placement)
    
    augment_performance = {}
    for augment, placements in augment_placements.items():
        if len(placements) >= 10:
            augment_performance[augment] = {
                'avg_placement': round(sum(placements) / len(placements), 2),
                'pick_count': len(placements),
                'win_rate': round(sum(1 for p in placements if p <= 4) / len(placements) * 100, 1)
            }
    
    return augment_performance

def analyze_items(matches):
    """Analyze item usage patterns."""
    item_placements = defaultdict(list)
    
    for match in matches:
        if 'info' not in match or 'participants' not in match['info']:
            continue
        for participant in match['info']['participants']:
            placement = participant.get('placement', 8)
            units = participant.get('units', [])
            
            for unit in units:
                items = unit.get('itemNames', []) or unit.get('items', [])
                for item in items:
                    if isinstance(item, str):
                        item_placements[item].append(placement)
                    elif isinstance(item, int):
                        item_placements[f"Item_{item}"].append(placement)
    
    item_performance = {}
    for item, placements in item_placements.items():
        if len(placements) >= 10:
            item_performance[item] = {
                'avg_placement': round(sum(placements) / len(placements), 2),
                'usage_count': len(placements),
                'win_rate': round(sum(1 for p in placements if p <= 4) / len(placements) * 100, 1)
            }
    
    return item_performance

def analyze_game_versions(matches):
    """Track game versions across matches."""
    versions = Counter()
    for match in matches:
        if 'info' in match:
            version = match['info'].get('game_version', 'Unknown')
            # Extract patch version (e.g., "15.22" from full string)
            if 'Version' in version:
                try:
                    patch = version.split('Version ')[1].split('.')[0:2]
                    versions['.'.join(patch)] += 1
                except:
                    versions['Unknown'] += 1
    return versions

def main():
    """Main analysis function."""
    data_dir = Path('/Users/jugarte/Documents/tft-data-extraction/data/raw')
    
    # Find all collection files
    collection_files = sorted(data_dir.glob('tft_collection_*.json'))
    
    print("=" * 80)
    print("TFT DATA ANALYSIS - RESEARCH QUESTIONS")
    print("=" * 80)
    
    all_matches = []
    collection_stats = {}
    
    for filepath in collection_files:
        if 'backup' in str(filepath):
            continue
        date_str = filepath.stem.split('_')[2][:8]  # Extract YYYYMMDD
        print(f"\nLoading {filepath.name}...")
        
        data = load_collection(filepath)
        matches = extract_matches_from_collection(data)
        
        collection_stats[date_str] = {
            'match_count': len(matches),
            'player_count': len(data.get('players', {}))
        }
        all_matches.extend(matches)
        print(f"  Found {len(matches)} matches from {len(data.get('players', {}))} players")
    
    # Deduplicate matches by match_id
    unique_matches = {}
    for match in all_matches:
        if 'metadata' in match and 'match_id' in match['metadata']:
            unique_matches[match['metadata']['match_id']] = match
    all_matches = list(unique_matches.values())
    
    print(f"\n{'=' * 80}")
    print(f"TOTAL: {len(all_matches)} unique matches across {len(collection_stats)} collections")
    print(f"{'=' * 80}")
    
    # ================================================================
    # RESEARCH QUESTION 1: Champion and Item Meta-Game Evolution
    # ================================================================
    print("\n" + "=" * 80)
    print("RESEARCH QUESTION 1: How do champion and item meta-games evolve over time?")
    print("=" * 80)
    
    unit_perf, unit_counts = analyze_unit_meta(all_matches, "all")
    
    # Top 15 most picked champions
    print("\n>> TOP 15 MOST PICKED CHAMPIONS:")
    print("-" * 60)
    top_units = sorted(unit_perf.items(), key=lambda x: x[1]['pick_count'], reverse=True)[:15]
    print(f"{'Champion':<30} {'Picks':>8} {'Avg Place':>10} {'Top 4%':>8}")
    print("-" * 60)
    for unit_id, stats in top_units:
        name = unit_id.replace('TFT13_', '').replace('TFT12_', '')
        print(f"{name:<30} {stats['pick_count']:>8} {stats['avg_placement']:>10} {stats['win_rate']:>7}%")
    
    # Top 15 best performing champions (by avg placement)
    print("\n>> TOP 15 BEST PERFORMING CHAMPIONS (by avg placement):")
    print("-" * 60)
    top_performers = sorted(unit_perf.items(), key=lambda x: x[1]['avg_placement'])[:15]
    print(f"{'Champion':<30} {'Picks':>8} {'Avg Place':>10} {'Top 4%':>8}")
    print("-" * 60)
    for unit_id, stats in top_performers:
        name = unit_id.replace('TFT13_', '').replace('TFT12_', '')
        print(f"{name:<30} {stats['pick_count']:>8} {stats['avg_placement']:>10} {stats['win_rate']:>7}%")
    
    # Item analysis
    item_perf = analyze_items(all_matches)
    print("\n>> TOP 15 MOST USED ITEMS:")
    print("-" * 60)
    top_items = sorted(item_perf.items(), key=lambda x: x[1]['usage_count'], reverse=True)[:15]
    print(f"{'Item':<35} {'Usage':>8} {'Avg Place':>10} {'Top 4%':>8}")
    print("-" * 60)
    for item, stats in top_items:
        name = item.replace('TFT_Item_', '').replace('TFT13_Item_', '')
        print(f"{name:<35} {stats['usage_count']:>8} {stats['avg_placement']:>10} {stats['win_rate']:>7}%")
    
    # Game version tracking
    versions = analyze_game_versions(all_matches)
    print("\n>> GAME VERSIONS OBSERVED:")
    print("-" * 40)
    for version, count in versions.most_common(5):
        print(f"  Patch {version}: {count} matches")
    
    # ================================================================
    # RESEARCH QUESTION 2: Factors Contributing to Success
    # ================================================================
    print("\n" + "=" * 80)
    print("RESEARCH QUESTION 2: What factors contribute to successful team compositions?")
    print("=" * 80)
    
    trait_perf, trait_combos = analyze_trait_synergies(all_matches)
    
    # Top performing traits
    print("\n>> TOP 15 HIGHEST WIN-RATE TRAITS:")
    print("-" * 60)
    top_traits = sorted(trait_perf.items(), key=lambda x: x[1]['top4_rate'], reverse=True)[:15]
    print(f"{'Trait':<30} {'Picks':>8} {'Avg Place':>10} {'Top 4%':>8}")
    print("-" * 60)
    for trait, stats in top_traits:
        name = trait.replace('Set13_', '').replace('Set12_', '')
        print(f"{name:<30} {stats['pick_count']:>8} {stats['avg_placement']:>10} {stats['top4_rate']:>7}%")
    
    # Most popular traits
    print("\n>> TOP 15 MOST ACTIVATED TRAITS:")
    print("-" * 60)
    popular_traits = sorted(trait_perf.items(), key=lambda x: x[1]['pick_count'], reverse=True)[:15]
    print(f"{'Trait':<30} {'Picks':>8} {'Avg Place':>10} {'Top 4%':>8}")
    print("-" * 60)
    for trait, stats in popular_traits:
        name = trait.replace('Set13_', '').replace('Set12_', '')
        print(f"{name:<30} {stats['pick_count']:>8} {stats['avg_placement']:>10} {stats['top4_rate']:>7}%")
    
    # Augment analysis
    augment_perf = analyze_augments(all_matches)
    print("\n>> TOP 15 HIGHEST WIN-RATE AUGMENTS:")
    print("-" * 70)
    top_augments = sorted(augment_perf.items(), key=lambda x: x[1]['win_rate'], reverse=True)[:15]
    print(f"{'Augment':<45} {'Picks':>6} {'Avg Place':>10} {'Top 4%':>8}")
    print("-" * 70)
    for augment, stats in top_augments:
        name = augment.replace('TFT13_Augment_', '').replace('TFT_Augment_', '')[:40]
        print(f"{name:<45} {stats['pick_count']:>6} {stats['avg_placement']:>10} {stats['win_rate']:>7}%")
    
    # ================================================================
    # RESEARCH QUESTION 3: Player Strategy Adaptation
    # ================================================================
    print("\n" + "=" * 80)
    print("RESEARCH QUESTION 3: How do player strategies adapt to game updates?")
    print("=" * 80)
    
    # Analyze placement distribution
    placements = []
    levels = []
    for match in all_matches:
        if 'info' not in match or 'participants' not in match['info']:
            continue
        for p in match['info']['participants']:
            placements.append(p.get('placement', 0))
            levels.append(p.get('level', 0))
    
    print("\n>> PLACEMENT DISTRIBUTION:")
    print("-" * 40)
    placement_counts = Counter(placements)
    for place in sorted(placement_counts.keys()):
        if place > 0:
            count = placement_counts[place]
            pct = count / len(placements) * 100
            bar = '█' * int(pct / 2)
            print(f"  {place}: {bar} {pct:.1f}% ({count})")
    
    print("\n>> AVERAGE LEVEL AT GAME END:")
    print("-" * 40)
    level_counts = Counter(levels)
    for level in sorted(level_counts.keys()):
        if level > 0:
            count = level_counts[level]
            pct = count / len(levels) * 100
            bar = '█' * int(pct / 2)
            print(f"  Level {level}: {bar} {pct:.1f}% ({count})")
    
    # Analyze tier distribution from collection metadata
    print("\n>> PLAYER TIER DISTRIBUTION (from ranked data):")
    print("-" * 40)
    tier_counts = Counter()
    for filepath in collection_files:
        if 'backup' in str(filepath):
            continue
        data = load_collection(filepath)
        for player_id, player_data in data.get('players', {}).items():
            tier = player_data.get('tier', 'Unknown')
            tier_counts[tier] += 1
    
    tier_order = ['CHALLENGER', 'GRANDMASTER', 'MASTER', 'DIAMOND', 'EMERALD', 
                  'PLATINUM', 'GOLD', 'SILVER', 'BRONZE', 'IRON']
    for tier in tier_order:
        if tier in tier_counts:
            count = tier_counts[tier]
            pct = count / sum(tier_counts.values()) * 100
            bar = '█' * int(pct)
            print(f"  {tier:<12}: {bar} {pct:.1f}% ({count})")
    
    # ================================================================
    # SUMMARY OF KEY FINDINGS
    # ================================================================
    print("\n" + "=" * 80)
    print("SUMMARY OF KEY FINDINGS")
    print("=" * 80)
    
    print("""
1. CHAMPION META-GAME:
   - Dataset captures unit usage across {} unique matches
   - Top champions by pick rate indicate current meta favorites
   - Performance metrics (avg placement, top4 rate) reveal tier-list rankings
   
2. SUCCESS FACTORS:
   - Trait synergies show which combinations lead to top 4 finishes
   - Certain augments provide significant competitive advantages
   - Item usage patterns reveal optimal itemization strategies
   
3. PLAYER ADAPTATION:
   - Game version tracking enables patch-by-patch analysis
   - Level distribution shows economy management strategies
   - Tier distribution validates data covers all skill levels

NOTE: This analysis uses {} matches from {} collection cycles.
For temporal evolution analysis, more collection cycles over multiple patches
would strengthen conclusions about meta-game changes over time.
""".format(len(all_matches), len(all_matches), len(collection_stats)))
    
    print("=" * 80)
    print("Analysis complete. Results can be added to final report.")
    print("=" * 80)

if __name__ == "__main__":
    main()
