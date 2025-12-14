# Snakemake Workflow Usage Guide

**Date**: December 1, 2025  
**Project**: TFT Match Data Curation  
**Purpose**: Guide for using the Snakemake workflow for reproducible data pipeline

---

## Overview

This workflow implements a reproducible data curation pipeline for TFT match data using Snakemake. The workflow includes data collection, validation, transformation, quality assessment, and provenance tracking.

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Snakemake installed (`pip install snakemake` or `conda install snakemake`)
- **Riot API key** - **REQUIRED**: Set as environment variable `RIOT_API_KEY` before running

```bash
# Set API key before running workflow
export RIOT_API_KEY="your_api_key_here"
```

### Basic Usage

**⚠️ IMPORTANT**: Set the `RIOT_API_KEY` environment variable before running:

```bash
# Set API key (REQUIRED)
export RIOT_API_KEY="your_api_key_here"

# Dry run (show what would be executed)
snakemake --dry-run --config collection_date=20251027

# Run workflow with specific date
snakemake --config collection_date=20251027

# Run with multiple cores
snakemake --cores 4 --config collection_date=20251027
```

---

## Installation

### Install Snakemake

```bash
# Using pip
pip install snakemake>=7.0.0

# Using conda
conda install -c bioconda -c conda-forge snakemake

# Verify installation
snakemake --version
```

### Set Environment Variables

**Option 1: Using .env file (Recommended)**

The workflow automatically sources the `.env` file if it exists. Create it in the project root:

```bash
# Create .env file
echo "RIOT_API_KEY=your_api_key_here" > .env

# Or use the setup script
bash setup_environment.sh
```

The workflow will automatically load environment variables from `.env` when running.

**Option 2: Export in shell**

```bash
# Set Riot API key
export RIOT_API_KEY="your_api_key_here"
```

**Note**: Snakemake runs each rule in a separate shell, so if you use `export`, make sure to export it in the same shell session where you run Snakemake. Using a `.env` file is recommended as it's automatically loaded by the workflow.

---

## Configuration

### Configuration File

The workflow uses `config/snakemake_config.yaml` for configuration. Key settings:

```yaml
# API Configuration
api:
  region: "la2"  # la2 or la1
  rate_limit: 100  # requests per 2 minutes

# Collection Configuration
collection:
  mode: "daily"  # daily or weekly
  tiers: ["DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]
  output_dir: "data/raw"

# Quality Assurance
quality:
  validation_enabled: true
  anomaly_detection: true
  quality_threshold: 0.8

# Provenance
provenance:
  enabled: true
  format: "w3c_prov"
  output_dir: "provenance"

# Collection Date (can be overridden via --config)
collection_date: ["20251027"]
```

### Override Configuration

```bash
# Override collection date
snakemake --config collection_date=20251027

# Override collection mode
snakemake --config collection.mode=weekly collection_date=20251027

# Override region
snakemake --config api.region=la1 collection_date=20251027

# Use different config file
snakemake --configfile config/production_config.yaml
```

---

## Workflow Structure

### Workflow Flow

```
config/snakemake_config.yaml
    ↓
collect_tft_data → data/raw/tft_collection_{date}.json
    ↓
validate_collection → data/validated/tft_collection_{date}.json
    ↓
transform_to_jsonld → data/transformed/tft_collection_{date}.jsonld
    ↓
    ↓
calculate_quality_metrics → reports/quality_{date}.json
    ↓
validate_cross_cycle → reports/cross_cycle_{date}.json
    ↓
generate_provenance → provenance/workflow_{date}.prov.json
```

### Rule Descriptions

1. **collect_tft_data**: Collects TFT match data from Riot API
2. **validate_collection**: Validates collected data using quality assurance modules
3. **transform_to_jsonld**: Transforms validated data to JSON-LD format
4. **calculate_quality_metrics**: Calculates quality metrics for processed data
5. **validate_cross_cycle**: Validates data consistency across collection cycles (retention, volume trends)
6. **generate_provenance**: Generates W3C PROV provenance information
7. **convert_to_parquet**: Converts JSON-LD data to optimized Parquet format (matches and participants tables)

---

## Command-Line Usage

### Basic Commands

