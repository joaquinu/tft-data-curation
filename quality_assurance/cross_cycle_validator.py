"""
Cross-Cycle Validator Module

Validates data consistency and quality across multiple collection cycles.
Identifies trends, anomalies, and structural shifts between data collections.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

class CrossCycleValidator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.collections: List[Dict[str, Any]] = []
        
    def load_collections(self, pattern: str = "tft_*collection_*.json", limit: int = 10):
        """
        Load recent collection files for comparison.
        
        Args:
            pattern: File pattern to match
            limit: Maximum number of recent files to load
        """
        files = sorted(list(self.output_dir.glob(pattern)), reverse=True)[:limit]
        
        if not files:
            logger.warning(f"No collection files found in {self.output_dir} matching {pattern}")
            return
            
        logger.info(f"Loading {len(files)} collection files for cross-cycle validation")
        
        self.collections = []
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Add filename/date metadata if not present
                    if 'meta_filename' not in data:
                        data['meta_filename'] = file_path.name
                    self.collections.append(data)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {str(e)}")
                
        # Sort by extraction timestamp
        self.collections.sort(key=lambda x: x.get('extractionTimestamp', ''))
        
    def extract_cycle_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from a single collection cycle."""
        # Extract timestamp from filename if not present
        timestamp = data.get('extractionTimestamp')
        if not timestamp:
            filename = data.get('meta_filename', '')
            # Extract date from filename like tft_collection_20251205.json
            import re
            match = re.search(r'(\d{8})', filename)
            if match:
                timestamp = match.group(1)
        
        metrics = {
            'timestamp': timestamp,
            'filename': data.get('meta_filename'),
            'total_players': len(data.get('players', {})),
            'total_matches': len(data.get('matches', {})),
            'total_static_data': len(data.get('static_data', {})),
            'extraction_duration': 0,
        }
        
        # Calculate rank distribution
        ranks = defaultdict(int)
        for p in data.get('players', {}).values():
            if isinstance(p, dict):
                tier = p.get('tier', 'UNKNOWN')
                ranks[tier] += 1
        metrics['rank_distribution'] = dict(ranks)
        
        # Calculate match types distribution if available
        queue_types = defaultdict(int)
        for m in data.get('matches', {}).values():
            if isinstance(m, dict):
                q_id = m.get('info', {}).get('queue_id', 'UNKNOWN')
                queue_types[q_id] += 1
        metrics['queue_distribution'] = dict(queue_types)
        
        return metrics

    def validate_player_continuity(self) -> Dict[str, Any]:
        """
        Check player retention and churn between cycles.
        Returns metrics on new vs returning players.
        """
        if len(self.collections) < 2:
            return {"status": "insufficient_data", "message": "Need at least 2 cycles"}
            
        continuity_report = []
        
        for i in range(1, len(self.collections)):
            prev = self.collections[i-1]
            curr = self.collections[i]
            
            # Extract timestamps using the helper method (with filename fallback)
            prev_metrics = self.extract_cycle_metrics(prev)
            curr_metrics = self.extract_cycle_metrics(curr)
            
            prev_players = set(prev.get('players', {}).keys())
            curr_players = set(curr.get('players', {}).keys())
            
            retained = prev_players.intersection(curr_players)
            new_players = curr_players - prev_players
            churned = prev_players - curr_players
            
            retention_rate = len(retained) / len(prev_players) if prev_players else 0.0
            
            continuity_report.append({
                'from_cycle': prev_metrics['timestamp'],
                'to_cycle': curr_metrics['timestamp'],
                'retained_count': len(retained),
                'new_count': len(new_players),
                'churned_count': len(churned),
                'retention_rate': retention_rate
            })
            
        return {"continuity_trends": continuity_report}

    def validate_volume_stability(self, threshold_pct: float = 0.50) -> Dict[str, Any]:
        """
        Check for sudden drops or spikes in data volume.
        
        Args:
            threshold_pct: Percentage change to trigger a warning (0.50 = 50%)
        """
        if len(self.collections) < 2:
            return {"status": "insufficient_data"}
            
        issues = []
        trends = []
        
        for i in range(1, len(self.collections)):
            prev = self.extract_cycle_metrics(self.collections[i-1])
            curr = self.extract_cycle_metrics(self.collections[i])
            
            # Check match volume
            prev_matches = prev['total_matches']
            curr_matches = curr['total_matches']
            
            if prev_matches > 0:
                pct_change = (curr_matches - prev_matches) / prev_matches
                trends.append({'cycle': curr['timestamp'], 'match_volume_change': pct_change})
                
                if abs(pct_change) > threshold_pct:
                    issues.append({
                        'type': 'volume_anomaly',
                        'metric': 'matches',
                        'prev_value': prev_matches,
                        'curr_value': curr_matches,
                        'change_pct': pct_change,
                        'cycle': curr['timestamp']
                    })
            
            # Check player volume
            prev_players = prev['total_players']
            curr_players = curr['total_players']
            
            if prev_players > 0:
                pct_change = (curr_players - prev_players) / prev_players
                
                if abs(pct_change) > threshold_pct:
                    issues.append({
                        'type': 'volume_anomaly',
                        'metric': 'players',
                        'prev_value': prev_players,
                        'curr_value': curr_players,
                        'change_pct': pct_change,
                        'cycle': curr['timestamp']
                    })
                    
        return {
            "volume_issues": issues,
            "volume_trends": trends
        }

    def generate_cross_cycle_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report on cross-cycle data quality."""
        if not self.collections:
            self.load_collections()
            
        if not self.collections:
            return {"error": "No data loaded"}
            
        report = {
            "timestamp": datetime.now().isoformat(),
            "cycles_analyzed": len(self.collections),
            "date_range": {
                "start": self.collections[0].get('extractionTimestamp'),
                "end": self.collections[-1].get('extractionTimestamp')
            },
            "metrics_summary": [self.extract_cycle_metrics(c) for c in self.collections],
            "continuity_analysis": self.validate_player_continuity(),
            "stability_analysis": self.validate_volume_stability()
        }
        
        return report

def run_validation(output_dir: str = "output", report_file: str = None):
    """Helper function to run validation and optionally save report."""
    validator = CrossCycleValidator(output_dir)
    report = validator.generate_cross_cycle_report()
    
    if report_file:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
    return report
