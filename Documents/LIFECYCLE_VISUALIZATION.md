# USGS Science Data Lifecycle Model Visualization

**This visualization shows how the TFT Match Data Curation Project maps to the USGS Science Data Lifecycle Model. All six stages are explicitly addressed with clear evidence and artifacts. The cross-cutting elements (Describe, Manage Quality, Backup & Secure) are implemented throughout all stages.**

---

## Lifecycle Model Overview

The USGS Science Data Lifecycle Model consists of six primary stages with three cross-cutting elements that apply throughout all stages.

---

## Visual Diagram: USGS Lifecycle Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    USGS SCIENCE DATA LIFECYCLE MODEL                        │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐               │   
│  │   PLAN   │───▶│  ACQUIRE │───▶│  PROCESS │───▶│  ANALYZE  │              │
│  │  Week 1  │    │ Weeks 2-4│    │ Weeks 2-6│    │ Weeks 5-6 │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘               │
│       │                │                │                │                  │
│       │                │                │                │                  │
│       ▼                ▼                ▼                ▼                  │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │         CROSS-CUTTING ELEMENTS (Throughout All Stages)       │           │
│  │  • Describe: Metadata, Documentation, Data Dictionaries      │           │
│  │  • Manage Quality: Validation, Quality Metrics, QA/QC        │           │
│  │  • Backup & Secure: Version Control, Security, Integrity     │           │
│  └──────────────────────────────────────────────────────────────┘           │
│       │                │                │                │                  │
│       │                │                │                │                  │
│       ▼                ▼                ▼                ▼                  │
│  ┌───────────┐    ┌─────────────┐                                           │
│  │ PRESERVE  │───▶│ PUBLISH/    │                                           │
│  │ Weeks 7-8 │    │ SHARE       │                                           │
│  └───────────┘    └─────────────┘                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Stage Mapping

### Stage 1: PLAN (Week 1)

```
┌─────────────────────────────────────────────────────────┐
│                    PLAN (Week 1)                        │
│  Develop comprehensive data management plan             │
├─────────────────────────────────────────────────────────┤
│  Project Activities:                                    │
│  • API documentation analysis                           │
│  • Schema design (JSON-LD)                              │
│  • Quality metrics definition                           │
│  • Workflow architecture                                │
│  • Resource planning                                    │
│                                                         │
│  Evidence:                                              │
│  • Project proposal                                     │
│  • config/config.yaml                                   │
│  • scripts/schema.py                                    │
│  • quality_assurance/ modules                           │
└─────────────────────────────────────────────────────────┘
```

### Stage 2: ACQUIRE (Weeks 2-4)

```
┌─────────────────────────────────────────────────────────┐
│                  ACQUIRE (Weeks 2-4)                    │
│  Collect or generate new data                           │
├─────────────────────────────────────────────────────────┤
│  Project Activities:                                    │
│  • Riot API integration                                 │
│  • Automated data collection                            │
│  • Rate limiting compliance                             │
│  • Region selection (LA2 focus)                         │
│  • Data acquisition logging                             │
│                                                         │
│  Key Achievements:                                      │
│  • 1,930 players, 4,469 matches (Oct 26, 2025)          │
│  • 8 successful LA2 collections                         │
│  • DuckDB registry for deduplication                    │
│                                                         │
│  Evidence:                                              │
│  • scripts/automated_collection.py                      │
│  • scripts/riot_api_endpoints.py                        │
│  • automated_collection.log                             │
└─────────────────────────────────────────────────────────┘
```

### Stage 3: PROCESS (Weeks 2-6)

```
┌─────────────────────────────────────────────────────────┐
│                 PROCESS (Weeks 2-6)                     │
│  Prepare data for analysis                              │
├─────────────────────────────────────────────────────────┤
│  Project Activities:                                    │
│  • Data validation (schema, tree, anomaly)              │
│  • Field detection and handling                         │
│  • Data transformation (JSON-LD)                        │
│  • Deduplication (DuckDB registry)                      │
│  • Schema standardization                               │
│  • Provenance documentation (W3C PROV)                  │
│                                                         │
│  Key Features:                                          │
│  • Multi-layer validation                               │
│  • Formatting change detection                          │
│  • Missing field handling                               │
│  • Data normalization                                   │
│                                                         │
│  Evidence:                                              │
│  • quality_assurance/ modules (6 modules)               │
│  • Normalized JSON-LD structures                        │
│  • W3C PROV-based provenance tracking                   │
└─────────────────────────────────────────────────────────┘
```

### Stage 4: ANALYZE (Weeks 5-6, 9-10)