```bash
# Dry run (show execution plan)
snakemake --dry-run

# Dry run with shell commands
snakemake --dry-run --printshellcmds

# Run workflow
snakemake

# Run with specific date
snakemake --config collection_date=20251027

# Run specific rule
snakemake collect_tft_data --config collection_date=20251027

# Run with multiple cores
snakemake --cores 4 --config collection_date=20251027
```

### Advanced Commands

```bash
# Force re-run (ignore existing outputs)
snakemake --forceall --config collection_date=20251027

# Run until specific rule
snakemake --until validate_collection --config collection_date=20251027

# Run from specific rule
snakemake --from validate_collection --config collection_date=20251027

# Show execution plan with details
snakemake --dry-run --printshellcmds --config collection_date=20251027

# Generate workflow diagram
snakemake --dag | dot -Tsvg > workflow_dag.svg

# Generate rule graph
snakemake --rulegraph | dot -Tsvg > workflow_rules.svg
```

### Logging and Output

```bash
# Run with logging
snakemake --log-handler-script workflow/scripts/log_handler.py

# Show detailed output
snakemake --verbose --config collection_date=20251027

# Quiet mode
snakemake --quiet --config collection_date=20251027
```

---

## Examples

### Example 1: Basic Workflow Execution

```bash
# Set API key
export RIOT_API_KEY="your_api_key_here"

# Run workflow for today's date
snakemake --config collection_date=20251027

# Check outputs
ls -lh data/transformed/
ls -lh reports/
ls -lh provenance/
```

### Example 2: Dry Run Before Execution

```bash
# First, check what would be executed
snakemake --dry-run --printshellcmds --config collection_date=20251027

# If everything looks good, run it
snakemake --config collection_date=20251027
```

### Example 3: Run Specific Rule

```bash
# Run only collection rule
snakemake collect_tft_data --config collection_date=20251027

# Run only validation rule (requires collection output)
snakemake validate_collection --config collection_date=20251027
```

### Example 4: Override Configuration

```bash
# Run with weekly mode instead of daily
snakemake --config collection.mode=weekly collection_date=20251027

# Run with different region
snakemake --config api.region=la1 collection_date=20251027

# Run with different quality threshold
snakemake --config quality.quality_threshold=0.9 collection_date=20251027
```

### Example 5: Multiple Collection Dates

```bash
# Run for multiple dates
for date in 20251025 20251026 20251027; do
    snakemake --config collection_date=$date
done
```

### Example 6: Backup Management

```bash
# Create backup manually
snakemake create_backup --config collection_date=20251027

# Verify backup integrity
python3 scripts/backup_system.py --backup-dir backups --list

# Restore from backup
python3 scripts/backup_system.py --restore backups/backup_20251027.tar.gz --restore-dir restored_data

# Clean up old backups (older than 1 year)
python3 scripts/backup_system.py --backup-dir backups --cleanup 365
```

---

## Output Files

### Data Files

- **Raw Data**: `data/raw/tft_collection_{date}.json`
- **Validated Data**: `data/validated/tft_collection_{date}.json`
- **Transformed Data**: `data/transformed/tft_collection_{date}.jsonld`

### Reports

- **Validation Report**: `reports/validation_{date}.json`
- **Quality Report**: `reports/quality_{date}.json`

### Provenance

- **Provenance File**: `provenance/workflow_{date}.prov.json`

### Logs

- **Collection Log**: `logs/collection_{date}.log`
- **Validation Log**: `logs/validate_{date}.log`
- **Transformation Log**: `logs/transform_{date}.log`
- **Quality Log**: `logs/quality_{date}.log`
- **Provenance Log**: `logs/provenance_{date}.log`
- **Backup Log**: `logs/backup_{date}.log`
- **Snakemake Log**: `logs/snakemake_collect_{date}.log`

### Backups

- **Backup Archive**: `backups/backup_{date}.tar.gz` - Compressed backup of all workflow outputs
- **Backup Metadata**: `backups/backup_{date}_metadata.json` - Backup metadata with checksums and file information

**Backup Contents**:
- Raw data files
- Validated data files
- Transformed JSON-LD files
- Quality reports
- Provenance files
- Configuration file

---

## Troubleshooting

### Common Issues

#### Issue 1: API Key Not Found

**Error**: `RIOT_API_KEY environment variable is required`

