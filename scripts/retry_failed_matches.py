#!/usr/bin/env python3
"""
This script retries fetching match details for failed match IDs from previous collections.
It can be used to recover data that failed during initial collection due to rate limits,
timeouts, or other transient errors.

Usage:
    python scripts/retry_failed_matches.py --match-ids LA2_123456 LA2_789012
    python scripts/retry_failed_matches.py --from-file data/raw/tft_collection_20251116.json
    python scripts/retry_failed_matches.py --from-error-summary collection_results.json
"""

import json
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.base_infrastructure import BaseAPIInfrastructure
from scripts.riot_api_endpoints import RiotAPIEndpoints
from scripts.rate_limiting import create_rate_limited_session
from scripts.identifier_system import TFTIdentifierSystem
from scripts.utils import load_data_from_file, save_data_to_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MatchRetryCollector(BaseAPIInfrastructure, RiotAPIEndpoints):
    """Specialized collector for retrying failed match IDs"""
    
    def __init__(self, api_key: str, key_type: str = "personal"):
        super().__init__(api_key, key_type)
        self.identifier_system = TFTIdentifierSystem()
        self.retry_stats = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'failed_match_ids': []
        }
    
    def retry_match_ids(self, match_ids: List[str]) -> Dict[str, Any]:
        """
        Retry fetching match details for a list of match IDs.
        """
        logger.info(f"Retrying {len(match_ids)} failed match IDs...")
        
        results = {
            'matches': {},
            'retry_stats': {
                'total_attempted': len(match_ids),
                'successful': 0,
                'failed': 0,
                'failed_match_ids': [],
                'successful_match_ids': []
            },
            'retry_timestamp': datetime.now().isoformat()
        }
        
        for i, match_id in enumerate(match_ids, 1):
            logger.info(f"Retrying match {i}/{len(match_ids)}: {match_id}")
            
            try:
                match_details = self.get_match_details(match_id)
                
                if match_details:
                    persistent_match_id = self.identifier_system.create_match_identifier(
                        match_id,
                        match_details
                    )
                    
                    match_details["@type"] = "TFTMatch"
                    match_details["@id"] = persistent_match_id
                    match_details["riot_match_id"] = match_id
                    
                    results['matches'][match_id] = match_details
                    results['retry_stats']['successful'] += 1
                    results['retry_stats']['successful_match_ids'].append(match_id)
                    logger.info(f"Successfully fetched match {match_id}")
                else:
                    results['retry_stats']['failed'] += 1
                    results['retry_stats']['failed_match_ids'].append(match_id)
                    logger.warning(f"Failed to fetch match {match_id} (returned None)")
                    
            except Exception as e:
                results['retry_stats']['failed'] += 1
                results['retry_stats']['failed_match_ids'].append(match_id)
                logger.error(f"Error fetching match {match_id}: {e}")
        
        logger.info("=" * 60)
        logger.info("RETRY SUMMARY:")
        logger.info(f"   Total Attempted: {results['retry_stats']['total_attempted']}")
        logger.info(f"   Successful: {results['retry_stats']['successful']}")
        logger.info(f"   Failed: {results['retry_stats']['failed']}")
        logger.info(f"   Success Rate: {(results['retry_stats']['successful'] / results['retry_stats']['total_attempted'] * 100):.1f}%")
        logger.info("=" * 60)
        
        return results
    
    def save_retry_results(self, results: Dict[str, Any], output_file: str):
        """Save retry results to a JSON file"""
        saved_path = save_data_to_file(results, output_file, create_dirs=True)
        if saved_path:
            logger.info(f"Retry results saved to: {saved_path}")
        else:
            logger.error(f"Failed to save retry results to: {output_file}")


def extract_failed_match_ids_from_file(data_file: str) -> List[str]:
    """Extract failed match IDs from a collection data file"""
    data = load_data_from_file(data_file)
    if data is None:
        logger.error(f"Failed to load data file: {data_file}")
        return []
    
    error_summary = data.get('error_summary', {})
    failed_match_ids = error_summary.get('failed_match_ids', [])
    
    logger.info(f"Found {len(failed_match_ids)} failed match IDs in {data_file}")
    return failed_match_ids


def extract_failed_match_ids_from_error_summary(error_summary_file: str) -> List[str]:
    """Extract failed match IDs from an error summary file"""
    error_summary = load_data_from_file(error_summary_file)
    if error_summary is None:
        logger.error(f"Failed to load error summary file: {error_summary_file}")
        return []
    
    failed_match_ids = error_summary.get('failed_match_ids', [])
    
    errors_by_category = error_summary.get('errors_by_category', {})
    for category, error_info in errors_by_category.items():
        category_match_ids = error_info.get('match_ids', [])
        failed_match_ids.extend(category_match_ids)
    
    failed_match_ids = list(set(failed_match_ids))
    
    logger.info(f"Found {len(failed_match_ids)} failed match IDs in {error_summary_file}")
    return failed_match_ids


def main():
    parser = argparse.ArgumentParser(
        description='Retry fetching failed match IDs from previous collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Retry specific match IDs
  python scripts/retry_failed_matches.py --match-ids LA2_123456 LA2_789012
  
  # Retry from collection data file
  python scripts/retry_failed_matches.py --from-file data/raw/tft_collection_20251116.json
  
  # Retry from error summary
  python scripts/retry_failed_matches.py --from-error-summary error_summary.json
  
  # Save results to specific file
  python scripts/retry_failed_matches.py --match-ids LA2_123456 --output retry_results.json
        """
    )
    
    parser.add_argument(
        '--match-ids',
        nargs='+',
        help='List of match IDs to retry'
    )
    
    parser.add_argument(
        '--from-file',
        help='Extract failed match IDs from a collection data file'
    )
    
    parser.add_argument(
        '--from-error-summary',
        help='Extract failed match IDs from an error summary file'
    )
    
    parser.add_argument(
        '--output',
        default=None,
        help='Output file for retry results (default: retry_results_TIMESTAMP.json)'
    )
    
    parser.add_argument(
        '--api-key',
        help='Riot API key (default: from RIOT_API_KEY environment variable)'
    )
    
    parser.add_argument(
        '--key-type',
        default='personal',
        choices=['personal', 'production', 'development'],
        help='API key type (default: personal)'
    )
    
    args = parser.parse_args()
    
    match_ids = []
    
    if args.match_ids:
        match_ids = args.match_ids
    elif args.from_file:
        match_ids = extract_failed_match_ids_from_file(args.from_file)
    elif args.from_error_summary:
        match_ids = extract_failed_match_ids_from_error_summary(args.from_error_summary)
    else:
        parser.error("Must provide either --match-ids, --from-file, or --from-error-summary")
    
    if not match_ids:
        logger.warning("No failed match IDs found to retry")
        return
    
    api_key = args.api_key or os.getenv('RIOT_API_KEY')
    if not api_key:
        logger.error("API key required. Set RIOT_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    collector = MatchRetryCollector(api_key, args.key_type)
    
    results = collector.retry_match_ids(match_ids)
    
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/retry/retry_results_{timestamp}.json"
    
    collector.save_retry_results(results, output_file)
    
    if results['retry_stats']['failed'] > 0:
        logger.warning(f"[WARNING] {results['retry_stats']['failed']} matches still failed after retry")
        sys.exit(1)
    else:
        logger.info("[SUCCESS] All matches successfully retried!")
        sys.exit(0)


if __name__ == '__main__':
    import os
    main()

