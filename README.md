# TFT Data Extraction Project

**A comprehensive data curation pipeline for Teamfight Tactics (TFT) match data from Riot Games API**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](requirements.txt)
[![License](https://img.shields.io/badge/License-Academic%20Use-green)]()

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Features](#features)
- [Documentation](#documentation)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [Status](#status)

---

## Overview

This project implements a comprehensive data curation pipeline for collecting, validating, transforming, and preserving TFT match data from the Riot Games API. The pipeline includes:

- **Automated Data Collection**: Multi-tier ranked match collection with rate limiting
- **Quality Assurance**: Comprehensive validation and quality scoring
- **Reproducible Workflows**: Snakemake-based pipeline with full provenance tracking
- **Data Preservation**: Automated backups with integrity verification
- **Error Handling**: Comprehensive error tracking and email notifications
- **W3C PROV Compliance**: Complete provenance tracking with temporal, error, and dependency tracking
- **Parquet Storage**: Columnar storage format for efficient analysis


---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Riot API Key ([Get one here](https://developer.riotgames.com/))
- Snakemake (for workflow execution)

### Installation

```bash
# Clone the repository
git clone https://github.com/joaquinu/tft-data-curation.git
cd tft-data-curation

# Install dependencies
pip install -r requirements.txt

# Set up environment
export RIOT_API_KEY="your_api_key_here"
# Or create .env file: echo "RIOT_API_KEY=your_key" > .env
```

### Basic Usage

**Using Snakemake Workflow (Recommended)**:
```bash
# Set API key
export RIOT_API_KEY="your_api_key_here"

# Run workflow for specific date
snakemake --cores 8 --config collection_date=20251101

# Run all workflow steps
snakemake --cores 8
```

**Using Automated Collection Script**:
```bash
# Weekly collection
python3 scripts/automated_collection.py --mode weekly

# Date-based collection
python3 scripts/automated_collection.py --mode daily
```

> **Need help with scripts?** See **[Script Documentation](Documents/SCRIPT_DOCUMENTATION.md)** for complete reference on all 24+ scripts including purpose, command-line usage, inputs, and expected outputs.

---

## Project Structure

```
tft-data-extraction/
├── scripts/                    # Core collection and processing scripts
│   ├── automated_collection.py # Main automated collection system
│   ├── optimized_match_collector.py
│   ├── notification_system.py  # Email notification system
│   ├── backup_system.py        # Automated backup system
│   └── ...
├── workflow/                   # Snakemake workflow
│   ├── README.md              # Workflow usage guide (871 lines)
│   ├── rules/                 # Workflow rule files
│   └── scripts/              # Workflow helper scripts
├── quality_assurance/          # Data validation and quality modules
├── config/                    # Configuration files
│   ├── config.yaml           # Main configuration
│   └── snakemake_config.yaml # Workflow configuration
├── Documents/                 # Comprehensive documentation (30+ files)
│   ├── final_report.md       # Complete project report
│   ├── SNAKEMAKE_WORKFLOW_DESIGN.md
│   ├── EMAIL_NOTIFICATION_SETUP.md
│   └── ...
├── data/                      # Data output directories
│   ├── raw/                  # Raw collected data
│   ├── validated/            # Validated data
│   ├── transformed/          # Transformed JSON-LD data
│   ├── parquet/              # Parquet columnar storage
│   └── final/                # Final processed data
├── logs/                      # Log files
├── backups/                   # Automated backups
├── provenance/               # W3C PROV provenance documents
└── reports/                   # Quality and validation reports
```

---

## Features

### Core Features

- **Multi-Tier Collection**: Collects data from all ranked tiers (Challenger to Iron)
- **Rate Limiting**: Advanced rate limiting with proactive 2-minute checks
- **Data Validation**: Comprehensive validation with quality scoring
- **Error Tracking**: Detailed error tracking and categorization
- **Deduplication**: Match deduplication to minimize API calls
- **Provenance Tracking**: W3C PROV compliant provenance with temporal, error, and dependency tracking

### Workflow Features

- **Snakemake Pipeline**: Reproducible workflow with 6 rule files
- **Parameterization**: Flexible date-based and weekly collection modes
- **Automated Backups**: SHA-256 integrity verification
- **Quality Metrics**: Automated quality assessment
- **JSON-LD Transformation**: Semantic data transformation
- **Parquet Storage**: Columnar format for efficient analysis (matches.parquet, participants.parquet)
- **Cross-Cycle Validation**: Historical trend analysis and player retention tracking

### Automation Features

- **Cron Scheduling**: Weekly automated collections
- **Email Notifications**: SMTP email alerts and summaries
- **Error Alerts**: Configurable error threshold notifications
- **Quality Warnings**: Automated quality score monitoring
- **Checkpoint & Resume**: Automatic checkpoint system for interrupted collections

---

## Documentation

### Main Documentation

- **[User Guide](Documents/USER_GUIDE.md)** - **Start Here!** Comprehensive guide for all users
- **[Script Documentation](Documents/SCRIPT_DOCUMENTATION.md)** - **Complete script reference** - Purpose, usage, inputs, and outputs for all scripts
- **[Final Report](Documents/reports/final_report.md)** - Complete project report with lifecycle implementation

### Quick Start Guides

- **[Workflow README](workflow/README.md)** - Snakemake workflow usage guide (871 lines)
- **[Snakemake Workflow Design](Documents/SNAKEMAKE_WORKFLOW_DESIGN.md)** - Detailed workflow architecture and design
- **[Snakemake Workflow Usage](Documents/SNAKEMAKE_WORKFLOW_USAGE.md)** - Practical usage guide and examples
- **[Email Notification Setup](Documents/EMAIL_NOTIFICATION_SETUP.md)** - Email system setup
- **[Backup System Manual](Documents/BACKUP_SYSTEM_MANUAL.md)** - Backup system documentation

### Technical Documentation

- **[Script Documentation](Documents/SCRIPT_DOCUMENTATION.md)** - Complete reference for all scripts (purpose, usage, inputs, outputs)
- **[Data Dictionary](Documents/DATA_DICTIONARY.md)** - Complete field-level documentation
- **[Operational Strategy](Documents/OPERATIONAL_STRATEGY.md)** - Operational procedures
- **[API Documentation](scripts/riot_api_endpoints.py)** - Embedded in code with docstrings

### Verification Reports

- **[All Phases Verification](Documents/no-tracking/ALL_PHASES_VERIFICATION_AND_SUMMARIES.md)** - Complete verification summary for all project phases
- **[Workflow Integration Test Results](Documents/no-tracking/WORKFLOW_INTEGRATION_TEST_RESULTS.md)** - Workflow integration test execution results
- **[Backup Validation](Documents/BACKUP_VALIDATION_REPORT.md)** - Backup system validation

### Project Documentation

- **[Project Proposal](Documents/Project_proposal.md)** - Original project proposal
- **[Progress Report](Documents/progress_report.md)** - Progress tracking
- **[Phase Summaries](Documents/PHASE4_SUMMARY.txt)** - Phase completion summaries

**Total Documentation**: 30+ files, 11,000+ lines

---

## Installation

### Full Installation

```bash
# 1. Clone repository
git clone https://github.com/joaquinu/tft-data-curation.git
cd tft-data-curation

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Snakemake (for workflow execution)
pip install snakemake>=7.0.0
# Or: conda install -c bioconda -c conda-forge snakemake

# 4. Set up environment
export RIOT_API_KEY="your_api_key_here"
# Or create .env file
echo "RIOT_API_KEY=your_key_here" > .env

# 5. Verify installation
python3 -c "import scripts.optimized_match_collector; print('✓ Installation successful')"
snakemake --version
```

### Quick Setup Scripts

```bash
# Environment setup
bash setup_environment.sh

# Snakemake setup
bash setup_snakemake.sh

# Cron job setup (for automation)
bash setup_cron.sh
```

---

## Usage

### Snakemake Workflow (Recommended)

The Snakemake workflow provides a complete, reproducible pipeline:

```bash
# Set API key
export RIOT_API_KEY="your_api_key_here"

# Date-based collection
snakemake --cores 8 --config collection_date=20251101

# Weekly collection (default)
snakemake --cores 8

# Dry run (see what would be executed)
snakemake --dry-run --config collection_date=20251101

# Run specific rule
snakemake collect_tft_data --config collection_date=20251101
```

**Workflow Steps**:
1. `collect_tft_data` - Collect raw data from API
2. `validate_collection` - Validate data structure and quality
3. `transform_to_jsonld` - Transform to JSON-LD format
4. `validate_cross_cycle` - Cross-cycle validation and trend analysis
5. `calculate_quality_metrics` - Calculate quality scores
6. `convert_to_parquet` - Convert to columnar Parquet format
7. `generate_provenance` - Generate W3C PROV provenance
8. `create_backup` - Create automated backup

### Automated Collection Script

```bash
# Weekly collection
python3 scripts/automated_collection.py --mode weekly \
    --output-dir data/raw \
    --log-file logs/collection.log

# Daily collection
python3 scripts/automated_collection.py --mode daily

# Incremental collection
python3 scripts/automated_collection.py --mode incremental
```

### Automated Scheduling

**Cron Job** (Weekly execution):
```bash
# Install cron job
bash setup_cron.sh

# Cron schedule: 0 0 * * 0 (Sunday 00:00)
```

---

## Configuration

### Main Configuration

Edit `config/config.yaml` for collection parameters:

```yaml
global:
  api:
    key: ${RIOT_API_KEY}  # From environment variable
    region: LA2
  rate_limiting:
    requests_per_second: 20
    requests_per_2min: 100
  notifications:
    enabled: false  # Set to true for email notifications
    email:
      smtp_server: smtp.gmail.com
      smtp_port: 587
      from_address: your-email@gmail.com
      to_addresses: [admin@example.com]
```

### Snakemake Configuration

Edit `config/snakemake_config.yaml` for workflow parameters:

```yaml
collection_date: ["20251101"]  # Date(s) to collect
collection_period: weekly      # Or: daily, weekly
output_dirs:
  raw: data/raw
  validated: data/validated
  transformed: data/transformed
```

### Environment Variables

Create `.env` file in project root:

```bash
RIOT_API_KEY=your_api_key_here
EMAIL_PASSWORD=your_email_app_password  # For notifications
```

---

## Features in Detail

### Data Collection

- **Multi-Tier Collection**: All ranked tiers (Challenger, Grandmaster, Master, Diamond, Platinum, Gold, Silver, Bronze, Iron)
- **Comprehensive Coverage**: Collects all divisions (I, II, III, IV) for each tier
- **Time Range Filtering**: Date-based collection with timestamp filtering
- **Player Coverage**: Collects from 6,000+ players per collection

### Quality Assurance

- **Structure Validation**: JSON schema validation
- **Data Quality Scoring**: Comprehensive quality metrics (0-100 scale)
- **Anomaly Detection**: Statistical anomaly detection
- **Field Validation**: Required and optional field validation
- **Cross-Cycle Comparison**: Quality trends over time
- **Type Comparison Fixes**: Robust type handling for timestamp comparisons
- **JSON-LD Compliance**: Complete @type field coverage for all entities

### Provenance Tracking

- **W3C PROV Compliance**: Full PROV standard implementation
- **Temporal Tracking**: Start/end times and durations for all activities
- **Error Tracking**: Error entities linked to collection activities
- **Dependency Tracking**: Python packages and API endpoints tracked
- **Git Integration**: Version control information in provenance

### Automation

- **Scheduled Collections**: Weekly automated execution
- **Email Notifications**: Collection summaries, error alerts, quality warnings
- **Error Handling**: Comprehensive error tracking and recovery
- **Backup System**: Automated backups with integrity verification
- **Checkpoint & Resume**: Automatic checkpoint system for handling interruptions and token expiry

---

## Contributing

This is an academic research project. For questions or contributions, please refer to the project documentation or contact the project maintainer.

---

## License

Academic/Research Use Only

This project is for academic and research purposes. Commercial use requires separate licensing from Riot Games.

---

## Acknowledgments

- **Riot Games API**: Data source via Riot Games Developer Portal
- **Snakemake**: Workflow management system
- **W3C PROV**: Provenance standard implementation

---

## Quick Links

- 📖 [Script Documentation](Documents/SCRIPT_DOCUMENTATION.md) - **Complete reference for all scripts**
- 📝 [Final Report](Documents/reports/final_report.md)
- 🔧 [Workflow Guide](workflow/README.md)
- 📧 [Email Setup](Documents/EMAIL_NOTIFICATION_SETUP.md)
- 💾 [Backup System](Documents/BACKUP_SYSTEM_MANUAL.md)
- 📚 [Data Dictionary](Documents/DATA_DICTIONARY.md)