**Solution**:
```bash
# Option 1: Create .env file (Recommended - automatically loaded by workflow)
echo "RIOT_API_KEY=your_api_key_here" > .env

# Option 2: Export in shell (must be in same session as snakemake)
export RIOT_API_KEY="your_api_key_here"
```

**Note**: The workflow automatically sources the `.env` file if it exists. You don't need to manually `source .env` before running Snakemake.

#### Issue 2: Configuration File Not Found

**Error**: `Config file not found: config/snakemake_config.yaml`

**Solution**:
```bash
# Check if config file exists
ls -la config/snakemake_config.yaml

# Create config file if missing (use template from guide)
cp config/snakemake_config.yaml.example config/snakemake_config.yaml
```

#### Issue 3: Rule Files Not Found

**Error**: `Include file not found: workflow/rules/collect.smk`

**Solution**:
```bash
# Check if rule files exist
ls -la workflow/rules/

# Create missing directories
mkdir -p workflow/rules workflow/scripts workflow/envs
```

#### Issue 4: Import Errors in Rules

**Error**: `ImportError: No module named 'quality_assurance'`

**Solution**:
```bash
# Make sure you're running from project root
cd /path/to/tft-data-extraction

# Check Python path
python3 -c "import sys; print(sys.path)"

# Install dependencies
pip install -r requirements.txt
```

#### Issue 5: Workflow Dependencies Not Met

**Error**: `MissingInputException: Missing input files`

**Solution**:
```bash
# Check if input files exist
ls -la data/raw/

# Run workflow from beginning
snakemake --forceall --config collection_date=20251027

# Or run specific rule that creates missing input
snakemake collect_tft_data --config collection_date=20251027
```

#### Issue 6: Quality Threshold Not Met

**Error**: `Quality score below threshold`

**Solution**:
```bash
# Check quality report
cat reports/quality_20251027.json

# Lower quality threshold if needed
snakemake --config quality.quality_threshold=0.7 collection_date=20251027

# Or investigate data quality issues
cat reports/validation_20251027.json
```

---

## Best Practices

### 1. Always Use Dry Run First

```bash
# Always check execution plan before running
snakemake --dry-run --printshellcmds --config collection_date=20251027
```

### 2. Use Version Control

```bash
# Track workflow files
git add Snakefile workflow/ config/snakemake_config.yaml

# Commit changes
git commit -m "Update Snakemake workflow"
```

### 3. Use Logging

```bash
# Run with logging enabled
snakemake --log-handler-script workflow/scripts/log_handler.py
```

### 4. Check Outputs

```bash
# Verify outputs after execution
ls -lh data/transformed/
ls -lh reports/
ls -lh provenance/
```

### 5. Use Configuration Files

```bash
# Use config files instead of command-line overrides
snakemake --configfile config/production_config.yaml
```

---

## Workflow Rules Reference

### collect_tft_data

**Purpose**: Collect TFT match data from Riot API

**Input**: `config/snakemake_config.yaml`

**Output**: 
- `data/raw/tft_collection_{date}.json`
- `logs/collection_{date}.log`

**Parameters**:
- `region`: API region (from config)
- `mode`: Collection mode (from config)
- `api_key`: Riot API key (from environment)

**Usage**:
```bash
snakemake collect_tft_data --config collection_date=20251027
```

---

### validate_collection

**Purpose**: Validate collected data using quality assurance modules

**Input**: `data/raw/tft_collection_{date}.json`

**Output**:
- `data/validated/tft_collection_{date}.json`
- `reports/validation_{date}.json`

**Parameters**:
- `quality_threshold`: Quality threshold (from config, default: 0.8)

**Usage**:
```bash
snakemake validate_collection --config collection_date=20251027
```

---

### transform_to_jsonld

**Purpose**: Transform validated data to JSON-LD format

**Input**: `data/validated/tft_collection_{date}.json`

**Output**: `data/transformed/tft_collection_{date}.jsonld`

**Usage**:
```bash
snakemake transform_to_jsonld --config collection_date=20251027
```

---

### calculate_quality_metrics

**Purpose**: Calculate quality metrics for processed data

**Input**: `data/transformed/tft_collection_{date}.jsonld`

**Output**: `reports/quality_{date}.json`

**Usage**:
```bash
snakemake calculate_quality_metrics --config collection_date=20251027
```

---

### generate_provenance

**Purpose**: Generate W3C PROV provenance information with full compliance

