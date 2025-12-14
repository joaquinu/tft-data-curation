#!/usr/bin/env python3
"""
Automated data collection system for weekly TFT data updates.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import traceback
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scripts.optimized_match_collector import create_match_collector
    from scripts.config_manager import create_config_manager
    from scripts.notification_system import EmailNotificationSystem
    from quality_assurance import (
        validate_json_structure, 
        calculate_data_quality_score,
        detect_statistical_anomalies
    )
    
except ImportError as e:
    print(f"Critical import error: {e}")
    print("Make sure you're running from the project root directory.")
    sys.exit(1)

class AutomatedCollector:
    """
    Automated TFT data collection system with production-ready features.
    """
    
    def __init__(self, config):
        """
        Initialize the automated collector with configuration.
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.dry_run = config.get('dry_run', False)
        self.output_dir = Path(config.get('output_dir', '.'))
        self.log_file = config.get('log_file', 'automated_collection.log')
        
        self.setup_logging()
        
        if not self.dry_run:
            try:
                self.collector = create_match_collector(self.api_key)
                self.logger.info("TFTMatchCollector initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize collectors: {e}")
                raise
        else:
            self.collector = None
            self.logger.info("Running in DRY-RUN mode - no actual data collection")
        
        self.stats = {
            'start_time': datetime.now(),
            'end_time': None,
            'success': False,
            'players_collected': 0,
            'matches_collected': 0,
            'data_size_mb': 0,
            'quality_score': 0,
            'files_created': [],
            'unique_matches_fetched': 0,
            'total_match_references': 0,
            'api_calls_saved': 0,
            'efficiency_percentage': 0,
            'collection_time_seconds': 0,
            'total_errors': 0,
            'errors_by_category': {},
            'failed_match_ids': [],
            'failed_player_puuids': []
        }
        self.notifier = EmailNotificationSystem(config)
    
    def setup_logging(self):
        """Setup comprehensive logging for automated execution."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('AutomatedTFTCollection')
        
        # Log collection start
        self.logger.info("=" * 60)
        self.logger.info("🤖 TFT AUTOMATED DATA COLLECTION STARTED")
        self.logger.info("=" * 60)
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2, default=str)}")
    
    def validate_environment(self):
        """Validate that all required environment variables and dependencies are available."""
        
        if not self.api_key:
            raise ValueError("RIOT_API_KEY environment variable is required")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.dry_run:
            try:
                test_result = self.collector.get_challenger_league()
                if not test_result or len(test_result.get('entries', [])) == 0:
                    raise ValueError("API test failed - no challenger league data returned")
            except Exception as e:
                self.logger.error(f"[ERROR] API connection test failed: {e}")
                raise
        
        self.logger.info("Environment validation completed")
    
    def _run_collection(self, players_count, preset: str, matches_per_player: int = 50):
        """
        Run collection that avoids duplicate API calls for shared matches.
        
        Args:
            players_count: Number of players to collect (None = collect all available)
            preset: Collection preset mode
            matches_per_player: Number of matches per player
        """
        self.logger.info("Running data collection...")
        if players_count is None:
            self.logger.info(f"Target: ALL available players, ~{matches_per_player} matches each")
        else:
            self.logger.info(f"Target: {players_count} players, ~{matches_per_player} matches each")
        
        start_time = time.time()
        
        try:
            self.logger.info("Step 1: Fetching player leaderboard...")
            config_mgr = create_config_manager()
            weekly_cfg = config_mgr.get_period_config("weekly")
            tier_list = weekly_cfg.parameters.get('tiers', None) if weekly_cfg else None
            division_list = weekly_cfg.parameters.get('divisions', None) if weekly_cfg else None
            leaderboard = self.collector.collect_leaderboard_data(
                tiers=tier_list,
                divisions=division_list
            )
            
            if not leaderboard:
                raise ValueError("Failed to fetch leaderboard data")
            
            self.collector.collected_data["leaderboards"] = leaderboard
            self.logger.info(f"Stored leaderboard data with {len(leaderboard)} tiers")
            
            if players_count is None:
                self.logger.info(f"Getting ALL available player PUUIDs using existing method...")
            else:
                self.logger.info(f"Getting top {players_count} player PUUIDs using existing method...")
            all_puuids = self.collector.get_top_players_puuids(players_count)
            
            if not all_puuids:
                raise ValueError("No PUUIDs found from leaderboard data")
            
            self.logger.info(f"Got {len(all_puuids)} player PUUIDs from leaderboard")
            
            self.logger.info("Step 2: Running match collection...")
            
            if preset == 'last_7_days':
                collection_results = self.collector.collect_matches_with_time_filter(
                    player_puuids=all_puuids,
                    preset=preset
                )
            else:
                collection_results = self.collector.collect_matches_for_multiple_players(
                    player_puuids=all_puuids,
                    match_count_per_player=matches_per_player
                )
            
            collection_time = time.time() - start_time
            
            efficiency_stats = collection_results.get('collection_stats', {})
            
            self.logger.info("--------------------------------\nOPTIMIZATION RESULTS:")
            self.logger.info(f"   Players processed: {efficiency_stats.get('players_processed', 0)}")
            self.logger.info(f"   Total match references: {efficiency_stats.get('total_match_ids_collected', 0)}")
            self.logger.info(f"   Unique matches fetched: {efficiency_stats.get('unique_matches_fetched', 0)}")
            self.logger.info(f"   API calls saved: {efficiency_stats.get('api_calls_saved', 0)}")
            self.logger.info(f"   Collection time: {collection_time:.2f} seconds")
            
            if efficiency_stats.get('api_calls_saved', 0) > 0:
                efficiency_percentage = (efficiency_stats['api_calls_saved'] / efficiency_stats['total_match_ids_collected']) * 100
                time_saved_minutes = efficiency_stats['api_calls_saved'] / 100
                self.logger.info(f"Efficiency gain: {efficiency_percentage:.1f}% reduction in API calls")
                self.logger.info(f"Time saved: ~{time_saved_minutes:.1f} minutes")
                self.stats['efficiency_percentage'] = efficiency_percentage
            self.logger.info("--------------------------------\n")
            
            self.stats['collection_time_seconds'] = collection_time
            self.stats['unique_matches_fetched'] = efficiency_stats.get('unique_matches_fetched', 0)
            self.stats['total_match_references'] = efficiency_stats.get('total_match_ids_collected', 0)
            self.stats['api_calls_saved'] = efficiency_stats.get('api_calls_saved', 0)
            
            error_summary = collection_results.get('error_summary', {})
            total_errors = error_summary.get('total_errors', 0)
            errors_by_category = error_summary.get('errors_by_category', {})
            failed_match_ids = error_summary.get('failed_match_ids', [])
            failed_player_puuids = error_summary.get('failed_player_puuids', [])
            
            self.stats['total_errors'] = total_errors
            self.stats['errors_by_category'] = errors_by_category
            self.stats['failed_match_ids'] = failed_match_ids
            self.stats['failed_player_puuids'] = failed_player_puuids
            
            if total_errors > 0:
                self.logger.warning(f"[WARNING] Collection encountered {total_errors} errors:")
                for category, error_info in errors_by_category.items():
                    count = error_info.get('count', 0)
                    match_count = len(error_info.get('match_ids', []))
                    player_count = len(error_info.get('player_puuids', []))
                    self.logger.warning(f"   - {category}: {count} errors ({match_count} matches, {player_count} players)")
                
                if failed_match_ids:
                    self.logger.info(f"   Failed match IDs ({len(failed_match_ids)}): {failed_match_ids[:10]}{'...' if len(failed_match_ids) > 10 else ''}")
                if failed_player_puuids:
                    self.logger.info(f"   Failed player PUUIDs ({len(failed_player_puuids)}): {len(failed_player_puuids)} players")
            else:
                self.logger.info("[SUCCESS] No errors encountered during collection")
            
            from scripts.schema import get_tft_context
            comprehensive_context = get_tft_context()
            self.collector.collected_data["@context"] = comprehensive_context
            
            annotated_matches = {}
            for match_id, match_data in collection_results.get('matches', {}).items():
                match_data["@type"] = "TFTMatch"
                annotated_matches[match_id] = match_data
            
            self.collector.collected_data["players"] = collection_results.get('players', {})
            self.collector.collected_data["matches"] = annotated_matches
            
            self.collector.collected_data["collectionInfo"] = {
                "@type": "CollectionInfo", 
                "@id": f"collection:{datetime.now().isoformat()}",
                'timestamp': datetime.now().isoformat(),
                'extractionLocation': 'LA2',
                'dataVersion': '1.0.0',
                'collection_type': 'optimized',
                'players_count': len(collection_results.get('players', {})),
                'matches_count': len(collection_results.get('matches', {})),
                'optimization_stats': efficiency_stats,
                'collection_time': collection_time
            }
            
            data = {
                'players': collection_results.get('players', {}),
                'matches': collection_results.get('matches', {}),
                'collectionInfo': self.collector.collected_data["collectionInfo"]
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"[ERROR] Collection failed: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def run_weekly_collection(self):
        """Execute weekly data collection with comprehensive validation."""
        self.logger.info("Starting weekly data collection...")
        
        try:
            config_mgr = create_config_manager()
            weekly_config = config_mgr.get_period_config("weekly")
            
            collection_config = {
                'players_count': weekly_config.parameters.get('max_players', None),  # None = collect all players
                'collection_mode': 'last_7_days',
                'include_quality_check': True,
                'include_pipeline_test': self.config.get('run_pipeline_tests', True)
            }
            
            self.logger.info(f"Collection config: {collection_config}")
            
            if self.dry_run:
                return self._simulate_collection(collection_config)
            
            self.logger.info("Estimating collection requirements...")
            self.collector.estimate_collection_time(
                collection_config['players_count'], 
                50,
                "count"
            )
            
            self.logger.info("Starting data collection...")
            
            collected_data = self._run_collection(
                players_count=collection_config['players_count'],
                preset=collection_config['collection_mode'],
                matches_per_player=50
            )
            
            self.logger.info(f"Data collection completed in {self.stats['collection_time_seconds']:.2f} seconds")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"tft_weekly_collection_{timestamp}.json"
            
            saved_filename = self.collector.save_data_to_file(str(filename))
            self.stats['files_created'].append(saved_filename)
            
            file_size_mb = Path(saved_filename).stat().st_size / (1024 * 1024)
            self.stats['data_size_mb'] = file_size_mb
            
            self.logger.info(f"Data saved to: {saved_filename} ({file_size_mb:.2f} MB)")
            
            self.stats['players_collected'] = len(collected_data.get('players', {}))
            
            total_matches = 0
            for player_data in collected_data.get('players', {}).values():
                total_matches += len(player_data.get('matches', {}))
            self.stats['matches_collected'] = total_matches
            
            self.logger.info(f"📈 Collection summary: {self.stats['players_collected']} players, {self.stats['matches_collected']} matches")
            
            if collection_config['include_quality_check']:
                self._run_quality_validation(collected_data, saved_filename)
            
            
            self.stats['success'] = True
            self.logger.info("Weekly collection completed successfully")
            
            return collected_data
            
        except Exception as e:
            self.logger.error(f"Weekly collection failed: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def run_incremental_collection(self):
        """
        Execute incremental data collection - ALL matches from YESTERDAY.
        
        Collects matches by scanning ranked ladder tiers and retrieving match histories
        for YESTERDAY, deduplicating across all players found.
        """
        self.logger.info("Starting daily incremental collection (ALL matches from YESTERDAY)...")
        
        try:
            config_mgr = create_config_manager()
            daily_config = config_mgr.get_period_config("daily")
            
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            yesterday_start = int((now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            yesterday_end = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            
            self.logger.info(f"Collection period: Yesterday ({yesterday_start} to {yesterday_end})")
            
            collection_config = {
                'collection_mode': 'yesterday_all_matches',
                'include_quality_check': False,
                'include_pipeline_test': False,
                'time_filter': {
                    'start_time': yesterday_start,
                    'end_time': yesterday_end,
                    'period': 'YESTERDAY ONLY'
                }
            }
            
            if self.dry_run:
                return self._simulate_collection(collection_config)
            
            self.logger.info("Scanning ranked ladder for matches from YESTERDAY...")
            
            all_match_ids = set()
            players_found = 0
            players_info = {}
            
            config_mgr = create_config_manager()
            daily_cfg = config_mgr.get_period_config("daily")
            tiers = daily_cfg.parameters.get('tiers', ["DIAMOND"]) if daily_cfg else ["DIAMOND"]
            divisions = daily_cfg.parameters.get('divisions', ["I", "II", "III", "IV"]) if daily_cfg else ["I", "II", "III", "IV"]
            
            high_elo_map = {
                "CHALLENGER": self.collector.get_challenger_league,
                "GRANDMASTER": self.collector.get_grandmaster_league,
                "MASTER": self.collector.get_master_league
            }

            for high_tier, fetch_fn in high_elo_map.items():
                if high_tier in tiers:
                    try:
                        league = fetch_fn()
                        for entry in league.get('entries', []) if league else []:
                            puuid = entry.get('puuid')
                            if not puuid and entry.get('summonerId'):
                                summoner = self.collector.get_summoner_by_id(entry["summonerId"]) or {}
                                puuid = summoner.get('puuid')
                            if puuid:
                                players_info.setdefault(puuid, {})
                                players_info[puuid]["current_rank"] = {
                                    "tier": high_tier,
                                    "rank": entry.get('rank'),
                                    "leaguePoints": entry.get('leaguePoints'),
                                    "wins": entry.get('wins'),
                                    "losses": entry.get('losses')
                                }
                                start_index = 0
                                counted_player = False
                                while True:
                                    match_ids = self.collector.get_match_ids_by_puuid(
                                        puuid=puuid,
                                        start=start_index,
                                        count=100,
                                        start_time=yesterday_start,
                                        end_time=yesterday_end
                                    )
                                    if not match_ids:
                                        break
                                    all_match_ids.update(match_ids)
                                    if not counted_player:
                                        players_found += 1
                                        counted_player = True
                                    if len(match_ids) < 100:
                                        break
                                    start_index += 100
                    except Exception as e:
                        self.logger.debug(f"High-elo fetch failed for {high_tier}: {e}")

            for tier in tiers:
                if tier in high_elo_map:
                    continue
                self.logger.info(f"  Scanning {tier} tier...")
                for division in divisions:
                    try:
                        entries = self.collector.get_league_entries_by_tier(tier, division)
                        
                        if entries:
                            self.logger.info(f"    Found {len(entries)} players in {tier} {division}")
                            
                            for entry in entries:
                                try:
                                    puuid = entry.get("puuid")
                                    
                                    if not puuid:
                                        self.logger.warning(f"Entry missing PUUID, skipping: {entry.get('summonerId', 'unknown')}")
                                        continue
                                    
                                    if puuid:
                                        players_info.setdefault(puuid, {})
                                        players_info[puuid]["current_rank"] = {
                                            "tier": tier,
                                            "rank": entry.get('rank') or division,
                                            "leaguePoints": entry.get('leaguePoints'),
                                            "wins": entry.get('wins'),
                                            "losses": entry.get('losses')
                                        }
                                        start_index = 0
                                        counted_player = False
                                        while True:
                                            match_ids = self.collector.get_match_ids_by_puuid(
                                                puuid=puuid,
                                                start=start_index,
                                                count=100,
                                                start_time=yesterday_start,
                                                end_time=yesterday_end
                                            )
                                            if not match_ids:
                                                break
                                            all_match_ids.update(match_ids)
                                            if not counted_player:
                                                players_found += 1
                                                counted_player = True
                                            if len(match_ids) < 100:
                                                break
                                            start_index += 100
                                            
                                except Exception as e:
                                    self.logger.debug(f"Failed to get matches for player: {e}")
                                    continue
                        
                        time.sleep(0.2)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to get entries for {tier} {division}: {e}")
                        continue
            
            self.logger.info(f"[SUCCESS] Scan complete: Found {players_found} players with {len(all_match_ids)} unique matches from YESTERDAY")
            
            collected_data = {
                'players': {},
                'matches': {},
                'collection_stats': {
                    'players_processed': players_found,
                    'total_match_ids_collected': len(all_match_ids),
                    'unique_matches_fetched': 0,
                    'api_calls_saved': 0,
                    'collection_time_seconds': 0
                }
            }

            if all_match_ids:
                self.logger.info(f"Fetching details for {len(all_match_ids)} unique matches...")
                fetched = 0
                for match_id in all_match_ids:
                    try:
                        match_details = self.collector.get_match_details(match_id)
                        if match_details:
                            collected_data['matches'][match_id] = match_details
                            fetched += 1
                            if fetched % 100 == 0:
                                self.logger.info(f"   ...fetched {fetched} match details so far")
                    except Exception as e:
                        self.logger.debug(f"Failed to fetch match {match_id}: {e}")
                collected_data['collection_stats']['unique_matches_fetched'] = fetched
            else:
                self.logger.info("No unique matches found for YESTERDAY; creating empty collection")
            
            from scripts.schema import get_tft_context
            comprehensive_context = get_tft_context()
            self.collector.collected_data = {
                "@context": comprehensive_context,
                "players": {p: {"@type": "TFTPlayer", "@id": f"player:{p}", "puuid": p, **players_info.get(p, {})} for p in players_info.keys()},
                "matches": collected_data.get('matches', {}),
                "collectionInfo": {
                    "@type": "CollectionInfo",
                    "@id": f"collection:{datetime.now().isoformat()}",
                    'timestamp': datetime.now().isoformat(),
                    'extractionLocation': 'LA2',
                    'dataVersion': '1.0.0',
                    'collection_type': 'incremental_yesterday',
                    'players_count': players_found,
                    'matches_count': len(collected_data.get('matches', {})),
                    'time_window_start': yesterday_start,
                    'time_window_end': yesterday_end,
                    'optimization_stats': collected_data.get('collection_stats', {})
                }
            }

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"tft_incremental_{timestamp}.json"
            saved_filename = self.collector.save_data_to_file(str(filename))
            
            self.stats['files_created'].append(saved_filename)
            try:
                file_size_mb = Path(saved_filename).stat().st_size / (1024 * 1024)
            except Exception:
                file_size_mb = 0.0
            self.stats['data_size_mb'] = file_size_mb
            self.stats['players_collected'] = players_found
            self.stats['matches_collected'] = len(self.collector.collected_data.get('matches', {}))
            self.stats['success'] = True
            
            self.logger.info(f"Incremental collection completed: {saved_filename}")
            return collected_data
            
        except Exception as e:
            self.logger.error(f"[ERROR] Incremental collection failed: {e}")
            raise
    
    def _run_quality_validation(self, collected_data, data_file):
        """Run comprehensive quality validation on collected data."""
        self.logger.info("Running quality validation...")
        
        try:
            from quality_assurance.data_validator import validate_tft_data_structure
            is_valid, validation_errors = validate_tft_data_structure(collected_data)
            
            if is_valid:
                self.logger.info(f"JSON structure validation: PASS")
            else:
                self.logger.warning(f"JSON structure validation: FAIL - {validation_errors}")
            
            quality_score_report = calculate_data_quality_score(collected_data)
            quality_score = quality_score_report.get('overall_score', 0.0)
            self.stats['quality_score'] = quality_score
            self.logger.info(f"Data quality score: {quality_score:.2f}/100")
            
            if quality_score < 70:
                self.logger.warning("LOW QUALITY WARNING: Data quality score below 70")
            elif quality_score < 85:
                self.logger.info("ACCEPTABLE QUALITY: Data quality score acceptable")
            else:
                self.logger.info("HIGH QUALITY: Excellent data quality score")
            
            anomaly_report = detect_statistical_anomalies(collected_data)
            anomalies_detected = anomaly_report.get('anomalies_detected', [])
            anomaly_count = anomaly_report.get('anomaly_count', 0)
            
            if anomaly_count > 0:
                self.logger.warning(f" {anomaly_count} anomalies detected")
                for anomaly in anomalies_detected[:3]:
                    self.logger.warning(f"   - {anomaly}")
            else:
                self.logger.info("No statistical anomalies detected")
            
        except Exception as e:
            self.logger.error(f"Quality validation failed: {e}")
    
    
    def _simulate_collection(self, config):
        """Simulate data collection for dry-run mode."""
        
        self.stats['players_collected'] = config['players_count']
        self.stats['matches_collected'] = config['players_count'] * 45
        self.stats['data_size_mb'] = config['players_count'] * 2.5
        self.stats['quality_score'] = 92.5
        self.stats['success'] = True
        
        mock_filename = f"DRY_RUN_tft_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.stats['files_created'].append(mock_filename)
        
        self.logger.info(f"Simulated collection: {self.stats['players_collected']} players, {self.stats['matches_collected']} matches")
        self.logger.info(f"Would create file: {mock_filename}")
        
        return {"simulation": True, "config": config}
    
    def cleanup(self):
        """Cleanup and finalization."""
        self.logger.info("🧹 Running cleanup...")
        
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        self.logger.info("FINAL STATISTICS:")
        self.logger.info(f"   Duration: {duration}")
        self.logger.info(f"   Success: {self.stats['success']}")
        self.logger.info(f"   Players: {self.stats['players_collected']}")
        self.logger.info(f"   Matches: {self.stats['matches_collected']}")
        self.logger.info(f"   Data Size: {self.stats['data_size_mb']:.2f} MB")
        self.logger.info(f"   Quality Score: {self.stats['quality_score']:.2f}")
        self.logger.info(f"   Files Created: {len(self.stats['files_created'])}")
        
        total_errors = self.stats.get('total_errors', 0)
        if total_errors > 0:
            self.logger.info(f"   Total Errors: {total_errors}")
            errors_by_category = self.stats.get('errors_by_category', {})
            if errors_by_category:
                self.logger.info(f"   Errors by Category:")
                for category, error_info in errors_by_category.items():
                    count = error_info.get('count', 0)
                    self.logger.info(f"      - {category}: {count}")
            
            failed_match_ids = self.stats.get('failed_match_ids', [])
            failed_player_puuids = self.stats.get('failed_player_puuids', [])
            if failed_match_ids:
                self.logger.info(f"   Failed Match IDs: {len(failed_match_ids)}")
            if failed_player_puuids:
                self.logger.info(f"   Failed Player PUUIDs: {len(failed_player_puuids)}")
        else:
            self.logger.info(f"   Errors: 0")
        
        self.logger.info("=" * 60)
        self.logger.info("🤖 TFT AUTOMATED DATA COLLECTION COMPLETED")
        self.logger.info("=" * 60)
        
        # Send email notifications
        self._send_notifications()
    
    def _send_notifications(self):
        """Send email notifications based on collection results."""
        try:
            # Always send collection summary if enabled
            collection_date = self.stats.get('start_time', datetime.now()).strftime('%Y-%m-%d')
            self.notifier.send_collection_summary(self.stats, collection_date)
            
            # Send quality warning if score is below threshold
            quality_score = self.stats.get('quality_score', 0)
            if self.notifier.should_send_quality_warning(quality_score):
                self.notifier.send_quality_warning(
                    quality_score,
                    self.notifier.quality_score_threshold,
                    collection_date
                )
            
            # Send error alert if error count exceeds threshold
            total_errors = self.stats.get('total_errors', 0)
            if self.notifier.should_send_error_alert(total_errors):
                error_details = {
                    'total_errors': total_errors,
                    'errors_by_category': self.stats.get('errors_by_category', {}),
                    'failed_match_ids_count': len(self.stats.get('failed_match_ids', [])),
                    'failed_player_puuids_count': len(self.stats.get('failed_player_puuids', []))
                }
                self.notifier.send_error_alert('error_threshold_exceeded', error_details, collection_date)
            
            # Send critical failure alert if collection failed
            if not self.stats.get('success', False):
                error_details = {
                    'collection_failed': True,
                    'total_errors': total_errors,
                    'duration': str(self.stats.get('end_time', datetime.now()) - self.stats.get('start_time', datetime.now()))
                }
                self.notifier.send_error_alert('collection_failure', error_details, collection_date)
                
        except Exception as e:
            self.logger.error(f"Failed to send email notifications: {e}")
            self.logger.error(traceback.format_exc())


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="TFT Automated Data Collection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Weekly collection (default)
  python scripts/automated_collection.py --mode weekly
  
  # Dry run test
  python scripts/automated_collection.py --dry-run
  
  # Incremental collection
  python scripts/automated_collection.py --mode incremental
  
  # Custom parameters
  python scripts/automated_collection.py --players 1000 --output-dir /data/tft
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['weekly', 'incremental'], 
        default='weekly',
        help='Collection mode (default: weekly)'
    )
    
    parser.add_argument(
        '--players', 
        type=int, 
        default=None,
        help='Number of players to collect (overrides mode defaults)'
    )
    
    parser.add_argument(
        '--output-dir', 
        default='.',
        help='Output directory for data files (default: current directory)'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Run in simulation mode without actual data collection'
    )
    
    parser.add_argument(
        '--no-pipeline-tests', 
        action='store_true',
        help='Skip pipeline validation tests (faster execution)'
    )
    
    parser.add_argument(
        '--log-file', 
        default='automated_collection.log',
        help='Log file path (default: automated_collection.log)'
    )
    
    parser.add_argument(
        '--config-file',
        help='JSON configuration file (overrides command line options)'
    )
    
    return parser.parse_args()


def load_configuration(args):
    """Load configuration from environment variables, config file, and command line args"""
    
    # Use config_manager to load configuration
    config_mgr = create_config_manager()
    
    config = {
        'api_key': os.getenv('RIOT_API_KEY'),
        'run_pipeline_tests': True,
    }
    
    notification_config = config_mgr.get_notification_config()
    if notification_config:
        config['notifications'] = notification_config
    
    # Load from config file if specified
    if args.config_file:
        try:
            with open(args.config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"[ERROR] Failed to load config file {args.config_file}: {e}")
            sys.exit(1)
    
    config.update({
        'mode': args.mode,
        'dry_run': args.dry_run,
        'output_dir': args.output_dir,
        'log_file': args.log_file,
        'run_pipeline_tests': not args.no_pipeline_tests,
    })
    
    return config


def main():
    """Main execution function."""
    args = parse_arguments()
    config = load_configuration(args)
    
    collector = None
    try:
        collector = AutomatedCollector(config)
        
        collector.validate_environment()
        
        if config['mode'] == 'weekly':
            collector.run_weekly_collection()
        elif config['mode'] == 'incremental':
            collector.run_incremental_collection()
        else:
            raise ValueError(f"Unknown collection mode: {config['mode']}")

        
        return 0
        
    except Exception as e:
        error_msg = f"Critical failure in automated collection: {e}"
        
        if collector:
            collector.logger.error(error_msg)
            collector.logger.error(traceback.format_exc())
        else:
            print(f"{error_msg}")
            print(traceback.format_exc())
        
        return 1
        
    finally:
        if collector:
            collector.cleanup()


if __name__ == "__main__":
    sys.exit(main())
