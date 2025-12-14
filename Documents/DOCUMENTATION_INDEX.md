# Documentation Index

**TFT Data Extraction Project - Complete Documentation Guide**


---

## Quick Navigation

### Top 3 Essential Documents
- **[Final Report](reports/final_report.md)** - Key results, analysis, and project summary.
- **[User Guide](USER_GUIDE.md)** - Comprehensive guide for all user roles.
- **[Data Dictionary](DATA_DICTIONARY.md)** - Field-level details for all datasets.

---

## Documentation by Category

### General Info & Reports
| Document | Location | Description |
|----------|----------|-------------|
| **Final Report** | `reports/final_report.md` | Executive summary, methodology, and results. |
| **Project Proposal** | `reports/Project_proposal.md` | Original project scope and objectives. |
| **Progress Report** | `reports/progress_report.md` | Tracking of milestones and completion status. |

### ️ Operations & Workflow
| Document | Location | Description |
|----------|----------|-------------|
| **User Guide** | `USER_GUIDE.md` | Operational guide for Consumers, Operators, and Admins. |
| **Snakemake Usage** | `SNAKEMAKE_WORKFLOW_USAGE.md` | Quick reference for running the pipeline. |
| **Operational Strategy** | `OPERATIONAL_STRATEGY.md` | Daily/Weekly routines and maintenance procedures. |
| **Email Setup** | `EMAIL_NOTIFICATION_SETUP.md` | Configuration for automated alerts. |
| **Test Plan** | `WORKFLOW_INTEGRATION_TEST_PLAN.md` | Integration testing strategy and coverage. |
| **Test Results** | `WORKFLOW_INTEGRATION_TEST_RESULTS.md` | Execution results of the test suite. |

### Technical Implementation
| Document | Location | Description |
|----------|----------|-------------|
| **Script Documentation** | `SCRIPT_DOCUMENTATION.md` | Detailed reference for all Python scripts. |
| **Workflow Architecture** | `SNAKEMAKE_WORKFLOW_DESIGN.md` | Core architecture of the pipeline rules. |
| **Data Dictionary** | `DATA_DICTIONARY.md` | Schema definitions and field explanations. |
| **Identifier System** | `IDENTIFIER_SYSTEM_SPECIFICATION.md` | Complete specification: theoretical background, ID schemes (PUUID, MatchID), and canonicalization. |
| **API Reference** | `../scripts/riot_api_endpoints.py` | (Code) API endpoint definitions. |

### Provenance & Lifecycle
| Document | Location | Description |
|----------|----------|-------------|
| **Lifecycle Visuals** | `LIFECYCLE_VISUALIZATION.md` | Diagrams of the data lifecycle. |
| **Lifecycle Summary** | `LIFECYCLE_IMPLEMENTATION_SUMMARY.md` | Quick summary of USGS lifecycle phases. |
| **Provenance Schema** | `PROVENANCE_SCHEMA.md` | W3C PROV implementation details. |
| **Future Prov** | `PROVENANCE_FUTURE_ENHANCEMENTS_EVALUATION.md` | Evaluation of future tracking capabilities. |
| **Quality Specification** | `QUALITY_METRICS_SPECIFICATION.md` | Metrics for data quality assessment. |

### Investigations & Legacy
| Document | Location | Description |
|----------|----------|-------------|
| **Backup Manual** | `BACKUP_SYSTEM_MANUAL.md` | Manual for backup system operations. |
| **Backup Validation** | `BACKUP_VALIDATION_REPORT.md` | Validation report of the backup system. |
| **Current Status** | `no-tracking/current_status.md` | Detailed status log (archived). |
| **Gantt Chart** | `no-tracking/gantt.md` | Project timeline (archived). |
| **Lifecycle Plan** | `no-tracking/USGS_LIFECYCLE_IMPLEMENTATION_PLAN.md` | Original lifecycle plan. |

---

## Documentation Statistics

- **Total Files**: ~38 markdown files
- **Core Reports**: 3 (Final, Proposal, Progress)
- **Technical Guides**: 10+
- **Status**: 100% Complete

---

## Finding Documentation

### By User Role

**1. Data Consumer / Analyst**
- Start with **[Final Report](reports/final_report.md)** to understand the dataset.
- Use **[Data Dictionary](DATA_DICTIONARY.md)** to interpret fields.
- Check **[Script Documentation](SCRIPT_DOCUMENTATION.md)** if using `parquet` conversion tools.

**2. Pipeline Operator**
- Read **[User Guide](USER_GUIDE.md)** for daily tasks.
- Keep **[Snakemake Usage](SNAKEMAKE_WORKFLOW_USAGE.md)** open while running jobs.
- Refer to **[Operational Strategy](OPERATIONAL_STRATEGY.md)** for troubleshooting.

**3. Developer / Maintainer**
- **[Workflow Architecture](SNAKEMAKE_WORKFLOW_DESIGN.md)** is your bible.
- **[Script Documentation](SCRIPT_DOCUMENTATION.md)** explains the Python codebase.
- **[Test Results](WORKFLOW_INTEGRATION_TEST_RESULTS.md)** confirms system stability.

