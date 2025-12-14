# TFT Data Extraction Project - User Guide

## Introduction

Welcome to the Teamfight Tactics (TFT) Data Extraction Project User Guide. This document serves as the central hub for all project documentation, designed to help you get started quickly whether you are a data analyst, pipeline operator, or system administrator.

## Choose Your Path

Select the role that best fits your needs:

### I want to analyze the data
**Role**: Data Consumer  
**Goal**: Understand the dataset structure, fields, and quality.  
**Go to**: [Data Consumer Guide](#data-consumer-guide)

### I want to run the data collection
**Role**: Pipeline Operator  
**Goal**: Execute the workflow, collect new data, or reproduce results.  
**Go to**: [Pipeline Operator Guide](#pipeline-operator-guide)

### I want to manage the system
**Role**: Administrator  
**Goal**: Set up automation, configure notifications, and manage backups.  
**Go to**: [Administrator Guide](#administrator-guide)

---

## <a name="data-consumer-guide"></a>Data Consumer Guide

If you are using the dataset for analysis, research, or application development.

### 1. Understanding the Data
*   **[Data Dictionary](DATA_DICTIONARY.md)**: The definitive reference for all fields, data types, and descriptions.
*   **[Project Final Report](reports/final_report.md)**: Detailed methodology, data quality assessment, and project results.

### 2. Accessing the Data
*   **Raw Data**: Located in `data/raw/`. JSON files containing direct API responses.
*   **Processed Data**: Located in `data/transformed/`. JSON-LD files with semantic markup.
*   **Archives**: Long-term preservation packages in `archives/`.

### 3. Data Quality
*   **Quality Reports**: Located in `reports/`. JSON files detailing quality metrics for each collection.
*   **Provenance**: Located in `provenance/`. W3C PROV files tracking the lineage of every data file.

---

## <a name="pipeline-operator-guide"></a>Pipeline Operator Guide

If you are responsible for running the data collection and processing workflow.

### 1. Quick Start
The project uses **Snakemake** for workflow management.

```bash
# Run the full workflow for the default configuration
snakemake --cores 8

# Run for a specific date
snakemake --cores 8 --config collection_date=20251102
```

### 2. Detailed Documentation
*   **[Workflow README](../workflow/README.md)**: Comprehensive guide to the Snakemake workflow, rules, and configuration.
*   **[Snakemake Usage Guide](SNAKEMAKE_WORKFLOW_USAGE.md)**: Practical examples and common commands.
*   **[Workflow Architecture](SNAKEMAKE_WORKFLOW_DESIGN.md)**: Deep dive into the workflow architecture.

### 3. Common Tasks
*   **Collect Data**: `snakemake collect_tft_data`
*   **Validate Data**: `snakemake validate_collection`
*   **Create Backup**: `snakemake create_backup`
*   **Create Archive**: `snakemake archive_release --config date=20251102 version=1.0.0`

---

## <a name="administrator-guide"></a>Administrator Guide

If you are setting up or maintaining the system infrastructure.

### 1. Automation Setup
*   **Cron Configuration**: Run `scripts/setup_cron.sh` to generate the crontab entries for the Hybrid Daily scheme.

### 2. System Configuration
*   **[Email Notification Setup](EMAIL_NOTIFICATION_SETUP.md)**: Configure SMTP settings for automated alerts.
*   **[Backup System Documentation](BACKUP_SYSTEM_MANUAL.md)**: Manage retention policies and recovery procedures.

### 3. Maintenance
*   **Logs**: Check `logs/` for detailed execution logs.
*   **Environment**: Ensure `requirements.txt` dependencies are up to date.

---

## Troubleshooting

### Common Issues

**1. Rate Limit Errors (429)**
*   **Cause**: Exceeding Riot API limits.
*   **Solution**: The system handles this automatically with exponential backoff. Check `logs/` to confirm.

**2. API Key Expired (403)**
*   **Cause**: Personal API key expired (24h limit).
*   **Solution**: Regenerate key at [developer.riotgames.com](https://developer.riotgames.com/) and update `RIOT_API_KEY` env var. The Checkpoint System will save progress.

**3. Missing Data Files**
*   **Cause**: Collection interrupted or failed.
*   **Solution**: Check `logs/` for errors. Use the Checkpoint System to resume.

### Getting Help
*   Refer to the **[Operational Strategy](OPERATIONAL_STRATEGY.md)** for incident response protocols.

---

## <a name="special-reports"></a>📈 Special Reports

### Long Term Health Report
To generate the **Long Term Health Report** (which aggregates quality scores, data volume trends, and retention rates across all collection cycles), run the following script:

```bash
python scripts/generate_long_term_report.py
```

This will:
1.  Read the latest cross-cycle validation report.
2.  Aggregate metrics from all available individual cycle reports.
3.  Update **`Documents/LONG_TERM_HEALTH_REPORT_P313.md`** with the latest trends.

Use this after running a new Cross-Cycle Validation to ensure the health report is up-to-date.

---

## Documentation Index

### Core Documentation
*   [README.md](../README.md) - Project Overview
*   [USER_GUIDE.md](USER_GUIDE.md) - This Guide
*   [DATA_DICTIONARY.md](DATA_DICTIONARY.md) - Field Definitions
*   [final_report.md](reports/final_report.md) - Project Report

### Workflow & Technical
*   [workflow/README.md](../workflow/README.md) - Snakemake Guide
*   [SNAKEMAKE_WORKFLOW_USAGE.md](SNAKEMAKE_WORKFLOW_USAGE.md) - Usage Examples
*   [setup_cron.sh](../scripts/setup_cron.sh) - Automation Script
*   [EMAIL_NOTIFICATION_SETUP.md](EMAIL_NOTIFICATION_SETUP.md) - Notification Setup
*   [BACKUP_SYSTEM_MANUAL.md](BACKUP_SYSTEM_MANUAL.md) - Backup System

### Project Tracking
*   [Status Dashboard](reports/status_dashboard.md)
*   [Timeline](reports/project_timeline.md)

