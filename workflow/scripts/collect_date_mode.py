# scripts/collect_date_mode.py

import os
import sys
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.optimized_match_collector import create_match_collector
    from scripts.config_manager import create_config_manager
    from scripts.notification_system import EmailNotificationSystem
except Exception:
    print("ERROR: Cannot import project modules", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

def setup_logging(log_file: str):
    """Setup logging to both file and console with structured format."""
    log_format = '%(asctime)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

def main():
    # Get log file early to ensure it exists even if script fails
    log_file = os.environ.get("LOG_FILE", "logs/collection.log")
    
    # Ensure log file directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create log file immediately to satisfy Snakemake output requirements
    log_path.touch(exist_ok=True)
    
    # Setup logging early
    logger = setup_logging(log_file)
    
    api_key = os.environ.get("RIOT_API_KEY")
    if not api_key:
        logger.error("ERROR: RIOT_API_KEY missing")
        sys.exit(1)

    start_time = int(os.environ["START_TIME"])
    end_time = int(os.environ["END_TIME"])
    date_str = os.environ["DATE_STR"]
    output_dir = Path(os.environ["OUTPUT_DIR"])
    
    logger.info("=" * 70)
    logger.info("TFT DATA COLLECTION - DATE MODE")
    logger.info("=" * 70)
    logger.info(f"Collection Date: {date_str}")
    logger.info(f"Start Timestamp: {start_time} ({datetime.fromtimestamp(start_time, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')})")
    logger.info(f"End Timestamp:   {end_time} ({datetime.fromtimestamp(end_time, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')})")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Log File: {log_file}")
    logger.info("-" * 70)

    try:
        logger.info("Initializing collector and configuration...")
        collector = create_match_collector(api_key)
        config_mgr = create_config_manager()
        
        notification_config = config_mgr.get_notification_config()
        notifier = EmailNotificationSystem({'notifications': notification_config}) if notification_config else None

        weekly_cfg = config_mgr.get_period_config("weekly")
        tier_list = weekly_cfg.parameters.get("tiers") if weekly_cfg else None
        division_list = weekly_cfg.parameters.get("divisions") if weekly_cfg else None
        
        logger.info(f"Collection parameters: tiers={tier_list}, divisions={division_list}")

        logger.info("Collecting leaderboard data...")
        leaderboard = collector.collect_leaderboard_data(
            tiers=tier_list,
            divisions=division_list
        )
        if not leaderboard:
            logger.error("Leaderboard fetch failed - no data returned")
            sys.exit(1)
        
        leaderboard_entries = sum(len(entries.get('entries', [])) for entries in leaderboard.values())
        logger.info(f"[SUCCESS] Leaderboard collected: {len(leaderboard)} tiers, {leaderboard_entries} total entries")
        
        collector.collected_data["leaderboards"] = leaderboard

        logger.info("👥 Extracting player PUUIDs from leaderboard...")
        puuids = collector.get_top_players_puuids(None)
        if not puuids:
            logger.error("No PUUIDs found in leaderboard data")
            sys.exit(1)
        
        logger.info(f"[SUCCESS] Found {len(puuids)} unique players")

        logger.info("🎮 Starting match collection...")
        collection_start = datetime.now(timezone.utc)
        
        # Define checkpoint file
        checkpoint_file = output_dir / f"tft_collection_{date_str}_checkpoint.json"
        if checkpoint_file.exists():
            logger.info(f"[INFO] Found checkpoint file: {checkpoint_file}")
            logger.info("Resuming collection from checkpoint...")
        
        results = collector.collect_matches_for_multiple_players(
            player_puuids=puuids,
            match_count_per_player=1000,
            start_time=start_time,
            end_time=end_time,
            checkpoint_file=checkpoint_file
        )
        
        collection_end = datetime.now(timezone.utc)
        collection_duration = (collection_end - collection_start).total_seconds()

        results["leaderboards"] = leaderboard

        matches_collected = len(results.get('matches', {}))
        players_processed = len(puuids)
        collection_stats = results.get('collection_stats', {})
        
        # Add collectionInfo for validation compliance
        results["collectionInfo"] = {
            "@type": "CollectionInfo",
            "@id": f"collection:{collection_start.isoformat()}",
            'timestamp': collection_start.isoformat(),
            'extractionLocation': 'LA2',
            'dataVersion': '1.0.0',
            'collection_type': 'date_mode',
            'collection_date': date_str,
            'players_count': players_processed,
            'matches_count': matches_collected,
            'collection_duration_seconds': collection_duration,
            'start_time': start_time,
            'end_time': end_time
        }
        
        logger.info("-" * 70)
        logger.info("COLLECTION SUMMARY")
        logger.info("-" * 70)
        logger.info(f"Matches Collected: {matches_collected}")
        logger.info(f"Players Processed: {players_processed}")
        logger.info(f"Collection Duration: {collection_duration:.2f} seconds")
        if collection_stats:
            logger.info(f"Total Match IDs Found: {collection_stats.get('total_match_ids_collected', 'N/A')}")
            logger.info(f"Unique Matches: {collection_stats.get('unique_matches_fetched', 'N/A')}")
            logger.info(f"API Calls Saved (dedup): {collection_stats.get('api_calls_saved', 'N/A')}")
        logger.info("-" * 70)

        # Save with the expected filename that Snakemake expects
        outpath = output_dir / f"tft_collection_{date_str}.json"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving results to {outpath}...")
        with open(outpath, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        file_size_mb = outpath.stat().st_size / (1024 * 1024)
        logger.info(f"[SUCCESS] File saved successfully ({file_size_mb:.2f} MB)")
        
        # Clean up checkpoint file on success
        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                logger.info("[INFO] Checkpoint file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to delete checkpoint file: {e}")
        
        error_summary = results.get('error_summary', {})
        total_errors = error_summary.get('total_errors', 0)
        errors_by_category = {}
        for category, stats in error_summary.items():
            if category not in ['total_errors', 'failed_match_ids', 'failed_player_puuids']:
                if isinstance(stats, dict) and stats.get('count', 0) > 0:
                    errors_by_category[category] = stats
        
        collection_stats_for_notification = {
            'start_time': collection_start,
            'end_time': collection_end,
            'duration': f"{collection_duration:.2f} seconds",
            'success': True,
            'players_collected': players_processed,
            'matches_collected': matches_collected,
            'data_size_mb': file_size_mb,
            'quality_score': 0,  # Will be calculated later in workflow
            'files_created': [str(outpath)],
            'total_errors': total_errors,
            'errors_by_category': errors_by_category,
            'failed_match_ids': error_summary.get('failed_match_ids', []),
            'failed_player_puuids': error_summary.get('failed_player_puuids', [])
        }
        
        # Send email notifications if enabled
        if notifier:
            try:
                notifier.send_collection_summary(collection_stats_for_notification, date_str)
                
                # Send quality warning if needed (will be updated after quality assessment)
                quality_score = collection_stats_for_notification.get('quality_score', 0)
                if notifier.should_send_quality_warning(quality_score):
                    notifier.send_quality_warning(
                        quality_score,
                        notifier.quality_score_threshold,
                        date_str
                    )
                
                # Send error alert if threshold exceeded
                if notifier.should_send_error_alert(total_errors):
                    error_details = {
                        'total_errors': total_errors,
                        'errors_by_category': errors_by_category,
                        'failed_match_ids_count': len(error_summary.get('failed_match_ids', [])),
                        'failed_player_puuids_count': len(error_summary.get('failed_player_puuids', []))
                    }
                    notifier.send_error_alert('error_threshold_exceeded', error_details, date_str)
            except Exception as e:
                logger.error(f"Failed to send email notifications: {e}")
                logger.error(traceback.format_exc())
        
        logger.info("=" * 70)
        logger.info("[SUCCESS] COLLECTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("[WARNING] Collection interrupted by user")
        try:
            config_mgr = create_config_manager()
            notification_config = config_mgr.get_notification_config()
            if notification_config:
                notifier = EmailNotificationSystem({'notifications': notification_config})
                error_details = {
                    'collection_failed': True,
                    'error_type': 'user_interrupt',
                    'message': 'Collection interrupted by user'
                }
                notifier.send_error_alert('collection_failure', error_details, date_str)
        except:
            pass
        sys.exit(130)
    except Exception as e:
        logger.error(f"[ERROR] Fatal error during collection: {e}")
        logger.error(traceback.format_exc())
        try:
            config_mgr = create_config_manager()
            notification_config = config_mgr.get_notification_config()
            if notification_config:
                notifier = EmailNotificationSystem({'notifications': notification_config})
                error_details = {
                    'collection_failed': True,
                    'error_type': 'fatal_error',
                    'error_message': str(e)
                }
                notifier.send_error_alert('collection_failure', error_details, date_str)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
