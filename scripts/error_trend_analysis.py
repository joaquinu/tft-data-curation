#!/usr/bin/env python3
"""
Error Trend Analysis Script

Analyzes error trends across collection cycles to identify recurring API failures,
rate limit issues, and system health patterns.

Usage:
    python3 scripts/error_trend_analysis.py --log-dir logs --output reports/error_trends_20251101.json --days 7
"""

import argparse
import json
import re
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional


# Error categories and their patterns
ERROR_PATTERNS = {
    'rate_limit': [
        r'rate.?limit',
        r'429',
        r'too many requests',
        r'throttl',
    ],
    'api_connection': [
        r'connection.?(error|failed|refused|timeout)',
        r'connect.?timeout',
        r'network.?error',
        r'socket.?error',
        r'ConnectionError',
        r'TimeoutError',
    ],
    'api_response': [
        r'api.?(error|failed)',
        r'invalid.?response',
        r'unexpected.?response',
        r'status.?code.?[45]\d{2}',
        r'HTTPError',
    ],
    'authentication': [
        r'auth.?(error|failed)',
        r'401',
        r'403',
        r'unauthorized',
        r'forbidden',
        r'invalid.?api.?key',
        r'token.?expir',
    ],
    'data_validation': [
        r'validation.?(error|failed)',
        r'invalid.?data',
        r'missing.?field',
        r'schema.?error',
        r'type.?error',
    ],
    'match_fetch': [
        r'failed.?to.?(fetch|get).?match',
        r'match.?not.?found',
        r'match.?id.?invalid',
    ],
    'player_fetch': [
        r'failed.?to.?(fetch|get).?player',
        r'puuid.?not.?found',
        r'summoner.?not.?found',
    ],
    'general_error': [
        r'\[ERROR\]',
        r'Exception',
        r'Traceback',
        r'failed:',
    ],
}