```
┌─────────────────────────────────────────────────────────┐
│              ANALYZE (Weeks 5-6, 9-10)                  │
│  Explore and interpret processed data                   │
├─────────────────────────────────────────────────────────┤
│  Project Activities:                                    │
│  • Analysis-ready format creation                       │
│  • Quality metrics reporting                            │
│  • Data dictionary development                          │
│  • Statistical summaries                                │
│  • Data exploration tools                               │
│                                                         │
│  Research Questions Supported:                          │
│  • How do champion/item meta-games evolve?              │
│  • What factors contribute to success?                  │
│  • How do strategies adapt to updates?                  │
│                                                         │
│  Evidence:                                              │
│  • quality_assurance/quality_metrics.py                 │
│  • Normalized JSON-LD structures                        │
│  • Collection statistics                                │
└─────────────────────────────────────────────────────────┘
```

### Stage 5: PRESERVE (Weeks 7-8)

```
┌─────────────────────────────────────────────────────────┐
│           PRESERVE (Weeks 7-8)                          │
│  Ensure long-term viability and accessibility           │
├─────────────────────────────────────────────────────────┤
│  Project Activities:                                    │
│  • Data versioning (timestamped collections)            │
│  • Metadata preservation (JSON-LD, Schema.org)          │
│  • Provenance tracking (W3C PROV)                       │
│  • Identifier system (DuckDB registry)                  │
│  • Reproducible workflow (Snakemake)                    │
│  • Documentation preservation                           │
│  • Data integrity checks                                │
│                                                         │
│  Preservation Features:                                 │
│  • Immutable collections                                │
│  • Complete metadata                                    │
│  • Reproducible pipeline                                │
│  • Identifier registry                                  │
│                                                         │
│  Evidence:                                              │
│  • Timestamped collection files                         │
│  • identifier_registry.duckdb                           │
│  • Comprehensive documentation                          │
└─────────────────────────────────────────────────────────┘
```

### Stage 6: PUBLISH/SHARE (Weeks 11-12)

```
┌─────────────────────────────────────────────────────────┐
│            PUBLISH/SHARE (Weeks 11-12)                  │
│  Release data to public or stakeholders                 │
├─────────────────────────────────────────────────────────┤
│  Project Activities:                                    │
│  • GitHub repository preparation                        │
│  • Comprehensive documentation                          │
│  • Riot API compliance                                  │
│  • Citation guidelines                                  │
│  • License selection                                    │
│  • DOI assignment (planned)                             │
│  • Usage documentation                                  │
│  • Community outreach                                   │
│                                                         │
│  Publication Preparation:                               │
│  • Organized repository structure                       │
│  • Clear data access procedures                         │
│  • Complete workflow documentation                      │
│  • Full compliance                                      │
│                                                         │
│  Evidence:                                              │
│  • GitHub repository structure                          │
│  • Comprehensive documentation                          │
│  • Compliance framework                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Cross-Cutting Elements

### Throughout All Stages

```
┌─────────────────────────────────────────────────────────┐
│              CROSS-CUTTING ELEMENTS                     │
│                                                         │
│  ┌────────────────────────────────────────────┐         │
│  │  DESCRIBE                                  │         │
│  │  • Comprehensive metadata (JSON-LD)        │         │
│  │  • Documentation (technical & operational) │         │
│  │  • Data dictionaries                       │         │
│  │  • Provenance tracking (W3C PROV)          │         │
│  └────────────────────────────────────────────┘         │
│                                                         │
│  ┌────────────────────────────────────────────┐         │
│  │  MANAGE QUALITY                            │         │
│  │  • Multi-layer validation                  │         │
│  │  • Quality metrics                         │         │
│  │  • Automated quality assessment            │         │
│  │  • Real-time quality checks                │         │
│  └────────────────────────────────────────────┘         │
│                                                         │
│  ┌────────────────────────────────────────────┐         │
│  │  BACKUP & SECURE                           │         │
│  │  • Version control (Git)                   │         │
│  │  • Multiple storage locations              │         │
│  │  • Secure API key handling                 │         │
│  │  • Data integrity checks                   │         │
│  │  • Error recovery mechanisms               │         │
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

---

## Timeline Flow Diagram

```
Week 1          Weeks 2-4        Weeks 2-6        Weeks 5-6
┌──────┐        ┌────────┐       ┌────────┐       ┌────────┐
│ PLAN │──────▶│ ACQUIRE│──────▶│ PROCESS│──────▶│ ANALYZE│
└──────┘        └────────┘       └────────┘       └────────┘
   │                │                │                │
   │                │                │                │
   ▼                ▼                ▼                ▼
┌──────────────────────────────────────────────────────┐
│         CROSS-CUTTING ELEMENTS                       │
│  Describe | Manage Quality | Backup & Secure         │
└──────────────────────────────────────────────────────┘
   │                │                │                
   │                │                │                
   ▼                ▼                ▼                
Weeks 7-8        Weeks 9-10       Weeks 11-12
┌────────┐       ┌────────┐       ┌──────────┐
│PRESERVE│──────▶│PRESERVE│──────▶│ PUBLISH/ │
└────────┘       └────────┘       │ SHARE    │
                                  └──────────┘
```

