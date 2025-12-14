# Operational Strategy: Hybrid Daily + Weekly Reconciliation


## 1. Executive Overview

This document defines the sustainable operational model for Teamfight Tactics (TFT) data collection, specifically designed to operate effectively under the constraints of a Development API Key.

**Strategic Approach**
The project implements a **Hybrid Daily + Weekly Reconciliation** strategy. Rather than attempting continuous collection (which risks rate limits and token expiration), this model maximizes coverage per token and ensures data integrity through periodic reconciliation.

**Key Achievements:**
*   **Efficiency:** Maximized data yield per collection window.
*   **Low Overhead:** Minimized manual intervention (~15 minutes/week).
*   **High Volume:** Achieving ~31,000+ matches per week.
*   **Automation:** Fully automated workflow via Snakemake (Phase 2).

---

## 2. Collection Strategy

### 2.1. Daily Collections (Data Acquisition)

**Schedule:** Daily at 02:00 UTC
**Objective:** Capture the previous day's match data across all ranked tiers (Iron through Diamond).

**Process Workflow:**
1.  **Token Refresh:** Administrator updates the `RIOT_API_KEY` (if validity < 4 hours remaining).
2.  **Execution:** Automated script triggers `scripts/automated_collection.py --mode daily`.
3.  **Validation:** System verifies API connectivity and rate limit status.
4.  **Preservation:** Raw JSON output is saved with timestamped filenames (`tft_daily_collection_YYYYMMDD_hhmmss.json`).

**Output:**
*   Raw Data File (JSON)
*   Execution Checksum & Logs
*   DuckDB Registry Update

### 2.2. Weekly Reconciliation (Data Integrity)

**Schedule:** Sunday at 15:00 UTC
**Objective:** Consolidate daily datasets, eliminate duplicates, and resolve incomplete records.

#### Status-Aware Deduplication
This project employs a novel **Status-Aware Deduplication** strategy to optimize API usage and ensure data completeness.

*   **The Problem:** Traditional scraping often rediscovers the same match IDs across multiple days, leading to redundant API calls for data already possessed.
*   **The Solution:** The system tracks the "Completion Status" of every match ID in the DuckDB registry.
    *   If a match is rediscovered and marked `COMPLETE` (8 participants), the API call is skipped.
    *   If a match is marked `INCOMPLETE`, the system triggers a targeted fetch to fill the gap.
*   **Impact:** This reduces weekly API calls by approximately **25%** compared to naive collection methods.

**Reconciliation Process:**
1.  **Aggregation:** Load all 7 daily JSON collection files.
2.  **Analysis:** Query DuckDB for status of all identified match IDs.
3.  **Gap-Filling:** Fetch details only for new or incomplete matches.
4.  **Consolidation:** Merge valid records into a single weekly release file.
5.  **Metrics Generation:** Produce quality report and storage statistics.

---

## 3. Data Management & Preservation

### 3.1. File Hierarchy

The data lake is structured to separate raw ingestion from reconciled curation:

```text
data/
├── daily/                  # Transient daily captures
│   ├── tft_daily_collection_YYYYMMDD.json
│   └── ...
├── weekly/                 # Authoritative consolidated releases
│   ├── tft_weekly_reconciled_YYYYWW.json
│   └── ...
├── registry/               # Metadata & deduplication index
│   └── identifier_registry.duckdb
└── logs/                   # Execution audit trails
```

### 3.2. Retention Policy
*   **Daily Files:** Retained for 90 days as a raw backup.
*   **Weekly Reconciled Files:** Retained indefinitely (2+ years).
*   **Registry:** Permanent, immutable audit trail of all ingestion events.
*   **Backup:** Weekly off-site backup execution via Snakemake.

---

## 4. Token Management

### 4.1. Constraints
The Development API Key imposes strict limits:
*   **Validity:** 24 hours.
*   **Rate System:** 100 requests per 2 minutes.

### 4.2. Operational Procedure
To maintain continuous operation:
1.  **Daily Refresh:** Recommended practice is to refresh the token daily prior to the automated run.
2.  **Environment Security:** The key is stored exclusively in a secure `.env` file, never committed to version control.
    ```bash
    # Content of .env
    RIOT_API_KEY="RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    ```

---

## 5. Automation & Workflow

### 5.1. Current State (Phase 2 - Complete)
The entire lifecycle is orchestrated by **Snakemake**, ensuring reproducibility and error handling.

*   **Workflow Definition:** `Snakefile`
*   **Trigger:** Cron / Task Scheduler
*   **Jobs:**
    *   `collect_tft_data`: Runs daily acquisition.
    *   `validate_collection`: Runs immediate QA checks.
    *   `reconcile_weekly`: Runs weekly merge and dedup.
    *   `backup_data`: Archives datasets to secure storage.

### 5.2. Future Roadmap
*   **Phase 3 (Personal Project Approval):** Shift to Personal API Key (Longer validity, higher limits).

---

## 6. Metrics & Monitoring

The system automatically generates performance metrics for every cycle:

**Daily Report:**
*   Collection Duration
*   Throughput (Matches/Minute)
*   Error Rate
*   Quality Score (0-100)

**Weekly Health Report:**
*   Total Unique Matches
*   Deduplication Efficiency (API Calls Saved)
*   Retention Rate (Cycle-over-Cycle)
*   Storage Growth

