"""
This module contains all the Riot Games API endpoint implementations for TFT data collection.
Organized by API category for better maintainability and documentation.
"""

import requests
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RiotAPIEndpoints:
    """
    Mixin class containing all Riot API endpoint implementations for TFT.
    This class provides organized access to all TFT-related API endpoints.
    """
    
    # ACCOUNT & SUMMONER DATA
    
    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> Optional[Dict]:
        """Get account information by Riot ID"""
        url = f"https://{self.regional_host}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return self._make_request(url)
    
    def get_account_by_puuid(self, puuid: str) -> Optional[Dict]:
        """Get account information by PUUID"""
        url = f"https://{self.regional_host}/riot/account/v1/accounts/by-puuid/{puuid}"
        return self._make_request(url)
    
    def get_summoner_by_puuid(self, puuid: str) -> Optional[Dict]:
        """Get summoner information by PUUID"""
        url = f"https://{self.platform_host}/tft/summoner/v1/summoners/by-puuid/{puuid}"
        return self._make_request(url)
    
    def get_summoner_by_name(self, summoner_name: str) -> Optional[Dict]:
        """Get summoner information by name"""
        url = f"https://{self.platform_host}/tft/summoner/v1/summoners/by-name/{summoner_name}"
        return self._make_request(url)
    
    def get_summoner_by_id(self, summoner_id: str) -> Optional[Dict]:
        """Get summoner information by summoner ID (encrypted summoner ID)"""
        url = f"https://{self.platform_host}/tft/summoner/v1/summoners/{summoner_id}"
        return self._make_request(url)
    
    # LEAGUE/RANKED DATA
    
    def get_challenger_league(self, queue: str = "RANKED_TFT") -> Optional[Dict]:
        """Get challenger league data"""
        url = f"https://{self.platform_host}/tft/league/v1/challenger"
        return self._make_request(url, params={"queue": queue})
    
    def get_grandmaster_league(self, queue: str = "RANKED_TFT") -> Optional[Dict]:
        """Get grandmaster league data"""
        url = f"https://{self.platform_host}/tft/league/v1/grandmaster"
        return self._make_request(url, params={"queue": queue})
    
    def get_master_league(self, queue: str = "RANKED_TFT") -> Optional[Dict]:
        """Get master league data"""
        url = f"https://{self.platform_host}/tft/league/v1/master"
        return self._make_request(url, params={"queue": queue})
    
    def get_league_entries_by_summoner(self, summoner_id: str) -> Optional[List[Dict]]:
        """Get league entries for a summoner"""
        url = f"https://{self.platform_host}/tft/league/v1/entries/by-summoner/{summoner_id}"
        return self._make_request(url)
    
    def get_league_entries_by_puuid(self, puuid: str) -> Optional[List[Dict]]:
        """Get league entries in all queues for a given PUUID"""
        url = f"https://{self.platform_host}/tft/league/v1/by-puuid/{puuid}"
        return self._make_request(url)
    
    def get_league_entries_by_tier(self, tier: str, division: str, page: int = 1) -> Optional[List[Dict]]:
        """Get all league entries for a specific tier and division"""
        url = f"https://{self.platform_host}/tft/league/v1/entries/{tier}/{division}"
        return self._make_request(url, params={"page": page})
    
    # MATCH DATA
    
    def get_match_ids_by_puuid(self, puuid: str, start: int = 0, count: int = 20, 
                              start_time: Optional[int] = None, end_time: Optional[int] = None) -> Optional[List[str]]:
        """Get match IDs for a player with optional time filtering"""
        url = f"https://{self.regional_host}/tft/match/v1/matches/by-puuid/{puuid}/ids"
        params = {"start": start, "count": count}
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
            
        return self._make_request(url, params)
    
    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed match information"""
        url = f"https://{self.regional_host}/tft/match/v1/matches/{match_id}"
        return self.requester.make_request(url, timeout=60)
    
    # SPECTATOR DATA
    
    def get_active_game_by_summoner(self, summoner_id: str) -> Optional[Dict]:
        """Get current game information for a summoner"""
        url = f"https://{self.platform_host}/tft/spectator/v5/active-games/by-summoner/{summoner_id}"
        return self._make_request(url)
    
    def get_featured_games(self) -> Optional[Dict]:
        """Get list of current featured games"""
        url = f"https://{self.platform_host}/tft/spectator/v5/featured-games"
        return self._make_request(url)
    
    # STATUS DATA
    
    def get_platform_status(self) -> Optional[Dict]:
        """Get platform status information"""
        url = f"https://{self.platform_host}/tft/status/v1/platform-data"
        return self._make_request(url)
    
    # STATIC DATA (DATA DRAGON)
    
    def get_data_dragon_versions(self) -> Optional[List[str]]:
        """Get available Data Dragon versions"""
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None
    
    def get_static_data(self, version: str = None) -> Dict[str, Any]:
        """Get all TFT static data"""
        if not version:
            versions = self.get_data_dragon_versions()
            version = versions[0] if versions else "15.15.1"
        
        base_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US"
        static_data = {}
        
        data_types = [
            "tft-champion",
            "tft-item", 
            "tft-trait",
            "tft-augments",
            "tft-tactician",
            "tft-queues",
            "tft-regalia",
            "tft-arena"
        ]
        
        for data_type in data_types:
            try:
                url = f"{base_url}/{data_type}.json"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    static_data[data_type] = response.json()
                    logger.info(f"Successfully fetched {data_type} data")
                else:
                    logger.warning(f"Failed to fetch {data_type}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching {data_type}: {e}")
        
        return static_data


# API ENDPOINT DOCUMENTATION

API_ENDPOINTS_DOCUMENTATION = {
    "account_summoner": {
        "endpoints": [
            "/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}",
            "/riot/account/v1/accounts/by-puuid/{puuid}",
            "/tft/summoner/v1/summoners/by-puuid/{encryptedPUUID}",
            "/tft/summoner/v1/summoners/by-name/{summonerName}"
        ],
        "description": "Account and summoner information retrieval",
        "rate_limits": "Personal API Key: 20 requests/1 second, 100 requests/2 minutes"
    },
    "league_ranked": {
        "endpoints": [
            "/tft/league/v1/challenger",
            "/tft/league/v1/grandmaster", 
            "/tft/league/v1/master",
            "/tft/league/v1/entries/by-summoner/{encryptedSummonerId}",
            "/tft/league/v1/entries/{tier}/{division}"
        ],
        "description": "Ranked league information and leaderboards",
        "rate_limits": "Personal API Key: 20 requests/1 second, 100 requests/2 minutes"
    },
    "match_data": {
        "endpoints": [
            "/tft/match/v1/matches/by-puuid/{puuid}/ids",
            "/tft/match/v1/matches/{matchId}"
        ],
        "description": "Match history and detailed match information",
        "rate_limits": "Personal API Key: 20 requests/1 second, 100 requests/2 minutes"
    },
    "spectator": {
        "endpoints": [
            "/tft/spectator/v5/active-games/by-summoner/{encryptedSummonerId}",
            "/tft/spectator/v5/featured-games"
        ],
        "description": "Live game information and featured games",
        "rate_limits": "Personal API Key: 20 requests/1 second, 100 requests/2 minutes"
    },
    "status": {
        "endpoints": [
            "/tft/status/v1/platform-data"
        ],
        "description": "Platform status and maintenance information",
        "rate_limits": "Personal API Key: 20 requests/1 second, 100 requests/2 minutes"
    },
    "static_data": {
        "endpoints": [
            "https://ddragon.leagueoflegends.com/api/versions.json",
            "https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/tft-champion.json",
            "https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/tft-item.json",
            "https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/tft-trait.json"
        ],
        "description": "Static game data from Data Dragon CDN",
        "rate_limits": "No specific limits (CDN hosted)"
    }
}
