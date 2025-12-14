"""
Leaderboard Mixin Module
========================

This module provides shared leaderboard and player collection functionality
"""

import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class LeaderboardMixin:
    """
    Mixin class providing leaderboard collection and player extraction functionality.
    
    Requirements for classes using this mixin:
    - Must have `self.collected_data` dict attribute
    - Must have `self.get_challenger_league()` method
    - Must have `self.get_grandmaster_league()` method  
    - Must have `self.get_master_league()` method
    - Must have `self.get_league_entries_by_tier()` method
    
    These requirements are satisfied by inheriting from BaseAPIInfrastructure
    and RiotAPIEndpoints.
    """
    
    def collect_leaderboard_data(
        self, 
        queue: str = "RANKED_TFT", 
        high_elo_only: bool = False,
        tiers: Optional[List[str]] = None,
        divisions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Collect leaderboard data from ranked leagues.
        
        Args:
            queue: Ranked queue type (default: RANKED_TFT)
            high_elo_only: If True, only collect Challenger/GM/Master/Diamond
            tiers: Optional list of tiers to collect (overrides high_elo_only)
            divisions: Optional list of divisions to collect
            
        Returns:
            Dict containing leaderboard data organized by tier/division
        """
        logger.info("Collecting leaderboard data...")
        
        leaderboards = {}
        
        # Get high elo leagues (Challenger, Grandmaster, Master)
        high_elo_methods = {
            "challenger": self.get_challenger_league,
            "grandmaster": self.get_grandmaster_league,
            "master": self.get_master_league,
        }
        
        for league_type, fetch_method in high_elo_methods.items():
            data = fetch_method(queue)
            if data:
                leaderboards[league_type] = data
                entry_count = len(data.get('entries', []))
                logger.info(f"Found {entry_count} {league_type} players")
        
        # Determine tiers to collect
        if tiers is None:
            if high_elo_only:
                tiers = ["DIAMOND"]
                logger.info("HIGH ELO ONLY MODE - Only collecting Diamond tier")
            else:
                tiers = ["DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]
        
        if divisions is None:
            divisions = ["I", "II", "III", "IV"]
        
        # Collect tier/division data
        for tier in tiers:
            if tier.upper() in ["CHALLENGER", "GRANDMASTER", "MASTER"]:
                continue

            leaderboards[tier] = {}
            for division in divisions:
                data = self.get_league_entries_by_tier(tier, division)
                if data:
                    leaderboards[tier][division] = data
                    logger.info(f"Found {len(data)} players in {tier} {division}")
                time.sleep(0.1)  # Rate limiting courtesy delay
        
        return leaderboards
    
    def get_top_players_puuids(self, target_count: Optional[int] = None) -> List[str]:
        """
        Get PUUIDs of top players from all tiers until target count is reached.
        
        Args:
            target_count: Number of top players to collect. 
                          If None, collects all available players.
            
        Returns:
            List of PUUIDs sorted by rank (best to worst)
        """
        if target_count is None:
            logger.info("Collecting PUUIDs for ALL available players (no limit)...")
        else:
            logger.info(f"Collecting PUUIDs for top {target_count} players...")
        
        top_players = []
        
        # Ensure leaderboard data is collected
        if "leaderboards" not in self.collected_data:
            self.collected_data["leaderboards"] = self.collect_leaderboard_data(high_elo_only=True)
        
        leaderboards = self.collected_data["leaderboards"]
        
        # Extract players from high elo leagues
        top_players.extend(
            self._extract_high_elo_players(leaderboards, target_count)
        )
        
        # If we need more players, get from lower tiers
        if target_count is None or len(top_players) < target_count:
            remaining = None if target_count is None else target_count - len(top_players)
            if remaining:
                logger.info(f"Need {remaining} more players, collecting from Diamond and below...")
            else:
                logger.info("Collecting all players from Diamond and below...")
            
            top_players.extend(
                self._extract_tier_players(leaderboards, remaining, len(top_players))
            )
        
        # Sort by priority (tier) and then by LP (descending)
        top_players.sort(key=lambda x: (x["priority"], -x["leaguePoints"]))
        
        # Extract PUUIDs, limited to target count
        if target_count is None:
            puuids = [player["puuid"] for player in top_players]
        else:
            puuids = [player["puuid"] for player in top_players[:target_count]]
        
        logger.info(f"Collected {len(puuids)} player PUUIDs")
        return puuids
    
    def _extract_high_elo_players(
        self, 
        leaderboards: Dict[str, Any], 
        target_count: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Extract player data from high elo leagues (Challenger, GM, Master).
        
        Args:
            leaderboards: Leaderboard data dict
            target_count: Maximum players to extract (None = no limit)
            
        Returns:
            List of player data dicts
        """
        players = []
        priority_map = {"challenger": 1, "grandmaster": 2, "master": 3}
        
        for league_type in ["challenger", "grandmaster", "master"]:
            if league_type not in leaderboards:
                continue
                
            entries = leaderboards[league_type].get("entries", [])
            for entry in entries:
                if target_count is not None and len(players) >= target_count:
                    break
                
                puuid = entry.get("puuid")
                if not puuid:
                    logger.warning(f"Entry missing PUUID, skipping: {entry.get('summonerId', 'unknown')}")
                    continue
                
                players.append({
                    "puuid": puuid,
                    "summonerId": entry.get("summonerId", ""),
                    "summonerName": entry.get("summonerName", ""),
                    "leaguePoints": entry.get("leaguePoints", 0),
                    "tier": league_type.upper(),
                    "rank": entry.get("rank", "I"),
                    "priority": priority_map[league_type]
                })
            
            if target_count is not None and len(players) >= target_count:
                break
        
        return players
    
    def _extract_tier_players(
        self, 
        leaderboards: Dict[str, Any], 
        remaining_count: Optional[int],
        current_count: int
    ) -> List[Dict[str, Any]]:
        """
        Extract player data from tier/division leagues (Diamond and below).
        
        Args:
            leaderboards: Leaderboard data dict
            remaining_count: Maximum additional players to extract (None = no limit)
            current_count: Current number of players already collected
            
        Returns:
            List of player data dicts
        """
        players = []
        tiers = ["DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE"]
        divisions = ["I", "II", "III", "IV"]
        priority_map = {"DIAMOND": 4, "PLATINUM": 5, "GOLD": 6, "SILVER": 7, "BRONZE": 8}
        
        for tier in tiers:
            if remaining_count is not None and len(players) >= remaining_count:
                break
            
            if tier not in leaderboards:
                continue
            
            for division in divisions:
                if remaining_count is not None and len(players) >= remaining_count:
                    break
                
                if division not in leaderboards[tier]:
                    continue
                
                entries = leaderboards[tier][division]
                for entry in entries:
                    if remaining_count is not None and len(players) >= remaining_count:
                        break
                    
                    puuid = entry.get("puuid")
                    if not puuid:
                        logger.warning(f"Entry missing PUUID, skipping: {entry.get('summonerId', 'unknown')}")
                        continue
                    
                    players.append({
                        "puuid": puuid,
                        "summonerId": entry.get("summonerId", ""),
                        "summonerName": entry.get("summonerName", ""),
                        "leaguePoints": entry.get("leaguePoints", 0),
                        "tier": tier,
                        "rank": division,
                        "priority": priority_map.get(tier, 6)
                    })
        
        return players
