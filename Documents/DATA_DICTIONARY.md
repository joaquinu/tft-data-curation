# TFT Data Dictionary
Comprehensive field-level documentation for TFT data collection structures

---

## Table of Contents

1. [Overview](#overview)
2. [Data Collection Structure](#data-collection-structure)
3. [Collection Information](#collection-information)
4. [Player Data](#player-data)
5. [Match Data](#match-data)
6. [Participant Data](#participant-data)
7. [Champion/Unit Data](#championunit-data)
8. [Trait Data](#trait-data)
9. [Item Data](#item-data)
10. [Leaderboard Data](#leaderboard-data)
11. [JSON-LD Schema Elements](#json-ld-schema-elements)
12. [Data Type Specifications](#data-type-specifications)
13. [Validation Rules](#validation-rules)
14. [Usage Examples](#usage-examples)

---

## Overview

This data dictionary provides comprehensive documentation for all data structures, fields, and types used in the TFT (Teamfight Tactics) data collection system. The data is structured in JSON format with JSON-LD semantic annotations for enhanced interoperability and analysis.

### Data Format

- **Primary Format**: JSON with JSON-LD context
- **Schema Standard**: W3C JSON-LD, Schema.org compatible
- **Encoding**: UTF-8
- **File Naming**: `tft_weekly_collection_YYYYMMDD_HHMMSS.json` or `tft_incremental_YYYYMMDD_HHMMSS.json`

### Data Structure Hierarchy

```
TFTDataCollection (Root)
├── collectionInfo
├── players (dict: puuid → Player)
├── matches (dict: matchId → Match)
│   └── info
│       └── participants (array)
│           ├── units (array)
│           ├── traits (array)
│           └── augments (array)
└── leaderboards (dict: tier → Leaderboard)
```

---

## Data Collection Structure

### Root Object: TFTDataCollection

The root object contains all collected data with JSON-LD context for semantic annotation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `@context` | object | Yes | JSON-LD context defining vocabulary and namespaces |
| `@type` | string | Yes | Always `"TFTDataCollection"` |
| `extractionTimestamp` | string (ISO 8601) | Yes | UTC timestamp when data was collected |
| `extractionLocation` | string | Yes | Region code (e.g., "LA2", "LA1") |
| `collectionInfo` | object | Yes | Metadata about the collection process |
| `players` | object | Yes | Dictionary of player data keyed by PUUID |
| `matches` | object | Yes | Dictionary of match data keyed by match ID |
| `leaderboards` | object | Optional | Dictionary of leaderboard data by tier |
| `static_data` | object | Optional | Static game data (champions, items, traits) |
| `collection_config` | object | Optional | Configuration used for this collection |

**Example**:
```json
{
  "@context": {
    "@vocab": "http://tft-data-extraction.com/schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "TFTDataCollection",
  "extractionTimestamp": "2025-11-15T22:58:17Z",
  "extractionLocation": "LA2",
  "collectionInfo": { ... },
  "players": { ... },
  "matches": { ... }
}
```

---

## Collection Information

### collectionInfo Object

Metadata about the data collection process and configuration.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `timestamp` | string (ISO 8601) | Yes | Collection start timestamp | `"2025-11-15T22:58:17Z"` |
| `extractionLocation` | string | Yes | API region code | `"LA2"` |
| `dataVersion` | string | Yes | Data schema version | `"1.0"` |
| `apiKey` | string | Optional | API key identifier (hashed) | `"***"` |
| `collectionMethod` | string | Optional | Collection method used | `"weekly"`, `"incremental"` |
| `regionCode` | string | Optional | Region code | `"la2"` |

**Example**:
```json
{
  "collectionInfo": {
    "timestamp": "2025-11-15T22:58:17Z",
    "extractionLocation": "LA2",
    "dataVersion": "1.0",
    "collectionMethod": "weekly",
    "regionCode": "la2"
  }
}
```

---

## Player Data

### Player Object

Individual player information including account details and ranked statistics.

**Location**: `players[puuid]`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `puuid` | string | Yes | Player Unique Identifier (Riot) | `"abc123..."` |
| `summonerId` | string | Yes | Summoner ID | `"xyz789"` |
| `summonerLevel` | integer | Yes | Summoner account level | `150` |
| `tier` | string | Yes | Ranked tier | `"DIAMOND"`, `"PLATINUM"`, etc. |
| `rank` | string | Yes | Division rank | `"I"`, `"II"`, `"III"`, `"IV"` |
| `leaguePoints` | integer | Yes | League Points (LP) | `75` |
| `profileIconId` | integer | Optional | Profile icon ID | `1234` |
| `revisionDate` | integer | Optional | Last profile update (Unix timestamp) | `1699999999000` |
| `riotIdGameName` | string | Optional | Riot ID game name | `"PlayerName"` |
| `riotIdTagline` | string | Optional | Riot ID tagline | `"TAG"` |
| `wins` | integer | Optional | Ranked wins | `45` |
| `losses` | integer | Optional | Ranked losses | `30` |

**Tier Values**: `"IRON"`, `"BRONZE"`, `"SILVER"`, `"GOLD"`, `"PLATINUM"`, `"DIAMOND"`, `"MASTER"`, `"GRANDMASTER"`, `"CHALLENGER"`

**Rank Values**: `"I"`, `"II"`, `"III"`, `"IV"`

**Example**:
```json
{
  "players": {
    "abc123...": {
      "puuid": "abc123...",
      "summonerId": "xyz789",
      "summonerLevel": 150,
      "tier": "DIAMOND",
      "rank": "I",
      "leaguePoints": 75,
      "riotIdGameName": "PlayerName",
      "riotIdTagline": "TAG"
    }
  }
}
```

---

## Match Data

### Match Object

Complete match information including game metadata and participant data.

**Location**: `matches[matchId]`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `matchId` | string | Yes | Unique match identifier | `"LA2_1234567890"` |
| `info` | object | Yes | Match information object | See below |
| `metadata` | object | Optional | Match metadata | See below |

### Match Info Object

**Location**: `matches[matchId].info`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `game_datetime` | integer | Yes | Game start time (Unix timestamp) | `1699999999000` |
| `game_length` | float | Yes | Game duration in seconds | `1234.5` |
| `participants` | array | Yes | Array of participant objects | See Participant Data |
| `queueId` | integer | Yes | Queue type ID | `1100` (Ranked) |
| `gameVersion` | string | Yes | Game patch version | `"13.24"` |
| `gameCreation` | integer | Optional | Game creation timestamp | `1699999999000` |
| `gameEndTimestamp` | integer | Optional | Game end timestamp | `1700001234000` |
| `gameId` | integer | Optional | Internal game ID | `1234567890` |
| `gameName` | string | Optional | Game name | `"TFT Match"` |
| `gameStartTimestamp` | integer | Optional | Game start timestamp | `1699999999000` |
| `tftSetNumber` | integer | Optional | TFT set number | `10` |
| `tftGameType` | string | Optional | Game type | `"standard"` |

**Queue IDs**:
- `1100`: Ranked
- `1090`: Normal
- `1160`: Double Up (May be different by region)

**Example**:
```json
{
  "matches": {
    "LA2_1234567890": {
      "matchId": "LA2_1234567890",
      "info": {
        "game_datetime": 1699999999000,
        "game_length": 1234.5,
        "queueId": 1100,
        "gameVersion": "13.24",
        "participants": [ ... ]
      }
    }
  }
}
```

---

## Participant Data

### Participant Object

Individual player's participation in a specific match.

**Location**: `matches[matchId].info.participants[]`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `puuid` | string | Yes | Player Unique Identifier | `"abc123..."` |
| `placement` | integer | Yes | Final placement (1-8) | `3` |
| `level` | integer | Yes | Final level reached | `9` |
| `units` | array | Yes | Array of champion/unit objects | See Champion/Unit Data |
| `traits` | array | Yes | Array of trait objects | See Trait Data |
| `augments` | array | Optional | Array of augment IDs | `["augment1", "augment2"]` |
| `companion` | object | Optional | Companion information | `{"skinId": 1, "contentId": "..."}` |
| `gold_left` | integer | Optional | Gold remaining at end | `12` |
| `last_round` | integer | Optional | Last round survived | `25` |
| `total_damage_to_players` | integer | Optional | Total damage dealt | `15000` |
| `players_eliminated` | integer | Optional | Number of players eliminated | `2` |

**Placement Values**: `1` (1st place) through `8` (8th place)

**Example**:
```json
{
  "participants": [
    {
      "puuid": "abc123...",
      "placement": 3,
      "level": 9,
      "units": [ ... ],
      "traits": [ ... ],
      "augments": ["augment1", "augment2"],
      "gold_left": 12,
      "last_round": 25,
      "total_damage_to_players": 15000
    }
  ]
}
```

---

## Champion/Unit Data

### Unit Object

Champion/unit information including items and star level.

**Location**: `matches[matchId].info.participants[].units[]`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `character_id` | string | Yes | Champion ID | `"TFT10_ChampionName"` |
| `items` | array | Yes | Array of item IDs | `[1, 2, 3]` |
| `name` | string | Optional | Champion name | `"ChampionName"` |
| `rarity` | integer | Optional | Champion rarity tier | `3` |
| `tier` | integer | Optional | Champion tier | `2` |
| `starLevel` | integer | Optional | Star level (1-3) | `2` |

**Star Level Values**: `1`, `2`, `3`

**Item IDs**: Integer IDs corresponding to TFT items (see Item Data section)

**Example**:
```json
{
  "units": [
    {
      "character_id": "TFT10_ChampionName",
      "items": [1, 2, 3],
      "name": "ChampionName",
      "rarity": 3,
      "tier": 2,
      "starLevel": 2
    }
  ]
}
```

---

## Trait Data

### Trait Object

Trait/synergy information including active tier.

**Location**: `matches[matchId].info.participants[].traits[]`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `name` | string | Yes | Trait name | `"TraitName"` |
| `num_units` | integer | Yes | Number of units with this trait | `4` |
| `style` | integer | Optional | Trait style/tier | `2` |
| `tier_current` | integer | Optional | Current active tier | `2` |
| `tier_total` | integer | Optional | Total tiers available | `4` |

**Tier Values**: Typically `1` through `4` or `5` depending on trait

**Example**:
```json
{
  "traits": [
    {
      "name": "TraitName",
      "num_units": 4,
      "style": 2,
      "tier_current": 2,
      "tier_total": 4
    }
  ]
}
```

---

## Item Data

### Item Information

Items are represented as integer IDs in the `units[].items[]` array.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| Item ID | integer | TFT item identifier | `1`, `2`, `3`, etc. |

**Common Item IDs** (varies by set):
- `1`: B.F. Sword
- `2`: Recurve Bow
- `3`: Needlessly Large Rod
- `4`: Tear of the Goddess
- `5`: Chain Vest
- `6`: Negatron Cloak
- `7`: Giant's Belt
- `8`: Spatula

**Note**: Item IDs are set-specific and may change between TFT sets. Refer to Riot API static data for current mappings.

---

## Leaderboard Data

### Leaderboard Object

Ranked leaderboard information organized by tier and division.

**Location**: `leaderboards[tier][division]` or `leaderboards[leagueType]`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `tier` | string | Yes | Tier name | `"DIAMOND"`, `"CHALLENGER"` |
| `division` | string | Optional | Division (I-IV) | `"I"`, `"II"`, `"III"`, `"IV"` |
| `entries` | array | Yes | Array of leaderboard entries | See below |

### Leaderboard Entry Object

**Location**: `leaderboards[tier][division].entries[]`

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `puuid` | string | Yes | Player Unique Identifier | `"abc123..."` |
| `summonerId` | string | Yes | Summoner ID | `"xyz789"` |
| `summonerName` | string | Yes | Summoner name | `"PlayerName"` |
| `leaguePoints` | integer | Yes | League Points | `1500` |
| `rank` | string | Optional | Rank within tier | `"I"` |
| `wins` | integer | Optional | Wins | `45` |
| `losses` | integer | Optional | Losses | `30` |

**Example**:
```json
{
  "leaderboards": {
    "DIAMOND": {
      "I": [
        {
          "puuid": "abc123...",
          "summonerId": "xyz789",
          "summonerName": "PlayerName",
          "leaguePoints": 1500,
          "rank": "I",
          "wins": 45,
          "losses": 30
        }
      ]
    },
    "CHALLENGER": {
      "entries": [ ... ]
    }
  }
}
```

---

## JSON-LD Schema Elements

### Context Namespaces

The JSON-LD `@context` defines vocabulary and type mappings:

| Namespace | URI | Purpose |
|-----------|-----|---------|
| `@vocab` | `http://tft-data-extraction.com/schema#` | Default vocabulary |
| `xsd` | `http://www.w3.org/2001/XMLSchema#` | XML Schema data types |
| `rdf` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` | RDF vocabulary |
| `rdfs` | `http://www.w3.org/2000/01/rdf-schema#` | RDF Schema |
| `dcterms` | `http://purl.org/dc/terms/` | Dublin Core terms |
| `foaf` | `http://xmlns.com/foaf/0.1/` | Friend of a Friend |
| `time` | `http://www.w3.org/2006/time#` | Time ontology |

### Entity Types

| Type | Description | Usage |
|------|-------------|-------|
| `TFTDataCollection` | Root collection entity | Root object `@type` |
| `TFTPlayer` | Player entity | Player objects |
| `TFTMatch` | Match entity | Match objects |
| `TFTParticipant` | Participant entity | Participant objects |
| `TFTChampion` | Champion/unit entity | Unit objects |
| `TFTTrait` | Trait entity | Trait objects |
| `TFTItem` | Item entity | Item objects |

### Property Mappings

| Property | XSD Type | Description |
|----------|----------|-------------|
| `puuid` | `xsd:string` | Player Unique Identifier |
| `extractionTimestamp` | `xsd:dateTime` | Collection timestamp |
| `gameCreation` | `xsd:dateTime` | Game creation time |
| `gameLength` | `xsd:float` | Game duration in seconds |
| `placement` | `xsd:integer` | Final placement (1-8) |
| `level` | `xsd:integer` | Final level |
| `goldLeft` | `xsd:integer` | Gold remaining |
| `damageDealt` | `xsd:integer` | Total damage dealt |
| `starLevel` | `xsd:integer` | Champion star level (1-3) |
| `traitTier` | `xsd:integer` | Active trait tier |

---

## Data Type Specifications

### String Types

| Type | Format | Example | Validation |
|------|--------|---------|------------|
| `puuid` | Base64-like string | `"abc123..."` | Length: ~78 characters |
| `matchId` | String with region prefix | `"LA2_1234567890"` | Pattern: `^[A-Z0-9]+_[0-9]+$` |
| `gameVersion` | Semantic version | `"13.24"` | Pattern: `^\d+\.\d+$` |
| `tier` | Uppercase string | `"DIAMOND"` | Enum: Valid tier names |
| `rank` | Roman numeral | `"I"`, `"II"`, `"III"`, `"IV"` | Enum: I, II, III, IV |

### Integer Types

| Type | Range | Description |
|------|-------|-------------|
| `placement` | 1-8 | Final placement in match |
| `level` | 1-10 | Final level reached |
| `leaguePoints` | 0-∞ | League Points (LP) |
| `starLevel` | 1-3 | Champion star level |
| `traitTier` | 1-5 | Active trait tier |
| `queueId` | Various | Queue type identifier |
| `game_datetime` | Unix timestamp | Milliseconds since epoch |

### Float Types

| Type | Range | Description |
|------|-------|-------------|
| `gameLength` | > 0 | Game duration in seconds |

### Date/Time Types

| Type | Format | Example | Description |
|------|--------|---------|-------------|
| `extractionTimestamp` | ISO 8601 UTC | `"2025-11-15T22:58:17Z"` | Collection timestamp |
| `gameCreation` | Unix timestamp (ms) | `1699999999000` | Game creation time |
| `game_datetime` | Unix timestamp (ms) | `1699999999000` | Game start time |

### Array Types

| Type | Element Type | Description |
|------|--------------|-------------|
| `participants` | Participant object | Match participants |
| `units` | Unit object | Champion/unit array |
| `traits` | Trait object | Trait array |
| `augments` | String | Augment ID array |
| `items` | Integer | Item ID array |

### Object Types

| Type | Structure | Description |
|------|-----------|-------------|
| `players` | Dictionary (puuid → Player) | Player data collection |
| `matches` | Dictionary (matchId → Match) | Match data collection |
| `leaderboards` | Nested dictionary | Leaderboard hierarchy |

---

## Validation Rules

### Required Field Validation

**Collection Info**:
- `timestamp`: Must be valid ISO 8601 UTC timestamp
- `extractionLocation`: Must be valid region code (LA1, LA2, etc.)
- `dataVersion`: Must be present

**Player Data**:
- `puuid`: Required, must be valid PUUID format
- `summonerId`: Required
- `tier`: Required, must be valid tier name
- `rank`: Required, must be I, II, III, or IV
- `leaguePoints`: Required, must be non-negative integer

**Match Data**:
- `game_datetime`: Required, must be valid Unix timestamp
- `game_length`: Required, must be positive float
- `participants`: Required, must be non-empty array
- `queueId`: Required, must be valid queue ID
- `gameVersion`: Required, must be valid version string

**Participant Data**:
- `puuid`: Required
- `placement`: Required, must be 1-8
- `level`: Required, must be 1-10
- `units`: Required, must be array (can be empty)
- `traits`: Required, must be array (can be empty)

### Data Quality Rules

1. **Placement Validation**: Must be unique within a match (1-8, each used once)
2. **Level Validation**: Must be between 1 and 10
3. **Star Level Validation**: Must be 1, 2, or 3
4. **Trait Tier Validation**: Must be within valid range for trait
5. **Timestamp Validation**: Must be chronologically consistent
6. **PUUID Format**: Must match Riot PUUID format (78 characters, base64-like)

### Schema Validation

The data must conform to the JSON-LD schema defined in `scripts/schema.py`:
- All `@type` fields must reference valid entity types
- All typed properties must match their XSD type definitions
- All relationships must use valid property names from the schema

### Tree-Based Hierarchical Validation

The data hierarchy is validated using `quality_assurance/tree_validator.py`:
- **Collection → Players → Matches**: Root structure integrity
- **Match → Participants → Units/Traits**: Match sub-structure validation
- **Cross-hierarchy relationships**: Player-match link validation
- Integrated into quality score as "structure" component (20% weight)

---

## Usage Examples

### Example 1: Accessing Player Data

```python
import json

# Load data
with open('tft_weekly_collection_20251115_225817.json', 'r') as f:
    data = json.load(f)

# Access player by PUUID
puuid = "abc123..."
player = data['players'][puuid]

print(f"Player: {player['riotIdGameName']}#{player['riotIdTagline']}")
print(f"Tier: {player['tier']} {player['rank']}")
print(f"LP: {player['leaguePoints']}")
```

### Example 2: Analyzing Match Results

```python
# Access match data
match_id = "LA2_1234567890"
match = data['matches'][match_id]

# Get participants sorted by placement
participants = sorted(
    match['info']['participants'],
    key=lambda p: p['placement']
)

# Print top 3
for i, participant in enumerate(participants[:3]):
    puuid = participant['puuid']
    player_name = data['players'][puuid]['riotIdGameName']
    print(f"{i+1}. {player_name} - Placement: {participant['placement']}")
```

### Example 3: Champion Usage Analysis

```python
# Count champion usage across all matches
champion_counts = {}

for match_id, match in data['matches'].items():
    for participant in match['info']['participants']:
        for unit in participant['units']:
            champ_id = unit['character_id']
            champion_counts[champ_id] = champion_counts.get(champ_id, 0) + 1

# Sort by usage
sorted_champions = sorted(
    champion_counts.items(),
    key=lambda x: x[1],
    reverse=True
)

print("Top 10 Most Used Champions:")
for champ_id, count in sorted_champions[:10]:
    print(f"  {champ_id}: {count} times")
```

### Example 4: Trait Analysis

```python
# Analyze trait activation rates
trait_stats = {}

for match_id, match in data['matches'].items():
    for participant in match['info']['participants']:
        for trait in participant['traits']:
            trait_name = trait['name']
            tier = trait.get('tier_current', 0)
            
            if trait_name not in trait_stats:
                trait_stats[trait_name] = {
                    'total': 0,
                    'tier_counts': {}
                }
            
            trait_stats[trait_name]['total'] += 1
            trait_stats[trait_name]['tier_counts'][tier] = \
                trait_stats[trait_name]['tier_counts'].get(tier, 0) + 1

# Print statistics
for trait_name, stats in trait_stats.items():
    print(f"{trait_name}:")
    print(f"  Total appearances: {stats['total']}")
    for tier, count in sorted(stats['tier_counts'].items()):
        print(f"  Tier {tier}: {count} times")
```

### Example 5: JSON-LD Query

```python
# Query using JSON-LD structure
# Find all matches where a specific player placed top 3

target_puuid = "abc123..."
top_3_matches = []

for match_id, match in data['matches'].items():
    for participant in match['info']['participants']:
        if (participant['puuid'] == target_puuid and 
            participant['placement'] <= 3):
            top_3_matches.append({
                'match_id': match_id,
                'placement': participant['placement'],
                'level': participant['level']
            })

print(f"Player {target_puuid} placed top 3 in {len(top_3_matches)} matches")
```

---

## Additional Resources

- **Schema Definition**: `scripts/schema.py`
- **Field Validation**: `quality_assurance/field_detector.py`
- **Data Validation**: `quality_assurance/data_validator.py`
- **JSON-LD Schema**: `output/tft_schema.jsonld`
- **Riot API Documentation**: https://developer.riotgames.com/