# Warning patterns
WARNING_PATTERNS = {
    'performance': [
        r'slow',
        r'performance',
        r'taking.?long',
    ],
    'data_quality': [
        r'missing',
        r'incomplete',
        r'empty.?response',
    ],
    'retry': [
        r'retry',
        r'retrying',
        r'attempt',
    ],
}


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a log line into structured data."""
    # Expected format: 2025-11-01 12:30:45,123 - LoggerName - LEVEL - Message
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},?\d*)\s*-\s*(\S+)\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*(.*)$'
    match = re.match(pattern, line.strip())
    
    if match:
        timestamp_str = match.group(1).replace(',', '.')
        try:
            # Try parsing with milliseconds
            timestamp = datetime.strptime(timestamp_str[:23], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                # Try without milliseconds
                timestamp = datetime.strptime(timestamp_str[:19], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
        
        return {
            'timestamp': timestamp,
            'logger': match.group(2),
            'level': match.group(3),
            'message': match.group(4),
        }
    
    return None


def categorize_error(message: str) -> List[str]:
    """Categorize an error message based on patterns."""
    categories = []
    message_lower = message.lower()
    
    for category, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                if category not in categories:
                    categories.append(category)
                break
    
    return categories if categories else ['uncategorized']


def categorize_warning(message: str) -> List[str]:
    """Categorize a warning message based on patterns."""
    categories = []
    message_lower = message.lower()
    
    for category, patterns in WARNING_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                if category not in categories:
                    categories.append(category)
                break
    
    return categories if categories else ['general']


def analyze_log_file(filepath: Path, cutoff_date: datetime) -> Dict[str, Any]:
    """Analyze a single log file for errors and warnings."""
    results = {
        'file': str(filepath),
        'errors': [],
        'warnings': [],
        'error_counts': defaultdict(int),
        'warning_counts': defaultdict(int),
        'lines_processed': 0,
        'lines_parsed': 0,
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                results['lines_processed'] += 1
                parsed = parse_log_line(line)
                
                if not parsed:
                    continue
                
                results['lines_parsed'] += 1
                
                # Skip entries before cutoff date
                if parsed['timestamp'] < cutoff_date:
                    continue
                
                if parsed['level'] == 'ERROR' or parsed['level'] == 'CRITICAL':
                    categories = categorize_error(parsed['message'])
                    error_entry = {
                        'timestamp': parsed['timestamp'].isoformat(),
                        'logger': parsed['logger'],
                        'message': parsed['message'][:500],  # Truncate long messages
                        'categories': categories,
                    }
                    results['errors'].append(error_entry)
                    for cat in categories:
                        results['error_counts'][cat] += 1
                
                elif parsed['level'] == 'WARNING':
                    categories = categorize_warning(parsed['message'])
                    warning_entry = {
                        'timestamp': parsed['timestamp'].isoformat(),
                        'logger': parsed['logger'],
                        'message': parsed['message'][:500],
                        'categories': categories,
                    }
                    results['warnings'].append(warning_entry)
                    for cat in categories:
                        results['warning_counts'][cat] += 1
    
    except Exception as e:
        results['parse_error'] = str(e)
    
    # Convert defaultdicts to regular dicts for JSON serialization
    results['error_counts'] = dict(results['error_counts'])
    results['warning_counts'] = dict(results['warning_counts'])
    
    return results


def compute_trends(all_results: List[Dict], days: int) -> Dict[str, Any]:
    """Compute error trends across all analyzed files."""
    # Aggregate all errors by date
    errors_by_date = defaultdict(lambda: defaultdict(int))
    warnings_by_date = defaultdict(lambda: defaultdict(int))
    
    for result in all_results:
        for error in result.get('errors', []):
            try:
                date = error['timestamp'][:10]  # Extract YYYY-MM-DD
                for cat in error['categories']:
                    errors_by_date[date][cat] += 1
            except (KeyError, IndexError):
                continue
        
        for warning in result.get('warnings', []):
            try:
                date = warning['timestamp'][:10]
                for cat in warning['categories']:
                    warnings_by_date[date][cat] += 1
            except (KeyError, IndexError):
                continue
    
    # Convert to sorted list
    error_trend = []
    for date in sorted(errors_by_date.keys()):
        error_trend.append({
            'date': date,
            'counts': dict(errors_by_date[date]),
            'total': sum(errors_by_date[date].values()),
        })
    
    warning_trend = []
    for date in sorted(warnings_by_date.keys()):
        warning_trend.append({
            'date': date,
            'counts': dict(warnings_by_date[date]),
            'total': sum(warnings_by_date[date].values()),
        })
    
    # Compute trend direction
    trend_direction = 'stable'
    if len(error_trend) >= 2:
        recent_avg = sum(e['total'] for e in error_trend[-3:]) / min(3, len(error_trend))
        older_avg = sum(e['total'] for e in error_trend[:-3]) / max(1, len(error_trend) - 3) if len(error_trend) > 3 else recent_avg
        
        if recent_avg > older_avg * 1.5:
            trend_direction = 'increasing'
        elif recent_avg < older_avg * 0.5:
            trend_direction = 'decreasing'
    
    return {
        'error_trend': error_trend,
        'warning_trend': warning_trend,
        'trend_direction': trend_direction,
        'analysis_period_days': days,
    }


def generate_recommendations(aggregated: Dict, trends: Dict) -> List[Dict[str, str]]:
    """Generate recommendations based on error analysis."""
    recommendations = []
    
    total_errors = aggregated['total_error_categories']
    
    # Rate limiting issues
    if total_errors.get('rate_limit', 0) > 5:
        recommendations.append({
            'priority': 'high',
            'category': 'rate_limit',
            'recommendation': 'Frequent rate limit errors detected. Consider reducing request frequency or implementing exponential backoff.',
            'action': 'Review rate_limiting.py configuration and increase sleep intervals between API calls.',
        })
    
    # Authentication issues
    if total_errors.get('authentication', 0) > 0:
        recommendations.append({
            'priority': 'critical',
            'category': 'authentication',
            'recommendation': 'Authentication errors detected. API key may be expired or invalid.',
            'action': 'Regenerate API key at developer.riotgames.com and update RIOT_API_KEY environment variable.',
        })
    
    # Connection issues
    if total_errors.get('api_connection', 0) > 3:
        recommendations.append({
            'priority': 'medium',
            'category': 'api_connection',
            'recommendation': 'Multiple connection errors detected. Network connectivity may be unstable.',
            'action': 'Check network configuration and consider implementing retry logic with longer timeouts.',
        })
    
    # Data validation issues
    if total_errors.get('data_validation', 0) > 5:
        recommendations.append({
            'priority': 'medium',
            'category': 'data_validation',
            'recommendation': 'Data validation errors suggest API response format may have changed.',
            'action': 'Review schema.py and data_validator.py for compatibility with current API responses.',
        })
    
    # Match fetch issues
    if total_errors.get('match_fetch', 0) > 10:
        recommendations.append({
            'priority': 'low',
            'category': 'match_fetch',
            'recommendation': 'Some matches could not be fetched. This may be normal for very old or deleted matches.',
            'action': 'Review retry_failed_matches.py output and consider filtering out matches older than 7 days.',
        })
    
    # Trend-based recommendations
    if trends.get('trend_direction') == 'increasing':
        recommendations.append({
            'priority': 'high',
            'category': 'trend',
            'recommendation': 'Error rate is increasing over time. System health may be degrading.',
            'action': 'Investigate recent changes to the collection pipeline and API availability.',
        })
    
    # No issues
    if not recommendations:
        recommendations.append({
            'priority': 'info',
            'category': 'health',
            'recommendation': 'No significant issues detected. System appears healthy.',
            'action': 'Continue monitoring with regular error trend analysis.',
        })
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(
        description='Analyze error trends across collection cycles'
    )
    parser.add_argument(
        '--log-dir', 
        default='logs',
        help='Directory containing log files (default: logs)'
    )
    parser.add_argument(
        '--output', 
        default=None,
        help='Output file path for JSON report (default: reports/error_trends_YYYYMMDD.json)'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=7,
        help='Number of days to analyze (default: 7)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Warning: Log directory '{log_dir}' does not exist. Creating empty report.")
        log_files = []
    else:
        # Find all log files
        log_files = list(log_dir.glob('*.log')) + list(log_dir.glob('**/*.log'))
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=args.days)
    
    print(f"=" * 60)
    print(f"📊 TFT ERROR TREND ANALYSIS")
    print(f"=" * 60)
    print(f"Log directory: {log_dir}")
    print(f"Analysis period: Last {args.days} days (since {cutoff_date.strftime('%Y-%m-%d')})")
    print(f"Log files found: {len(log_files)}")
    print()
    
    # Analyze each log file
    all_results = []
    total_errors = 0
    total_warnings = 0
    
    for log_file in log_files:
        if args.verbose:
            print(f"  Analyzing: {log_file.name}")
        
        result = analyze_log_file(log_file, cutoff_date)
        all_results.append(result)
        total_errors += len(result.get('errors', []))
        total_warnings += len(result.get('warnings', []))
    
    # Aggregate results
    aggregated = {
        'total_errors': total_errors,
        'total_warnings': total_warnings,
        'total_error_categories': defaultdict(int),
        'total_warning_categories': defaultdict(int),
        'files_analyzed': len(log_files),
    }
    
    for result in all_results:
        for cat, count in result.get('error_counts', {}).items():
            aggregated['total_error_categories'][cat] += count
        for cat, count in result.get('warning_counts', {}).items():
            aggregated['total_warning_categories'][cat] += count
    
    aggregated['total_error_categories'] = dict(aggregated['total_error_categories'])
    aggregated['total_warning_categories'] = dict(aggregated['total_warning_categories'])
    
    # Compute trends
    trends = compute_trends(all_results, args.days)
    
    # Generate recommendations
    recommendations = generate_recommendations(aggregated, trends)
    
    # Build final report
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'analysis_period': {
            'days': args.days,
            'start_date': cutoff_date.isoformat(),
            'end_date': datetime.now().isoformat(),
        },
        'summary': aggregated,
        'trends': trends,
        'recommendations': recommendations,
        'detailed_results': all_results if args.verbose else None,
    }
    
    # Remove None values
    report = {k: v for k, v in report.items() if v is not None}
    
    # Output report
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"reports/error_trends_{datetime.now().strftime('%Y%m%d')}.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print(f"--- Summary ---")
    print(f"Total errors found: {total_errors}")
    print(f"Total warnings found: {total_warnings}")
    print()
    
    if aggregated['total_error_categories']:
        print(f"--- Errors by Category ---")
        for cat, count in sorted(aggregated['total_error_categories'].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        print()
    
    if aggregated['total_warning_categories']:
        print(f"--- Warnings by Category ---")
        for cat, count in sorted(aggregated['total_warning_categories'].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        print()
    
    print(f"--- Trend Analysis ---")
    print(f"Error trend direction: {trends['trend_direction']}")
    print()
    
    print(f"--- Recommendations ---")
    for rec in recommendations:
        priority_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢', 'info': 'ℹ️'}.get(rec['priority'], '•')
        print(f"{priority_icon} [{rec['priority'].upper()}] {rec['category']}")
        print(f"   {rec['recommendation']}")
        print(f"   Action: {rec['action']}")
        print()
    
    print(f"Full report saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
