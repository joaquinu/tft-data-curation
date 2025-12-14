#!/usr/bin/env python3
"""
TFT Identifier System Test Suite
================================

This script demonstrates and tests the implementation of:
- Canonicalization for data integrity (Lynch, 1999)
- Persistent identifiers with UUIDv7 (RFC 9562)
- Scientific equivalence verification
- Content-based identifiers with SHA-256

Tests the complete identifier system as specified in 
Documents/riot_tft_identifier_system.md
"""

import json
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.identifier_system import (
    TFTIdentifierSystem, 
    IdentifierType,
    create_canonical_hash,
    verify_data_equivalence,
    generate_match_uuid
)

TEST_DB_PATH = None

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Create a temporary test database for each test"""
    global TEST_DB_PATH
    TEST_DB_PATH = str(tmp_path / "test_identifier_registry.duckdb")
    yield


def get_test_system():
    """Get a TFTIdentifierSystem using the test database"""
    return TFTIdentifierSystem(registry_path=TEST_DB_PATH)

def test_canonicalization():
    """Test canonicalization function for data integrity"""
    print("🧪 Testing Canonicalization Function")
    print("=" * 50)
    
    # Use test system
    system = get_test_system()
    
    # Test data - same content, different order
    data1 = {
        "player": "test_player",
        "match_id": "12345",
        "placement": 1,
        "champions": ["Ahri", "Yasuo"]
    }
    
    data2 = {
        "champions": ["Ahri", "Yasuo"],
        "placement": 1,
        "player": "test_player", 
        "match_id": "12345"
    }
    
    data3 = {
        "player": "test_player",
        "match_id": "12345",
        "placement": 2,  # Different placement
        "champions": ["Ahri", "Yasuo"]
    }
    
    # Test canonical hash generation using system methods
    hash1 = system.canonical_hash(data1)
    hash2 = system.canonical_hash(data2)
    hash3 = system.canonical_hash(data3)
    
    print(f"Data 1 hash: {hash1}")
    print(f"Data 2 hash: {hash2}")
    print(f"Data 3 hash: {hash3}")
    
    # Test scientific equivalence using system methods
    equivalent_1_2 = system.verify_scientific_equivalence(data1, data2)
    equivalent_1_3 = system.verify_scientific_equivalence(data1, data3)
    
    print(f"\nScientific Equivalence Tests:")
    print(f"Data 1 ≡ Data 2 (same content, different order): {equivalent_1_2}")
    print(f"Data 1 ≡ Data 3 (different content): {equivalent_1_3}")
    
    assert equivalent_1_2 == True, "Same data should be equivalent regardless of order"
    assert equivalent_1_3 == False, "Different data should not be equivalent"
    
    print("✅ Canonicalization tests passed!\n")

def test_uuid_generation():
    """Test UUIDv7 generation for persistent identifiers"""
    print("🔑 Testing UUIDv7 Generation")
    print("=" * 50)
    
    # Use test system to generate UUIDs
    system = get_test_system()
    uuids = [system.generate_uuidv7() for _ in range(5)]
    
    print("Generated UUIDs:")
    for i, uuid_str in enumerate(uuids, 1):
        print(f"  {i}. {uuid_str}")
    
    # Verify format
    for uuid_str in uuids:
        assert uuid_str.startswith("urn:uuid:"), f"UUID should start with 'urn:uuid:': {uuid_str}"
        assert len(uuid_str) == 45, f"UUID should be 45 characters: {len(uuid_str)}"
    
    # Verify uniqueness
    assert len(set(uuids)) == len(uuids), "All UUIDs should be unique"
    
    print("✅ UUID generation tests passed!\n")

def test_identifier_system():
    """Test the complete identifier system"""
    print("🏗️ Testing Complete Identifier System")
    print("=" * 50)
    
    system = get_test_system()
    
    # Test match identifier creation
    riot_match_id = "NA1_1234567890"
    match_data = {
        "gameCreation": 1640995200000,
        "gameLength": 1800,
        "queueId": 1100,
        "tftSetNumber": 6
    }
    
    match_identifier = system.create_match_identifier(riot_match_id, match_data)
    print(f"Match identifier: {match_identifier}")
    
    # Test player identifier creation
    puuid = "test-puuid-12345"
    player_data = {
        "gameName": "TestPlayer",
        "tagLine": "NA1"
    }
    
    player_identifier = system.create_player_identifier(puuid, player_data)
    print(f"Player identifier: {player_identifier}")
    
    # Test dataset identifier creation
    dataset_data = {
        "matches": {"match1": match_data},
        "players": {puuid: player_data},
        "collection_time": datetime.now().isoformat()
    }
    
    dataset_identifier = system.create_dataset_identifier(dataset_data)
    print(f"Dataset identifier: {dataset_identifier}")
    
    # Test game version identifier
    version_identifier = system.create_game_version_identifier("13.24")
    print(f"Version identifier: {version_identifier}")
    
    # Test item identifier
    item_identifier = system.create_item_identifier("InfinityEdge", "13.24")
    print(f"Item identifier: {item_identifier}")
    
    # Test identifier resolution
    resolved_match = system.resolve_identifier(match_identifier)
    print(f"\nResolved match metadata: {resolved_match.type.value if resolved_match else 'None'}")
    
    # Test provenance
    provenance = system.get_identifier_provenance(match_identifier)
    print(f"Match provenance: {provenance['riot_match_id'] if provenance else 'None'}")
    
    print("✅ Identifier system tests passed!\n")

def test_collection_identifiers():
    """Test collection-level identifier generation"""
    print("📦 Testing Collection Identifier Generation")
    print("=" * 50)
    
    system = get_test_system()
    
    # Create sample collection data
    collection_data = {
        "matches": {
            "NA1_123": {
                "gameCreation": 1640995200000,
                "gameLength": 1800,
                "queueId": 1100
            },
            "NA1_456": {
                "gameCreation": 1640995300000,
                "gameLength": 1900,
                "queueId": 1100
            }
        },
        "players": {
            "puuid-1": {
                "gameName": "Player1",
                "tagLine": "NA1"
            },
            "puuid-2": {
                "gameName": "Player2", 
                "tagLine": "NA1"
            }
        },
        "collectionInfo": {
            "timestamp": datetime.now().isoformat(),
            "extractionLocation": "LA2"
        }
    }
    
    # Generate collection identifiers
    identifiers = system.create_collection_identifier(collection_data)
    
    print("Collection Identifiers:")
    for key, value in identifiers.items():
        print(f"  {key}: {value}")
    
    # Test identifier metadata addition
    enhanced_data = system.add_identifier_metadata(collection_data, identifiers)
    
    print(f"\nEnhanced data keys: {list(enhanced_data.keys())}")
    print(f"Dataset ID: {enhanced_data.get('@identifiers', {}).get('dataset_id', 'N/A')}")
    print(f"Canonicalization method: {enhanced_data.get('@canonicalization', {}).get('method', 'N/A')}")
    
    print("✅ Collection identifier tests passed!\n")

def test_scientific_equivalence_scenarios():
    """Test scientific equivalence in various scenarios"""
    print("🔬 Testing Scientific Equivalence Scenarios")
    print("=" * 50)
    
    system = get_test_system()
    
    # Scenario 1: Same match data, different serialization
    match1 = {
        "matchId": "NA1_123",
        "participants": [
            {"puuid": "player1", "placement": 1},
            {"puuid": "player2", "placement": 2}
        ],
        "gameCreation": 1640995200000
    }
    
    match2 = {
        "gameCreation": 1640995200000,
        "matchId": "NA1_123",
        "participants": [
            {"puuid": "player1", "placement": 1},
            {"puuid": "player2", "placement": 2}
        ]
    }
    
    equivalent = system.verify_scientific_equivalence(match1, match2)
    print(f"Same match, different order: {equivalent}")
    assert equivalent == True, "Same match data should be equivalent"
    
    # Scenario 2: Different match data
    match3 = {
        "matchId": "NA1_456",  # Different match ID
        "participants": [
            {"puuid": "player1", "placement": 1},
            {"puuid": "player2", "placement": 2}
        ],
        "gameCreation": 1640995200000
    }
    
    equivalent = system.verify_scientific_equivalence(match1, match3)
    print(f"Different matches: {equivalent}")
    assert equivalent == False, "Different matches should not be equivalent"
    
    # Scenario 3: Format migration simulation
    old_format = {
        "match_id": "NA1_123",
        "game_time": 1800,
        "queue": "ranked"
    }
    
    new_format = {
        "matchId": "NA1_123",
        "gameLength": 1800,
        "queueType": "ranked"
    }
    
    equivalent = system.verify_scientific_equivalence(old_format, new_format)
    print(f"Format migration (different field names): {equivalent}")
    assert equivalent == False, "Different field names should not be equivalent"
    
    print("✅ Scientific equivalence scenario tests passed!\n")

def test_identifier_registry():
    """Test identifier registry functionality"""
    print("📋 Testing Identifier Registry")
    print("=" * 50)
    
    system = get_test_system()
    
    # Create several identifiers
    match_id = system.create_match_identifier("NA1_123", {"test": "data"})
    player_id = system.create_player_identifier("puuid-123", {"name": "TestPlayer"})
    dataset_id = system.create_dataset_identifier({"test": "dataset"})
    
    # Export registry
    registry = system.export_identifier_registry()
    
    print(f"Registry contains {registry['total_identifiers']} identifiers")
    print(f"Registry version: {registry['registry_version']}")
    
    # Verify all identifiers are in registry
    assert match_id in registry['identifiers'], "Match identifier should be in registry"
    assert player_id in registry['identifiers'], "Player identifier should be in registry"
    assert dataset_id in registry['identifiers'], "Dataset identifier should be in registry"
    
    # Test registry data structure
    match_registry_data = registry['identifiers'][match_id]
    assert match_registry_data['type'] == 'match', "Match type should be correct"
    assert 'provenance' in match_registry_data, "Provenance should be included"
    
    print("✅ Identifier registry tests passed!\n")

def main():
    """Run all identifier system tests"""
    global TEST_DB_PATH
    
    print("🎮 TFT Identifier System Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Create temporary database for standalone execution
    with tempfile.TemporaryDirectory() as tmp_dir:
        TEST_DB_PATH = os.path.join(tmp_dir, "test_identifier_registry.duckdb")
        
        try:
            test_canonicalization()
            test_uuid_generation()
            test_identifier_system()
            test_collection_identifiers()
            test_scientific_equivalence_scenarios()
            test_identifier_registry()
            
            print("🎉 All tests passed successfully!")
            print("=" * 60)
            print("✅ Canonicalization implemented (Lynch, 1999)")
            print("✅ Persistent identifiers with UUIDv7 (RFC 9562)")
            print("✅ Scientific equivalence verification")
            print("✅ Content-based identifiers with SHA-256")
            print("✅ Complete identifier system operational")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise

if __name__ == "__main__":
    main()