**Input**:
- `data/raw/tft_collection_{date}.json`
- `data/validated/tft_collection_{date}.json`
- `data/transformed/tft_collection_{date}.jsonld`
- `reports/quality_{date}.json`
- `config/snakemake_config.yaml`

**Output**: `provenance/workflow_{date}.prov.json` (W3C PROV JSON-LD format)

**Features**:
- ✅ **W3C PROV Compliant**: Full PROV entities, activities, agents, and relationships
- ✅ **File Integrity**: SHA-256 checksums for all files
- ✅ **Complete Lineage**: Full data lineage tracking
- ✅ **Execution Metadata**: Software versions, platform, user information
- ✅ **Quality Integration**: Quality metrics embedded in provenance
- ✅ **Configuration Tracking**: Config file checksums and content

**Provenance Components**:
- **Entities**: All data files (raw, validated, transformed, quality reports, config)
- **Activities**: Each workflow step (collection, validation, transformation, quality, provenance)
- **Agents**: Snakemake, workflow system, user, API source
- **Relationships**: `wasGeneratedBy`, `used`, `wasAttributedTo`, `wasAssociatedWith`, `wasInformedBy`

**Usage**:
```bash
snakemake generate_provenance --config collection_date=20251027
```

**View Provenance**:
```bash
# View full provenance document
cat provenance/workflow_20251027.prov.json | jq .

# Extract checksums
cat provenance/workflow_20251027.prov.json | jq '.entity[] | select(.prov:label == "Raw TFT Collection Data") | .tft:sha256'

# View metadata
cat provenance/workflow_20251027.prov.json | jq '.metadata'
```

**Documentation**: See `Documents/PROVENANCE_ENHANCEMENT.md` for complete details.

---

### create_backup

**Purpose**: Create automated backup of workflow outputs

**Input**:
- `data/raw/tft_collection_{date}.json`
- `data/validated/tft_collection_{date}.json`
- `data/transformed/tft_collection_{date}.jsonld`
- `reports/quality_{date}.json`
- `provenance/workflow_{date}.prov.json`
- `config/snakemake_config.yaml`

**Output**:
- `backups/backup_{date}.tar.gz` - Compressed backup archive
- `backups/backup_{date}_metadata.json` - Backup metadata with checksums

**Parameters**:
- `backup_type`: Backup type (from config: "full", "incremental", "differential")
- `backup_dir`: Backup directory (default: "backups")

**Usage**:
```bash
# Create backup automatically (if auto_backup enabled in config)
snakemake create_backup --config collection_date=20251027

# Backup is automatically included in 'all' rule if enabled
snakemake --config collection_date=20251027
```

**Note**: Backup is automatically created after workflow completion if `backup.auto_backup: true` in configuration.

---

### archive_release

**Purpose**: Create long-term preservation archive (Release Package) with bundled documentation

**Input**:
- `Documents/DATA_DICTIONARY.md`
- `Documents/reports/final_report.md`
- `README.md`
- `LICENSE`

**Output**:
- `archives/tft_data_archive_v{version}_{date}.tar.gz` - Compressed archive with data and documentation
- `archives/tft_data_archive_v{version}_{date}.tar.gz.sha256` - SHA-256 checksum file

**Parameters**:
- `version`: Archive version (e.g., "1.0.0")
- `date`: Collection date (e.g., "20251105")
- `archive_description`: Description of the archive content

**Archive Contents**:
```
tft_archive_v{version}/
├── ARCHIVE_README.txt          # Human-readable archive information
├── data/
│   └── tft_collection_{date}.json
├── documentation/
│   ├── DATA_DICTIONARY.md
│   ├── final_report.md
│   ├── README.md
│   └── LICENSE
└── metadata/
    └── manifest.json           # File manifest with checksums
```

**Usage**:
```bash
# Create archive for specific date and version
snakemake archive_release --cores 1 --config date=20251105 version=1.0.0 archive_description="TFT Set 12 Data"

# Create archive with custom description
snakemake archive_release --cores 1 --config date=20251102 version=1.0.1 archive_description="TFT Match Data - November 2025"
```

**Features**:
- ✅ **Self-Contained**: Bundles data with all critical documentation
- ✅ **Citation Ready**: Includes ARCHIVE_README.txt with citation information
- ✅ **Integrity Verified**: SHA-256 checksums for all files
- ✅ **Manifest**: Complete file listing with metadata
- ✅ **Compressed**: Efficient tar.gz compression (~14x compression ratio)

