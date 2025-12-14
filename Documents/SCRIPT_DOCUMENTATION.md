# Script Documentation

**Comprehensive guide to all scripts in the TFT Data Extraction project**

---

## Table of Contents

- [Overview](#overview)
- [Data Collection Scripts](#data-collection-scripts)
- [Data Processing Scripts](#data-processing-scripts)
- [Quality Assurance Scripts](#quality-assurance-scripts)
- [Workflow Management Scripts](#workflow-management-scripts)
- [System Management Scripts](#system-management-scripts)
- [Utility Scripts](#utility-scripts)
- [Quick Reference](#quick-reference)

---

## Overview

This document provides detailed documentation for all scripts in the `scripts/` directory. Each script entry includes:
- **Purpose**: What the script does
- **How to Run**: Command-line usage with examples
- **Inputs**: Required files, parameters, or environment variables
- **Outputs**: Generated files and their locations
- **Dependencies**: Required Python packages or system dependencies

---

## Data Collection Scripts

### `automated_collection.py`

**Purpose**: Main automated data collection system for TFT match data. Handles weekly, daily, or incremental collection modes with comprehensive error handling, rate limiting, and quality validation.

**How to Run**:
```bash
# Weekly collection (default)
python3 scripts/automated_collection.py --mode weekly

# Daily collection for specific date
python3 scripts/automated_collection.py --mode daily --date 20251101

# Incremental collection (resume from checkpoint)
python3 scripts/automated_collection.py --mode incremental

# Dry run (test without API calls)
python3 scripts/automated_collection.py --mode weekly --dry-run
```

**Inputs**:
- Environment variable: `RIOT_API_KEY` (required)
- Configuration file: `config/config.yaml` (optional, uses defaults if not provided)
- Checkpoint file: `data/raw/checkpoint_*.json` (for incremental mode)

**Outputs**:
- Raw data file: `data/raw/tft_incremental_YYYYMMDD_HHMMSS.json`
- Log file: `logs/collection_YYYYMMDD.log` (or specified via `--log-file`)
- Checkpoint file: `data/raw/checkpoint_YYYYMMDD_HHMMSS.json` (for resume capability)
- Quality report: `reports/quality_YYYYMMDD.json` (if validation enabled)

**Dependencies**:
- `scripts.optimized_match_collector`
- `scripts.config_manager`
- `scripts.notification_system`
- `quality_assurance` modules

**Example Output**:
```
Collection completed successfully
Players processed: 1,930
Matches collected: 4,469
Data volume: 179.49 MB
Duration: 3 hours 40 minutes
Errors: 0
```

---

### `optimized_match_collector.py`

**Purpose**: Core match collection engine with rate limiting, deduplication, and error handling. Used by `automated_collection.py` but can be used directly for custom collection workflows.

**How to Run**:
```bash
# Direct usage (typically used as a module)
python3 -c "from scripts.optimized_match_collector import create_match_collector; collector = create_match_collector('YOUR_API_KEY'); collector.collect_all_tiers()"
```

**Inputs**:
- API key (via constructor or environment variable)
- Configuration: `config/config.yaml`

**Outputs**:
- Match data dictionary (returned to caller)
- Logs to console and file

**Dependencies**:
- `scripts.base_infrastructure`
- `scripts.riot_api_endpoints`
- `scripts.rate_limiting`
- `scripts.identifier_system`

---

### `player_data_collector.py`

**Purpose**: Collects player data (summoner information, ranked stats) from Riot API. Used for building player pools for match collection.

**How to Run**:
```bash
# Collect players from specific tier
python3 scripts/player_data_collector.py --tier CHALLENGER --region LA2
```

**Inputs**:
- Environment variable: `RIOT_API_KEY`
- Command-line arguments: `--tier`, `--region`, `--division`

**Outputs**:
- Player data JSON file
- Player registry updates

**Dependencies**:
- `scripts.base_infrastructure`
- `scripts.riot_api_endpoints`

---

## Data Processing Scripts

### `transform_to_jsonld.py`

**Purpose**: Transforms raw JSON match data into JSON-LD format with semantic markup (Schema.org compliance) and W3C PROV provenance information.

**How to Run**:
```bash
# Transform a single file
python3 scripts/transform_to_jsonld.py \
    --input data/raw/tft_incremental_20251101_120000.json \
    --output data/transformed/tft_incremental_20251101_120000.jsonld

# Transform all files in directory
python3 scripts/transform_to_jsonld.py \
    --input-dir data/raw \
    --output-dir data/transformed
```

**Inputs**:
- Raw JSON file(s) from collection
- Schema context: `scripts/schema.py` (embedded)

**Outputs**:
- JSON-LD file: `data/transformed/tft_incremental_YYYYMMDD_HHMMSS.jsonld`
- Enhanced with `@context`, `@type`, and provenance metadata

**Dependencies**:
- `scripts.schema`

**Example Output Structure**:
```json
{
  "@context": "https://schema.org/",
  "@type": "VideoGame",
  "game": {
    "@type": "Game",
    "match_id": "...",
    "provenance": { ... }
  }
}
```

---

### `convert_to_parquet.py`

**Purpose**: Converts JSON-LD match data to optimized Parquet columnar format for efficient analysis. Creates two tables: matches (match-level metadata) and participants (player-level performance data).

**How to Run**:
```bash
# Convert single file
python3 scripts/convert_to_parquet.py \
    --input data/transformed/tft_incremental_20251101_120000.jsonld \
    --output-dir data/parquet/20251101

# Convert with date-based organization
python3 scripts/convert_to_parquet.py \
    --input data/transformed/tft_incremental_20251101_120000.jsonld \
    --output-dir data/parquet \
    --date 20251101
```

**Inputs**:
- JSON-LD file: `data/transformed/tft_incremental_*.jsonld`

**Outputs**:
- `data/parquet/YYYYMMDD/matches.parquet` - Match-level data (match_id, game_datetime, tft_set_number, etc.)
- `data/parquet/YYYYMMDD/participants.parquet` - Participant-level data (match_id, puuid, placement, level, damage, etc.)

**Dependencies**:
- `pandas`
- `pyarrow` (for Parquet I/O)

**Example Usage in Analysis**:
```python
import pandas as pd

# Load match data
matches = pd.read_parquet('data/parquet/20251101/matches.parquet')

# Load participant data
participants = pd.read_parquet('data/parquet/20251101/participants.parquet')

# Join for analysis
analysis_data = participants.merge(matches, on='match_id')
```

---

### `filter_incomplete_matches.py`

**Purpose**: Identifies and filters out incomplete match records (missing participants, incomplete data) from collection files.

**How to Run**:
```bash
# Identify incomplete matches (dry run)
python3 scripts/filter_incomplete_matches.py \
    --input data/raw/tft_incremental_20251101_120000.json \
    --mode identify

# Filter out incomplete matches
python3 scripts/filter_incomplete_matches.py \
    --input data/raw/tft_incremental_20251101_120000.json \
    --output data/raw/tft_incremental_20251101_120000_filtered.json \
    --mode filter

# Mark incomplete matches (keep but flag)
python3 scripts/filter_incomplete_matches.py \
    --input data/raw/tft_incremental_20251101_120000.json \
    --output data/raw/tft_incremental_20251101_120000_marked.json \
    --mode mark
```

**Inputs**:
- Raw collection JSON file

**Outputs**:
- Filtered JSON file (if `--mode filter`)
- Marked JSON file with `incomplete` flags (if `--mode mark`)
- Report of incomplete matches (console output)

**Dependencies**:
- Standard library only

---

### `investigate_incomplete_matches.py`

**Purpose**: Analyzes incomplete match patterns to identify root causes and generate recommendations for collection improvements.

**How to Run**:
```bash
# Analyze incomplete matches
python3 scripts/investigate_incomplete_matches.py \
    --input data/raw/tft_incremental_20251101_120000.json \
    --output reports/incomplete_analysis_20251101.json
```

**Inputs**:
- Raw collection JSON file

**Outputs**:
- Analysis report JSON: `reports/incomplete_analysis_YYYYMMDD.json`
- Console summary with recommendations

**Dependencies**:
- Standard library only

---

### `fix_collection_info.py`

**Purpose**: Fixes missing or incorrect `collection_info` metadata in collection files by extracting date from filename or user input.

**How to Run**:
```bash
# Fix single file
python3 scripts/fix_collection_info.py \
    --input data/raw/tft_incremental_20251101_120000.json

# Fix all files in directory
python3 scripts/fix_collection_info.py \
    --input-dir data/raw

# Fix with explicit date
python3 scripts/fix_collection_info.py \
    --input data/raw/tft_incremental_20251101_120000.json \
    --date 20251101
```

**Inputs**:
- Collection JSON file(s) with missing `collection_info`

**Outputs**:
- Updated JSON file (backup created automatically)
- Backup file: `data/raw/tft_incremental_YYYYMMDD_HHMMSS.json.backup`

**Dependencies**:
- Standard library only

---

### `research_analysis.py`

**Purpose**: Performs analysis on TFT match data to answer research questions about meta-game evolution, unit performance, and trait synergies.

**How to Run**:
```bash
python3 scripts/research_analysis.py --input-dir data/transformed --output-dir reports/research
```

**Inputs**:
- Transformed JSON-LD data files

**Outputs**:
- JSON Analysis reports

**Dependencies**:
- `pandas`

---

## Quality Assurance Scripts

### Quality Assurance Module (`quality_assurance/`)

The `quality_assurance/` module provides comprehensive data validation with 6 sub-modules:

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `data_validator.py` | Schema validation | `validate_tft_data_structure()` |
| `quality_metrics.py` | Quality scoring | `calculate_data_quality_score()` - 5-component scoring |
| `tree_validator.py` | Hierarchical validation | `validate_hierarchical_structure()`, `calculate_tree_validation_score()` |
| `anomaly_detector.py` | Outlier detection | Anomaly detection functions |
| `field_detector.py` | Missing field detection | Field detection functions |
| `cross_cycle_validator.py` | Longitudinal validation | Cross-cycle trend analysis |

**Quality Score Components** (as of December 2025):
- **Completeness** (25%): Required fields present
- **Consistency** (20%): Data consistency across sections
- **Accuracy** (20%): Valid values (placements 1-8, levels 1-10)
- **Integrity** (15%): Player-match relationship integrity
- **Structure** (20%): Tree-based hierarchical validation

**Example Usage**:
```python
from quality_assurance import calculate_data_quality_score, calculate_tree_validation_score

# Calculate full quality score (includes tree validation)
quality = calculate_data_quality_score(data)
print(f"Overall Score: {quality['overall_score']:.2f}, Grade: {quality['quality_grade']}")

# Direct tree validation
tree_result = calculate_tree_validation_score(data)
print(f"Tree Score: {tree_result['tree_score']:.2f}")
```

---

### `run_cross_cycle_validation.py`

**Purpose**: Performs cross-cycle validation to detect anomalies across multiple collection cycles (player retention, volume trends, quality degradation).

**How to Run**:
```bash
# Validate across multiple cycles
python3 scripts/run_cross_cycle_validation.py \
    --data-dir data/raw \
    --output reports/cross_cycle_20251101.json \
    --cycles 20251101,20251102,20251103
```

**Inputs**:
- Collection JSON files from multiple dates
- Configuration: `config/config.yaml` (for validation thresholds)

**Outputs**:
- Validation report: `reports/cross_cycle_YYYYMMDD.json`
- Console summary with detected anomalies

**Dependencies**:
- `quality_assurance.cross_cycle_validator`

---

### `error_trend_analysis.py`

**Purpose**: Analyzes error trends across collection cycles to identify recurring API failures, rate limit issues, and system health patterns.

**How to Run**:
```bash
# Analyze error trends
python3 scripts/error_trend_analysis.py \
    --log-dir logs \
    --output reports/error_trends_20251101.json \
    --days 7
```

**Inputs**:
- Log files: `logs/collection_*.log`
- Error summary files (if available)

**Outputs**:
- Trend analysis report: `reports/error_trends_YYYYMMDD.json`
- Console summary with recommendations

**Dependencies**:
- Standard library only

---

## Workflow Management Scripts

### `retry_failed_matches.py`

**Purpose**: Retries collection for matches that failed during initial collection (extracted from error logs or error summary files).

**How to Run**:
```bash
# Retry from error summary
python3 scripts/retry_failed_matches.py \
    --error-summary logs/error_summary_20251101.json \
    --output data/raw/retry_20251101.json

# Retry from data file (extract failed match IDs)
python3 scripts/retry_failed_matches.py \
    --data-file data/raw/tft_incremental_20251101_120000.json \
    --output data/raw/retry_20251101.json
```

**Inputs**:
- Error summary file OR data file with failed matches
- Environment variable: `RIOT_API_KEY`

**Outputs**:
- Retry collection file: `data/raw/retry_YYYYMMDD.json`
- Retry log: `logs/retry_YYYYMMDD.log`

**Dependencies**:
- `scripts.base_infrastructure`
- `scripts.riot_api_endpoints`

---

### `generate_long_term_report.py`

**Purpose**: Generates comprehensive long-term reports aggregating data across multiple collection cycles for trend analysis and project status.

**How to Run**:
```bash
# Generate report for date range
python3 scripts/generate_long_term_report.py \
    --data-dir data/raw \
    --output reports/long_term_report_20251101_20251130.json \
    --start-date 20251101 \
    --end-date 20251130
```

**Inputs**:
- Collection JSON files from date range
- Quality reports (optional)

**Outputs**:
- Long-term report: `reports/long_term_report_YYYYMMDD_YYYYMMDD.json`
- Aggregated statistics, trends, and quality metrics

**Dependencies**:
- Standard library only

---

## System Management Scripts

### `backup_system.py`

**Purpose**: Automated backup system with compression, SHA-256 integrity verification, and retention policy management.

**How to Run**:
```bash
# Create backup
python3 scripts/backup_system.py \
    --source data/raw \
    --backup-dir backups \
    --compress

# Create backup with retention policy
python3 scripts/backup_system.py \
    --source data/raw \
    --backup-dir backups \
    --retention-days 30 \
    --compress

# Restore from backup
python3 scripts/backup_system.py \
    --restore backups/backup_20251101_120000.tar.gz \
    --target data/restored
```

**Inputs**:
- Source directory or files to backup
- Backup configuration (optional)

**Outputs**:
- Compressed backup: `backups/backup_YYYYMMDD_HHMMSS.tar.gz`
- Checksum file: `backups/backup_YYYYMMDD_HHMMSS.sha256`
- Backup manifest: `backups/manifest_YYYYMMDD_HHMMSS.json`

**Dependencies**:
- Standard library only

**Features**:
- Automatic compression (gzip)
- SHA-256 integrity verification
- Retention policy enforcement
- Backup manifest with metadata

---

### `archive_manager.py`

**Purpose**: Creates self-contained, long-term preservation archives by bundling data files, documentation, metadata, and context into release packages.

**How to Run**:
```bash
# Create archive for specific date
python3 scripts/archive_manager.py \
    --date 20251101 \
    --version 1.0.0 \
    --output-dir archives

# Create archive with custom files
python3 scripts/archive_manager.py \
    --data-files data/raw/tft_incremental_20251101_120000.json \
    --docs Documents/DATA_DICTIONARY.md Documents/final_report.md \
    --version 1.0.0 \
    --output-dir archives
```

**Inputs**:
- Data files (JSON/Parquet)
- Documentation files (optional, auto-included if in standard locations)
- Version number

**Outputs**:
- Archive package: `archives/tft_data_YYYYMMDD_vVERSION.tar.gz`
- Archive manifest: `archives/tft_data_YYYYMMDD_vVERSION_manifest.json`
- Archive README: `archives/tft_data_YYYYMMDD_vVERSION_README.md`

**Dependencies**:
- Standard library only

**Archive Contents**:
- Data files (raw, transformed, parquet)
- Documentation (Data Dictionary, Final Report, README)
- Metadata (manifest, checksums)
- Archive README with usage instructions

---

### `notification_system.py`

**Purpose**: Email notification system for collection summaries, error alerts, and quality warnings. Supports SMTP (Gmail, SendGrid, etc.).

**How to Run**:
```bash
# Send collection summary (typically called from automated_collection.py)
python3 -c "
from scripts.notification_system import EmailNotificationSystem
config = {
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'from_address': 'your-email@gmail.com',
    'to_addresses': ['admin@example.com'],
    'password': 'your-app-password'
}
notifier = EmailNotificationSystem(config)
notifier.send_collection_summary({
    'players': 1930,
    'matches': 4469,
    'duration': '3 hours 40 minutes',
    'errors': 0
})
"
```

**Inputs**:
- SMTP configuration (server, port, credentials)
- Notification data (collection stats, errors, quality metrics)

**Outputs**:
- Email notifications sent to configured recipients
- Log entries for notification status

**Dependencies**:
- `smtplib` (standard library)

**Configuration**:
See `Documents/EMAIL_NOTIFICATION_SETUP.md` for detailed setup instructions.

---

### `setup_cron.sh`

**Purpose**: Bash script that generates crontab entries for the hybrid collection strategy (Daily Incremental + Weekly Reconciliation).

**How to Run**:
```bash
# Make executable
chmod +x scripts/setup_cron.sh

# Run to generate crontab lines
./scripts/setup_cron.sh
```

**Inputs**:
- None

**Outputs**:
- Crontab configuration lines (stdout)

---

## Utility Scripts

### `schema.py`

**Purpose**: Generates JSON-LD schema context for TFT match data with Schema.org compliance.

**How to Run**:
```bash
# Generate default schema
python3 scripts/schema.py

# Export schema to file
python3 -c "from scripts.schema import export_default_schema; export_default_schema('tft_schema.jsonld')"
```

**Inputs**:
- None (uses embedded schema definitions)

**Outputs**:
- Schema JSON-LD file: `tft_schema.jsonld` (if exported)
- Schema context dictionary (returned to caller)

**Dependencies**:
- Standard library only

---

### `config_manager.py`

**Purpose**: Manages configuration loading, validation, and parameter management for collection workflows.

**How to Run**:
```bash
# Typically used as a module
python3 -c "
from scripts.config_manager import create_config_manager
config = create_config_manager('config/config.yaml')
print(config.get_collection_config('weekly'))
"
```

**Inputs**:
- Configuration file: `config/config.yaml` (optional)

**Outputs**:
- Configuration object (returned to caller)

**Dependencies**:
- `yaml` (PyYAML)

---

### `rate_limiting.py`

**Purpose**: Advanced rate limiting system with proactive 2-minute window checks, exponential backoff, and comprehensive error handling.

**How to Run**:
```bash
# Typically used as a module
python3 -c "
from scripts.rate_limiting import create_rate_limited_session
session = create_rate_limited_session('YOUR_API_KEY')
response = session.get('https://americas.api.riotgames.com/...')
"
```

**Inputs**:
- API key
- Rate limit configuration

**Outputs**:
- Rate-limited HTTP session object

**Dependencies**:
- `requests`
- `time` (standard library)

---

### `identifier_system.py`

**Purpose**: Manages persistent identifier registry using DuckDB for match deduplication and status tracking.

**How to Run**:
```bash
# Typically used as a module
python3 -c "
from scripts.identifier_system import TFTIdentifierSystem
id_system = TFTIdentifierSystem('identifier_registry.duckdb')
status = id_system.check_match_status('LA2_1234567890')
"
```

**Inputs**:
- DuckDB database file: `identifier_registry.duckdb`

**Outputs**:
- Identifier status information
- Registry updates

**Dependencies**:
- `duckdb`

---

### `utils.py`

**Purpose**: Utility functions for file I/O, data loading, and common operations.

**How to Run**:
```bash
# Typically used as a module
python3 -c "
from scripts.utils import save_data_to_file, load_data_from_file
data = load_data_from_file('data/raw/collection.json')
save_data_to_file(data, 'output.json')
"
```

**Dependencies**:
- Standard library only

---

### `riot_api_endpoints.py`

**Purpose**: Riot API endpoint definitions and URL construction. Provides centralized endpoint management for all TFT API calls including match history, player data, and league entries.

**How to Run**:
```bash
# Typically used as a module by other scripts
python3 -c "
from scripts.riot_api_endpoints import TFTEndpoints
endpoints = TFTEndpoints(region='LA2')
print(endpoints.get_match_url('LA2_1234567890'))
"
```

**Key Endpoints**:
- Match history: `/tft/match/v1/matches/by-puuid/{puuid}/ids`
- Match details: `/tft/match/v1/matches/{matchId}`
- League entries: `/tft/league/v1/entries/{tier}/{division}`
- Summoner info: `/tft/summoner/v1/summoners/{encryptedSummonerId}`

**Dependencies**:
- Standard library only

---

### `base_infrastructure.py`

**Purpose**: Base infrastructure classes and HTTP session management. Provides foundational components for API interaction including session configuration, headers management, and request handling.

**How to Run**:
```bash
# Typically used as a module by collection scripts
python3 -c "
from scripts.base_infrastructure import create_session
session = create_session('YOUR_API_KEY')
"
```

**Key Components**:
- `create_session()` - Creates configured HTTP session with API key headers
- Base classes for API clients
- Error handling utilities

**Dependencies**:
- `requests`

---

### `governance_policies.py`

**Purpose**: Data governance and compliance policy definitions. Implements Riot API Terms of Service compliance checks and data retention policies.

**How to Run**:
```bash
# Typically used as a module
python3 -c "
from scripts.governance_policies import GovernancePolicies
policies = GovernancePolicies()
policies.check_compliance()
"
```

**Key Features**:
- API rate limit compliance tracking
- Data retention policy enforcement
- Terms of Service validation

**Dependencies**:
- Standard library only

---

## Quick Reference

### Most Common Workflows

**1. Weekly Collection (Recommended)**:
```bash
# Using Snakemake (recommended)
snakemake --cores 8

# Using automated_collection.py directly
python3 scripts/automated_collection.py --mode weekly
```

**2. Data Transformation Pipeline**:
```bash
# Step 1: Transform to JSON-LD
python3 scripts/transform_to_jsonld.py \
    --input data/raw/tft_incremental_20251101_120000.json \
    --output data/transformed/tft_incremental_20251101_120000.jsonld

# Step 2: Convert to Parquet
python3 scripts/convert_to_parquet.py \
    --input data/transformed/tft_incremental_20251101_120000.jsonld \
    --output-dir data/parquet/20251101
```

**3. Quality Assurance**:
```bash
# Cross-cycle validation
python3 scripts/run_cross_cycle_validation.py \
    --data-dir data/raw \
    --output reports/cross_cycle_20251101.json

# Error trend analysis
python3 scripts/error_trend_analysis.py \
    --log-dir logs \
    --output reports/error_trends_20251101.json
```

**4. Backup and Archive**:
```bash
# Create backup
python3 scripts/backup_system.py \
    --source data/raw \
    --backup-dir backups \
    --compress

# Create archive
python3 scripts/archive_manager.py \
    --date 20251101 \
    --version 1.0.0 \
    --output-dir archives
```

---

## Environment Variables

All scripts that interact with the Riot API require:

```bash
export RIOT_API_KEY="your_api_key_here"
```

Or create a `.env` file:
```bash
echo "RIOT_API_KEY=your_key_here" > .env
```

---

## Output Directory Structure

After running scripts, your directory structure will look like:

```
tft-data-extraction/
├── data/
│   ├── raw/              # Raw collection JSON files
│   ├── transformed/      # JSON-LD transformed files
│   ├── parquet/          # Parquet columnar storage
│   └── final/            # Final processed data
├── logs/                 # Execution logs
├── backups/              # Automated backups
├── archives/             # Long-term preservation archives
└── reports/              # Quality and validation reports
```

---

## Getting Help

For detailed usage examples and troubleshooting:
- **User Guide**: `Documents/USER_GUIDE.md`
- **Workflow Guide**: `workflow/README.md`
- **Snakemake Usage**: `Documents/SNAKEMAKE_WORKFLOW_USAGE.md`

For script-specific questions, check the docstrings in each script file:
```bash
python3 -c "import scripts.automated_collection; help(scripts.automated_collection.AutomatedCollector)"
```

