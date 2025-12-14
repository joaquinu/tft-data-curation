# Final Report: TFT Match Data Curation Project

**Student Name**: Joaquin Ugarte  
**Course**: CS 598: Foundations of Data Curation  
**Date**: December 14, 2025  

---

## Executive Summary

The TFT Match Data Curation Project is currently **100% complete**. All tasks planned for the entire 12-week timeline have been completed, including core infrastructure setup, automated data collection, quality assurance workflows, Snakemake workflow implementation, and comprehensive provenance tracking. Automation scheduling is operational.

Key achievements:

| Category | Achievement | Evidence |
|----------|-------------|----------|
| **Data Collection** | 13 successful LA2 collections: 73,121 matches, ~54,000 players, 7.1 GB | [`data/raw/`](../../data/raw/), [`scripts/automated_collection.py`](../../scripts/automated_collection.py) |
| **Deduplication** | DuckDB registry achieving 25-50% API call reduction | [`identifier_registry.duckdb`](../../identifier_registry.duckdb) |
| **Metadata & Provenance** | JSON-LD with Schema.org, W3C PROV tracking | [`provenance/`](../../provenance/), [`scripts/schema.py`](../../scripts/schema.py) |
| **Workflow** | Snakemake pipeline with 6 rules, checkpoint/resume | [`Snakefile`](../../Snakefile), [`workflow/`](../../workflow/) |
| **Quality Assurance** | 6-module validation, cross-cycle checks, error trend analysis | [`quality_assurance/`](../../quality_assurance/), [`scripts/error_trend_analysis.py`](../../scripts/error_trend_analysis.py) |
| **Storage** | Parquet columnar format for analysis | [`data/parquet/`](../../data/parquet/), [`scripts/convert_to_parquet.py`](../../scripts/convert_to_parquet.py) |
| **Documentation** | Data dictionary, user guides, script docs | [`DATA_DICTIONARY.md`](../DATA_DICTIONARY.md), [`SCRIPT_DOCUMENTATION.md`](../SCRIPT_DOCUMENTATION.md) |

*Scope adjustment*: LA1 collection infrastructure ready but deferred pending API quota or personal token from Riot.

These results demonstrate the feasibility of sustained daily and weekly collection within current API limits (~100 requests/2 minutes), with comprehensive provenance tracking and reproducible workflows.

**Project Scope**: This is a **data curation project** that successfully created reproducible data collection infrastructure and analysis-ready datasets. Additionally, we conducted preliminary analysis to demonstrate the dataset's capabilities, answering the research questions about meta-game evolution, team compositions, and player strategies (see "Research Question Analysis Results" section).

---

## Dataset Profile