**Note**: This creates a publication-ready archive suitable for long-term preservation and data sharing.

---

### convert_to_parquet

**Purpose**: Convert JSON-LD data to optimized, columnar Parquet format for efficient analysis

**Input**: `data/transformed/tft_collection_{date}.jsonld`

**Output**:
- `data/parquet/{date}/matches.parquet` - Match-level metadata
- `data/parquet/{date}/participants.parquet` - Participant-level performance data

**Features**:
- ✅ **Optimized Storage**: Columnar format significantly reduces file size and improves query performance
- ✅ **Relational Schema**: Flattens nested JSON into relational tables (matches, participants)
- ✅ **Deduplication**: Ensures unique matches across the dataset
- ✅ **Analysis Ready**: Directly loadable into Pandas, Polars, or DuckDB

**Usage**:
```bash
snakemake convert_to_parquet --config collection_date=20251101
```

---

## Checkpoint & Resume System

**Purpose**: Handle interruptions and token expiry without data loss

The workflow includes an automatic checkpoint system that saves progress during long-running collections.

**Features**:
- ✅ **Auto-Save on Token Expiry**: Saves checkpoint when API returns 403 Forbidden
- ✅ **Auto-Save on Interrupt**: Saves checkpoint when you press Ctrl+C
- ✅ **Periodic Saving**: Saves progress every 500 matches
- ✅ **Seamless Resume**: Automatically resumes from checkpoint on restart
- ✅ **Auto-Cleanup**: Deletes checkpoint file on successful completion

**Usage**:
```bash
# Start collection (may be interrupted)
snakemake --cores 8 --config collection_date=20251102

# If interrupted or token expires, checkpoint is saved automatically
# Output: data/raw/tft_collection_20251102_checkpoint.json

# Update your API token
export RIOT_API_KEY="new_token_here"

# Resume collection (automatically detects checkpoint)
snakemake --cores 8 --config collection_date=20251102
# Output: 🔄 Found checkpoint file... Resuming collection from checkpoint...
```

**Checkpoint File Location**:
- `data/raw/tft_collection_{date}_checkpoint.json`

**When Checkpoints Are Created**:
1. Every 500 matches collected
2. When API token expires (403 Forbidden error)
3. When you interrupt with Ctrl+C (KeyboardInterrupt)

**Note**: The checkpoint system is automatic and requires no configuration.

---

## Configuration Options

### API Configuration

```yaml
api:
  region: "la2"  # Options: "la2", "la1"
  rate_limit: 100  # Requests per 2 minutes
```

### Collection Configuration

```yaml
collection:
  mode: "daily"  # Options: "daily", "weekly"
  tiers: ["DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]
  output_dir: "data/daily"
```

### Quality Configuration

```yaml
quality:
  validation_enabled: true  # Enable/disable validation
  anomaly_detection: true  # Enable/disable anomaly detection
  quality_threshold: 0.8  # Minimum quality score (0.0-1.0)
```

### Provenance Configuration

```yaml
provenance:
  enabled: true  # Enable/disable provenance tracking
  format: "w3c_prov"  # Provenance format
  output_dir: "provenance"  # Output directory
```

### Backup Configuration

```yaml
backup:
  enabled: true  # Enable/disable backup system
  type: "full"  # Options: "full", "incremental", "differential"
  retention_days: 730  # Days to retain backups (default: 2 years)
  verify_integrity: true  # Verify backup integrity with checksums
  compression: "gzip"  # Compression format: "gzip", "bz2", "xz"
  compression_level: 6  # Compression level (1-9, higher = more compression)
  auto_backup: true  # Automatically create backup after workflow completion
```

**Backup Features**:
- **Automatic backups**: Enabled by default, creates backup after workflow completion
- **Integrity verification**: SHA-256 checksums for backup integrity
- **Retention management**: Automatic cleanup of old backups based on retention policy
- **Compression**: Configurable compression (gzip, bz2, xz) to save storage space
- **Metadata tracking**: JSON metadata files with backup information and checksums

**Usage**:
```bash
# Disable automatic backup
snakemake --config backup.auto_backup=false collection_date=20251027

# Change backup type
snakemake --config backup.type=incremental collection_date=20251027

# Change retention period
snakemake --config backup.retention_days=365 collection_date=20251027
```