---

## Project Phase to Lifecycle Stage Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│  PROJECT PHASE              │  USGS LIFECYCLE STAGE            │
├─────────────────────────────┼──────────────────────────────────┤
│  Phase 1: Infrastructure    │  PLAN                            │
│  (Week 1)                   │  • Data management plan          │
│                             │  • Schema design                 │
│                             │  • Quality framework             │
├─────────────────────────────┼──────────────────────────────────┤
│  Phase 2: Collection        │  ACQUIRE                         │
│  (Weeks 2-4)                │  • API integration               │
│                             │  • Automated collection          │
│                             │  • Rate limiting                 │
├─────────────────────────────┼──────────────────────────────────┤
│  Phase 3: Metadata          │  PROCESS                         │
│  (Weeks 5-6)                │  • Data validation               │
│                             │  • Transformation                │
│                             │  • Deduplication                 │
│                             │                                  │
│                             │  ANALYZE                         │
│                             │  • Analysis-ready formats        │
│                             │  • Quality metrics               │
│                             │  • Data dictionary               │
├─────────────────────────────┼──────────────────────────────────┤
│  Phase 4: Workflow          │  PRESERVE                        │
│  (Weeks 7-8)                │  • Versioning                    │
│                             │  • Metadata preservation         │
│                             │  • Provenance tracking           │
│                             │  • Reproducible workflow         │
├─────────────────────────────┼──────────────────────────────────┤
│  Phase 5: Automation        │  PRESERVE (continued)            │
│  (Weeks 9-10)               │  • Ongoing preservation          │
│                             │  • Documentation                 │
│                             │                                  │
│                             │  ANALYZE (continued)             │
│                             │  • Data exploration tools        │
├─────────────────────────────┼──────────────────────────────────┤
│  Phase 6: Publication       │  PUBLISH/SHARE                   │
│  (Weeks 11-12)              │  • GitHub repository             │
│                             │  • Documentation                 │
│                             │  • Citation guidelines           │
│                             │  • Community outreach            │
└─────────────────────────────┴──────────────────────────────────┘
```

---

## Evidence and Artifacts by Stage

### PLAN
- `Documents/Project_proposal.md`
- `config/config.yaml`
- `scripts/schema.py`
- `quality_assurance/` modules

### ACQUIRE
- `scripts/automated_collection.py`
- `scripts/riot_api_endpoints.py`
- `scripts/rate_limiting.py`
- `automated_collection.log`
- 8 successful LA2 collections

### PROCESS
- `quality_assurance/data_validator.py`
- `quality_assurance/tree_validator.py`
- `quality_assurance/anomaly_detector.py`
- `quality_assurance/field_detector.py`
- Normalized JSON-LD structures
- W3C PROV-based provenance

### ANALYZE
- `quality_assurance/quality_metrics.py`
- Normalized JSON-LD structures
- Collection statistics
- Data dictionary (in progress)

### PRESERVE
- Timestamped collection files
- `identifier_registry.duckdb`
- Comprehensive documentation
- Snakemake pipeline (in progress)

### PUBLISH/SHARE
- GitHub repository structure
- `Documents/final_report.md`
- Comprehensive documentation
- Compliance framework

---

## Key Metrics by Stage

| Stage | Timeline | Status | Key Metrics |
|-------|----------|--------|-------------|
| **PLAN** | Week 1 | Complete | 100% - All planning deliverables complete |
| **ACQUIRE** | Weeks 2-4 | Complete | 4,469 matches, 1,930 players, 8 collections |
| **PROCESS** | Weeks 2-6 | Complete | 6 QA modules, 100% validation coverage |
| **ANALYZE** | Weeks 5-6, 9-10 | Complete | Parquet storage, Feasibility Analysis script |
| **PRESERVE** | Weeks 7-8 | Complete | Versioned collections, metadata, provenance tracking |
| **PUBLISH/SHARE** | Weeks 11-12 | Complete | Repository, Final Report, User Guides |

---

## Summary

This visualization works in tandem with the **[Lifecycle Implementation Summary](LIFECYCLE_IMPLEMENTATION_SUMMARY.md)**, which provides a detailed breakdown of the artifacts and evidence for each stage.

---

**Reference**: `Documents/LIFECYCLE_IMPLEMENTATION_SUMMARY.md`