### Data Source
- **Primary Source**: Riot Games TFT API ([developer.riotgames.com](https://developer.riotgames.com/))
- **Data Type**: Teamfight Tactics (TFT) ranked match data
- **Region**: LA2 (Latin America South)
- **Collection Period**: November – December 2025

### Dataset Characteristics

| Metric | Value |
|--------|-------|
| **Total Collections** | 13 successful LA2 collections |
| **Total Matches** | 73,121 collected (61,523 unique after deduplication) |
| **Total Players Processed** | ~54,000 unique players (all ranked tiers) |
| **Data Volume** | 7.1 GB total |
| **Collection Period** | November 1 – December 8, 2025 |
| **Tiers Covered** | All 9 (Challenger, Grandmaster, Master, Diamond, Platinum, Gold, Silver, Bronze, Iron) |
| **Divisions Covered** | All 4 (I, II, III, IV) per applicable tier |

### Data Formats

| Format | Location | Purpose |
|--------|----------|---------|
| **JSON** | `data/raw/` | Raw API responses |
| **JSON-LD** | `data/transformed/` | Semantic markup with Schema.org compliance |
| **Parquet** | `data/parquet/` | Columnar storage for analysis (matches.parquet, participants.parquet) |

### Data Elements
- **Match Data**: Match ID, game datetime, game length, game version, queue type, participants
- **Participant Data**: PUUID, placement (1-8), level, units/champions, traits, augments, items
- **Player Data**: Summoner ID, tier, rank, league points, wins/losses

### Data Citation
```text
TFT Match Data Collection, LA2 Region (2025). 
Collected via Riot Games TFT API. 
Available at: https://github.com/joaquinu/tft-data-curation.git
License: Academic/Research Use (per Riot API Terms of Service)
```

---

## Response to Proposal Feedback

> **Original Proposal Feedback**: "Address the data lifecycle from class (e.g., the USGS Science Data Lifecycle Model of plan, acquire, process, analyze, preserve, publish/share)."

**Response**: This project explicitly addresses **all six stages of the USGS Science Data Lifecycle Model** as requested in the original proposal feedback. The table below provides a quick reference, followed by detailed implementation evidence for each stage.

### USGS Science Data Lifecycle Model - Implementation Summary

| Stage | Timeline | Status | Key Implementation | Primary Evidence |
|-------|----------|--------|-------------------|------------------|
| **1. PLAN** | Week 1 | Complete | Data management plan, schema design, quality framework | `Documents/reports/Project_proposal.md`, `config/config.yaml` |
| **2. ACQUIRE** | Weeks 2-4 | Complete | Automated API collection, rate limiting, 13 successful collections (73K+ matches) | `scripts/automated_collection.py`, DuckDB registry |
| **3. PROCESS** | Weeks 2-6 | Complete | Multi-layer validation, JSON-LD transformation, deduplication | `quality_assurance/` modules (6 validators) |
| **4. ANALYZE** | Weeks 5-6, 9-10 | Complete | Analysis-ready formats, Parquet storage, data dictionary | `Documents/DATA_DICTIONARY.md`, `data/parquet/` |
| **5. PRESERVE** | Weeks 7-8+ | Complete | W3C PROV provenance, Snakemake workflow, automated backups | `provenance/`, `Snakefile`, `scripts/backup_system.py` |
| **6. PUBLISH/SHARE** | Weeks 11-12 | Complete | GitHub repository, comprehensive documentation, compliance | `README.md`, `Documents/` |

**Cross-Cutting Elements** implemented throughout all stages:
- **Describe**: JSON-LD metadata, Schema.org compliance, comprehensive documentation
- **Manage Quality**: 6-module validation system, automated quality metrics
- **Backup & Secure**: Git version control, SHA-256 integrity verification, secure API handling

For detailed implementation evidence for each lifecycle stage, see [`LIFECYCLE_IMPLEMENTATION_SUMMARY.md`](../LIFECYCLE_IMPLEMENTATION_SUMMARY.md).

---

## Research Question Analysis Results

Using the curated dataset (**61,523 unique matches** across 13 collection cycles, patches 15.21–15.24), we conducted analysis to demonstrate the dataset's analytical capabilities:

### RQ1: How do champion and item meta-games evolve?

| Champion | Picks | Avg Placement | Top 4 Rate |
|----------|-------|---------------|------------|
| Baron Nashor | 5,069 | 2.44 | **87.3%** |
| Ziggs | 10,225 | 2.84 | **82.4%** |
| Volibear | 26,168 | 3.11 | **77.2%** |
| Swain (most picked) | 64,276 | 4.11 | 57.0% |

**Finding**: High-cost legendary champions (Baron Nashor, Ziggs) dominate win rates; Swain is most popular but mid-tier performance.

### RQ2: What factors contribute to successful compositions?

| Trait | Activations | Top 4 Rate |
|-------|-------------|------------|
| Baron (unique) | 4,941 | **87.0%** |
| RuneMage | 3,619 | **78.0%** |
| Heroic | 15,141 | **72.0%** |
| Starcaller | 6,304 | **70.3%** |

**Finding**: Vertical trait commitment (RuneMage, Starcaller) and legendary-tier units correlate with top 4 finishes.

### RQ3: How do player strategies adapt to balance changes?

| Level | Players | Percentage |
|-------|---------|------------|
| Level 8 | 188,946 | **39.1%** |
| Level 9 | 158,344 | **32.8%** |
| Level 10 | 44,600 | 9.2% |

**Finding**: **71.9%** of games end at levels 8-9, indicating balanced economy management is the dominant strategy across patches 15.21–15.24.

Full analysis script: [`scripts/research_analysis.py`](../../scripts/research_analysis.py)

---

## Application of Course Concepts

This project demonstrates understanding and application of all required course concepts:

| Course Concept | Implementation | Evidence |
|----------------|----------------|----------|
| **Data Lifecycle** | Full USGS Science Data Lifecycle Model (Plan, Acquire, Process, Analyze, Preserve, Publish/Share) | See "Response to Proposal Feedback" section; all 6 stages implemented |
| **Ethics/Legal Constraints** | Riot API Terms of Service compliance, privacy considerations, data usage restrictions | See "Ethics and Legal Constraints" section; zero ToS violations |
| **Metadata Standards** | JSON-LD with Schema.org compliance, Dublin Core terms, FOAF | `scripts/schema.py`, JSON-LD `@context` in all data files |
| **Workflow Automation** | Snakemake pipeline with 6 rules, cron scheduling, GitHub Actions | `Snakefile`, `workflow/rules/`, `setup_cron.sh` |
| **Provenance Tracking** | W3C PROV standard with temporal, error, and dependency tracking | `provenance/workflow_*.prov.json`, `workflow/rules/provenance.smk` |
| **Reproducibility** | Complete environment specification, step-by-step instructions, parameterized workflows | `requirements.txt`, `README.md`, Snakemake config |
| **Dissemination** | GitHub repository, comprehensive documentation, data citation guidelines | `README.md`, `Documents/` (30+ files), JSON-LD citation metadata |
| **Data Quality** | 7-module validation framework, quality metrics with 5-component scoring (including tree validation), cross-cycle validation | `quality_assurance/` modules, `reports/quality_*.json` |
| **Identifiers** | DuckDB-backed registry for match IDs, PUUID tracking, persistent identifier system | `scripts/identifier_system.py` (creates runtime database) |
| **Data Abstraction** | Tree-structured validation integrated into quality score as "structure" component, relational models, hierarchical match data | `quality_assurance/tree_validator.py`, `quality_assurance/quality_metrics.py` |

---

## Project Progress Summary

### Progress

| Phase | Planned Weeks | Status | Notes |
|-------|---------------|--------|-------|
| Phase 1: Infrastructure | 1 | Completed | Endpoint mapping (`scripts/riot_api_endpoints.py`), rate limiting, JSON-LD schema generation (`scripts/schema.py`) |
| Phase 2: Collection & Quality | 2–4 | Completed | LA2 collection automated (13 runs); QA modules implemented (`quality_assurance/`) |
| Phase 3: Metadata & Organization | 5–6 | Completed | DuckDB registry, unified JSON-LD `@context/@type`, reusable configuration (`config/config.yaml`), weekly deduplication logic, identifier/provenance alignment |
| Phase 4: Workflow & Preservation | 7–8 | Completed | Snakemake workflow with enhanced provenance tracking (temporal, error, dependencies), automated backup system |
| Phase 5: Automation | 9–10 | Completed | Cron jobs operational, automated collection system deployed |
| Phase 6: Testing & Publication | 11–12 | Completed | Multi-week testing completed, data dictionary finished, final report submitted |

**Decisions and Scope Adjustments**: JSON remains primary exchange format with Parquet optimization implemented; LA2 collection prioritized; LA1 infrastructure ready but deferred pending API quota assessment.

---

## Evidence of Progress Through Artifacts

### Collection Summary (November–December 2025)

| Date | Matches | Players |
|------|---------|---------|
| Nov 1-5, 2025 | 18,000 | 31,655 |
| Nov 7, 2025 | 2,573 | 2,172 |
| Dec 1-8, 2025 | 52,550 | 20,196 |
| **Total** | **73,121** (61,523 unique) | **~54,000** |

Key outcomes:
* **13 successful collections** over 6 weeks demonstrating pipeline stability.
* **Zero errors** in last 7-day error trend analysis (236 log files analyzed).
* Full tier coverage across all ranked divisions.
* Validated deduplication, rate-limiting, and checkpoint/resume strategies.

---

## Challenges and Mitigation

**Development API Token Management**:
* **Challenge**: Personal project approval pending; dev tokens require daily manual refresh.
* **Impact**: Single day all-tier collection takes ~4 hours; weekly full collection requires token management.
* **Mitigation**: Implemented **hybrid daily + weekly reconciliation** strategy with status-aware deduplication:
  1. **Daily runs** capture complete match data using one token per day.
  2. **Weekly reconciliation** skips already collected matches.
  3. DuckDB registry tracks match completion status.

**Operational Advantages**:
* Sustainable under dev-key constraints.
* Daily + weekly approach achieves ~31,000 matches/week.
* Personal project approval will remove manual refresh requirement, enabling full automation.

Other operational improvements include complete `@type` coverage, enhanced schema validation, controlled API rate usage, email notification integration, and API efficiency optimization reducing duplicate calls by ~50%.

---

## Limitations

* **API Rate Limits**: ~3,000 requests/hour or 100 every 2 minutes.
* **Token Management**: Requires manual refresh until approval; mitigated via hybrid strategy.
* **Automation Infrastructure**: Full activation pending API project approval (currently using dev tokens with manual refresh).
* **Rerun Setup Issues**: Not implementing reruns correctly made me lost some runs because it was deleteing my previous runs. 

---

## Ethics and Legal Constraints

### Riot API Terms of Service Compliance

This project strictly adheres to the [Riot Games API Terms of Service](https://developer.riotgames.com/terms):

| Requirement | Implementation |
|-------------|----------------|
| **Rate Limiting** | Proactive 2-minute buffer check; 100 requests/2 min limit enforced (`scripts/rate_limiting.py`) |
| **API Key Security** | Keys stored in environment variables, never committed to version control |
| **Data Usage** | Academic/research use only; no commercial redistribution |
| **Attribution** | Riot Games cited as data source in all documentation |
| **No ToS Violations** | Zero violations across 13+ collection cycles |

### Privacy Considerations

- **Player Data**: Uses Riot-provided PUUIDs (pseudonymous identifiers); no personally identifiable information (PII) collected
- **Data Minimization**: Only match and ranked data collected; no chat logs, friend lists, or account details
- **No Re-identification**: Data structure does not support re-identification of real-world identities

### Data Redistribution

- **Code**: Available under MIT License for academic use
- **Data**: Subject to Riot API Terms; may not be redistributed commercially
- **Documentation**: Available for reference and educational purposes

### Ethical Use Statement

This dataset is intended for:
- Academic research on gaming analytics
- Educational demonstration of data curation workflows
- Non-commercial analysis of game meta-evolution

The project does not support or enable:
- Player harassment or targeting
- Cheating or game manipulation
- Commercial exploitation of player data

---

## Findings and Lessons Learned

### Key Findings

1. **Feasibility of Large-Scale Collection**: Successfully demonstrated that comprehensive TFT match data collection (~4,500 matches) is achievable within Riot API rate limits (~100 requests/2 minutes).

2. **Deduplication Effectiveness**: The DuckDB identifier registry achieved 25-50% reduction in redundant API calls through status-aware match tracking.

3. **Multi-Layer Validation Value**: The six-module quality assurance framework (schema, tree, anomaly, field, cross-cycle, error trend) proved essential for maintaining data integrity across collection cycles.

4. **Workflow Reproducibility**: Snakemake integration enabled fully reproducible pipelines with complete provenance tracking, meeting W3C PROV standards.

### Lessons Learned

1. **Plan for API Constraints Early**: Rate limiting and token expiry handling should be core architecture decisions, not afterthoughts. The checkpoint/resume system was critical for handling 24-hour dev token limits.

2. **Metadata Standards Pay Off**: Investing in JSON-LD and Schema.org compliance early enabled seamless provenance tracking and analysis-ready data formats throughout the pipeline.

3. **Automation Requires Robust Error Handling**: Email notifications, error trend analysis, and comprehensive logging were essential for monitoring unattended collection runs.

4. **Quality Assurance Must Be Multi-Layered**: Single-point validation is insufficient for API data; hierarchical validation (schema,tree, anomaly and field detection) catches different error classes.

5. **Version Control Everything**: Git-based versioning of code, documentation, and configuration enabled rollback capability and audit trails essential for reproducibility.

### Recommendations and Next Steps

To further enhance the utility and scale of this dataset, the following future work is recommended:

1.  **Multi-Region Expansion**: Extend collection to major regions (NA, EUW, KR, JP) to enable cross-cultural meta comparison. Korean and Japanese regions often develop unique strategies that later spread globally, making early detection of emerging meta trends possible. This would require per-region rate limiting and region-partitioned storage (`data/raw/{region}/`).

2.  **Longitudinal Meta-Analysis**: Execute the analysis pipeline over a full 3-month TFT set cycle. The current data proves the pipeline works; a full-season run would provide the volume needed for statistically significant balance trend analysis.

3.  **Patch Notes Integration**: Programmatically ingest official Riot patch notes as structured data, enabling automatic correlation between balance changes and meta shifts. For example, tracking "Braum armor nerf in 15.23 → 10% pick rate drop" would provide causal evidence for meta evolution beyond simple observation.

4.  **Augment Synergy Mapping**: Build a graph database (Neo4j or NetworkX) of augment-champion-item synergies with weighted edges based on win rate correlation. This would enable queries such as "find the highest-performing augment combinations for El Tigre compositions" and support visual exploration of meta relationships.

5.  **Open Dataset Publication**: Publish the anonymized dataset on Kaggle or similar site with a DOI for academic citation and community research. Include a datasheet (Gebru et al. format), citation file (`CITATION.cff`), and sample analysis notebooks to maximize reusability and research impact.

6.  **API Version Change Detection**: Extend the existing field detection capabilities to automatically detect API schema changes (new champions, traits, items, or field modifications). By hashing the current schema and comparing daily, the system could alert operators to content patches without manual monitoring, ensuring the pipeline adapts to Riot API updates proactively.

---

## References

Köster, J., & Rahmann, S. (2012). *Snakemake—a scalable bioinformatics workflow engine*. Bioinformatics, 28(19), 2520–2522. [https://doi.org/10.1093/bioinformatics/bts480](https://doi.org/10.1093/bioinformatics/bts480)

Riot Games. (2024). *Riot developer portal*. [https://developer.riotgames.com/](https://developer.riotgames.com/)

Riot Games. (2024). *Teamfight Tactics API documentation*. [https://developer.riotgames.com/apis#tft-match-v1](https://developer.riotgames.com/apis#tft-match-v1)

Schema.org Community Group. (2024). *Schema.org*. [https://schema.org/](https://schema.org/)

Ugarte, J. (2025). *Curating Riot's TFT match data: A reproducible data workflow project*. [Project Proposal](Project_proposal.md). GitHub: [https://github.com/joaquinu/tft-data-curation](https://github.com/joaquinu/tft-data-curation)

Lynch, C. (1999). *Canonicalization: A Fundamental Tool to Facilitate Preservation and Management of Digital Information*. D-Lib Magazine, 5(9). [https://www.dlib.org/dlib/september99/09lynch.html](https://www.dlib.org/dlib/september99/09lynch.html)

Duerr, R. E., et al. (2011). *On the Utility of Identification Schemes for Digital Earth Science Data*. Earth Science Informatics, 4, 139–160. [https://doi.org/10.1007/s12145-011-0083-6](https://doi.org/10.1007/s12145-011-0083-6)

Gil, Y. (2017). *Identifiers and Identifier Systems*. CS598-FDC Lecture (Foundations of Data Curation). [Course lecture material - not publicly available]

Kunze, J. A. (2002). *A Metadata Kernel for Electronic Permanence*. Journal of Digital Information, 2(2). [https://dcpapers.dublincore.org/article/952106562](https://dcpapers.dublincore.org/article/952106562)

USGS Data Management. (2024). *USGS Science Data Lifecycle Model*. [https://www.usgs.gov/data-management/data-lifecycle](https://www.usgs.gov/data-management/data-lifecycle)

---

## Documentation & Reproducibility

This project includes comprehensive documentation. Full script documentation is available in [`SCRIPT_DOCUMENTATION.md`](../SCRIPT_DOCUMENTATION.md).

### Script Quick Reference

| Script | Purpose | Command | Output |
|--------|---------|---------|--------|
| `automated_collection.py` | Main data collection | `python3 scripts/automated_collection.py --mode weekly` | `data/raw/tft_incremental_*.json` |
| `transform_to_jsonld.py` | JSON-LD transformation | `python3 scripts/transform_to_jsonld.py --input <file>` | `data/transformed/*.jsonld` |
| `convert_to_parquet.py` | Parquet storage | `python3 scripts/convert_to_parquet.py --input <file>` | `data/parquet/*/matches.parquet` |
| `run_cross_cycle_validation.py` | Cross-cycle validation | `python3 scripts/run_cross_cycle_validation.py --data-dir data/raw` | `reports/cross_cycle_*.json` |
| `backup_system.py` | Automated backups | `python3 scripts/backup_system.py --source data/raw --compress` | `backups/backup_*.tar.gz` |
| `error_trend_analysis.py` | Error pattern analysis | `python3 scripts/error_trend_analysis.py --log-dir logs` | `reports/error_trends_*.json` |

### Documentation Index

| Category | Document | Purpose |
|----------|----------|---------|
| **Quick Start** | `README.md` | Project overview and setup (415 lines) |
| **Quick Start** | `Documents/USER_GUIDE.md` | Role-based user guide |
| **Technical** | `Documents/DATA_DICTIONARY.md` | Field-level data documentation |
| **Technical** | `Documents/SCRIPT_DOCUMENTATION.md` | Complete script reference |
| **Workflow** | `workflow/README.md` | Detailed Snakemake guide |
| **Workflow** | `Documents/SNAKEMAKE_WORKFLOW_USAGE.md` | Practical workflow examples |
| **Lifecycle** | `Documents/USGS_LIFECYCLE_IMPLEMENTATION_PLAN.md` | USGS lifecycle mapping |
| **Lifecycle** | `Documents/LIFECYCLE_IMPLEMENTATION_SUMMARY.md` | Lifecycle quick reference |
| **Operations** | `Documents/EMAIL_NOTIFICATION_SETUP.md` | Email system configuration |
| **Operations** | `Documents/OPERATIONAL_STRATEGY.md` | Operational procedures |

### Computational Environment

| Component | Specification |
|-----------|--------------|
| **Operating System** | macOS, Linux, or Windows (with WSL) |
| **Python Version** | 3.8+, 3.13 recommended (tested on 3.10, 3.12, 3.13) |
| **Workflow Engine** | Snakemake >= 7.0.0 |

**Key Dependencies**: `duckdb>=0.9.0`, `requests>=2.31.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `python-dotenv>=1.0.0`, `snakemake>=7.0.0`, `networkx>=3.2`

### How to Reproduce

```bash
# 1. Clone and setup
git clone https://github.com/joaquinu/tft-data-curation.git
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure API key
export RIOT_API_KEY="your_key"  # from developer.riotgames.com

# 3. Run workflow
snakemake --cores 8 --config collection_date=20251101
```

For detailed instructions, see `README.md` and `Documents/SNAKEMAKE_WORKFLOW_USAGE.md`.

---

## Submission Artifacts

### Artifact Archive

A comprehensive artifact archive containing all project deliverables, code, documentation, and data samples is available at:

**University of Illinois Box**: [https://uofi.box.com/s/tglg5yeccot73zn1bah9z7m23zaci0do](https://uofi.box.com/s/tglg5yeccot73zn1bah9z7m23zaci0do)

This archive includes data, logs and reports. For Code and Documentation visit the [GitHub Repository](https://github.com/joaquinu/tft-data-curation)

**Note**: Access requires University of Illinois Box credentials. For public access, see the GitHub repository: [https://github.com/joaquinu/tft-data-curation](https://github.com/joaquinu/tft-data-curation)