---

## Advanced Usage

### Parallel Execution

```bash
# Run with multiple cores
snakemake --cores 8 --config collection_date=20251027

# Run with unlimited cores (use all available)
snakemake --cores all --config collection_date=20251027
```

### Resource Management

```bash
# Set memory limit
snakemake --resources mem_mb=8000 --config collection_date=20251027

# Set time limit
snakemake --resources runtime_min=60 --config collection_date=20251027
```

### Workflow Visualization

```bash
# Generate DAG diagram
snakemake --dag | dot -Tsvg > workflow_dag.svg

# Generate rule graph
snakemake --rulegraph | dot -Tsvg > workflow_rules.svg

# Generate file graph
snakemake --filegraph | dot -Tsvg > workflow_files.svg
```

### Workflow Testing

```bash
# Test workflow syntax
snakemake --lint

# Test with dry run
snakemake --dry-run --config collection_date=20251027

# Test specific rule
snakemake collect_tft_data --dry-run --config collection_date=20251027

### Multi-week Automated Collection Testing

Tools are available to simulate historical data and test long-term trend analysis:

```bash
# 1. Generate simulated data (4 weeks history)
python3 scripts/simulate_multi_week_data.py --output-dir data/simulated --weeks 4

# 2. Generate long-term health report
python3 scripts/generate_long_term_report.py --data-dir data/simulated --output Documents/LONG_TERM_HEALTH_REPORT.md
```
```

---

## Integration with Existing Scripts

### Using with automated_collection.py

The workflow integrates with existing Python scripts:

```bash
# The collect_tft_data rule calls:
python3 scripts/automated_collection.py \
    --mode daily \
    --region la2 \
    --output data/raw/tft_collection_20251027.json \
    --log logs/collection_20251027.log
```

### Using with Quality Assurance Modules

The workflow uses existing quality assurance modules:

```python
# The validate_collection rule uses:
from quality_assurance.data_validator import validate_tft_data_structure
from quality_assurance.quality_metrics import calculate_data_quality_score
from quality_assurance.tree_validator import calculate_tree_validation_score
```

**Quality Score Components** (5-component scoring):
- Completeness (25%), Consistency (20%), Accuracy (20%), Integrity (15%), Structure (20%)

The "Structure" component integrates tree-based hierarchical validation, validating:
- Collection → Players → Matches hierarchy
- Match → Participants → Units/Traits sub-structure
- Cross-hierarchy relationships (player-match links)

---

## Monitoring and Debugging

### Check Workflow Status

```bash
# Check if workflow is running
ps aux | grep snakemake

# Check log files
tail -f logs/snakemake_collect_20251027.log

# Check output files
ls -lh data/transformed/
```

### Debug Workflow Issues

```bash
# Run with verbose output
snakemake --verbose --config collection_date=20251027

# Run with debug mode
snakemake --debug --config collection_date=20251027

# Check rule dependencies
snakemake --dry-run --printshellcmds --config collection_date=20251027
```

---

## Performance Tips

### 1. Use Multiple Cores

```bash
# Use all available cores
snakemake --cores all --config collection_date=20251027
```

### 2. Cache Results

```bash
# Snakemake automatically caches results
# Re-run only if inputs change
snakemake --config collection_date=20251027
```

### 3. Parallel Execution

```bash
# Run multiple dates in parallel (if supported)
snakemake --cores 4 --config collection_date=20251027
```

---

## References

- **Snakemake Documentation**: https://snakemake.readthedocs.io/
- **Workflow Design**: `Documents/SNAKEMAKE_WORKFLOW_DESIGN.md` - Detailed architecture and design
- **Workflow Usage**: `Documents/SNAKEMAKE_WORKFLOW_USAGE.md` - Practical usage guide
- **Test Results**: `Documents/no-tracking/WORKFLOW_INTEGRATION_TEST_RESULTS.md` - Integration test results

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review workflow logs in `logs/` directory
3. Check validation reports in `reports/` directory
4. Review workflow design: `Documents/SNAKEMAKE_WORKFLOW_DESIGN.md`
5. Review usage guide: `Documents/SNAKEMAKE_WORKFLOW_USAGE.md`

---

**Last Updated**: October 27, 2025  
**Workflow Version**: 1.0.0

