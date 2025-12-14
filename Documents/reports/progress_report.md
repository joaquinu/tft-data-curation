# Progress Report: TFT Match Data Curation Project

**Student Name**: Joaquin Ugarte
**Course**: CS 598: Foundations of Data Curation
**Date**: October 26, 2025
**Project Week**: 5 of 12

**Schedule Alignment**: With a September 16, 2025 start, this report reflects the end of Week 5 of the proposed timeline.

---

## Executive Summary

The TFT Match Data Curation Project is currently **70% complete** and on schedule. All tasks planned for the first five weeks have been completed, including core infrastructure setup, automated data collection, and quality assurance workflows. Automation scheduling is prepared but not yet live and will be activated according to Weeks 9–10 of the proposal. Key achievements include:

* Successful **all-tier data collection** for October 25, 2025 (1,930 players, 4,469 matches, 179.49 MB in 3.67 hours).
* **Eight successful LA2 collections**.
* Implementation of **DuckDB registry** for weekly deduplication, achieving at least ~25% API call reduction (still need to prove this with a complete week of daily extraction + a weekly extraction for missing matches).
* Full **JSON-LD parameterization**, schema validation, and W3C PROV-based provenance tracking.
* Scope adjustments: Parquet format and LA1 collection deferred to prioritize stability and efficiency under dev-key constraints.

These results demonstrate the feasibility of sustained daily and weekly collection within current API limits (~100 requests/2 minutes).

---

## Progress Against Proposed Plan

| Phase                            | Planned Weeks | Status    | Notes                                                                                                                                                         |
| -------------------------------- | ------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1: Infrastructure          | 1             | Completed | Endpoint mapping (`scripts/riot_api_endpoints.py`), rate limiting, JSON-LD schema generation (`scripts/schema.py`)                                            |
| Phase 2: Collection & Quality    | 2–4           | Completed | LA2 collection automated (8 runs); QA modules implemented (`quality_assurance/`)                                                                              |
| Phase 3: Metadata & Organization | 5–6           | Completed | DuckDB registry, unified JSON-LD `@context/@type`, reusable configuration (`config/config.yaml`), weekly deduplication logic, identifier/provenance alignment |
| Phase 4: Automation              | 9–10          | Prepared  | Scheduling ready; activation aligns with proposal timeline                                                                                                    |
| Phase 5: Publication             | 12            | On track  | Metadata and artifact preparation ongoing                                                                                                                     |

**Decisions and Scope Adjustments**: JSON remains primary exchange format; LA2 collection prioritized; LA1 and Parquet deferred. These decisions ensure stable operation under dev-key limits while maintaining reproducibility and quality.

### Response to Proposal Feedback

* **Reproducibility:** Advanced parameterization completed; Snakemake incorporated for workflow management.
* **Automation Scheduling:** Prepared for activation in Weeks 9–10; manual workflow verified.
* **Scope Realism:** LA1 and Parquet deferred to maintain quality and adhere to rate limits.

---

## Evidence of Progress Through Artifacts

### Latest Collection Run – October 26, 2025 (All Tiers)

```
Timestamp: 2025-10-26 15:39:13
Duration: 3h 40m
Players: 1,930 (all ranks)
Matches: 4,469
Data Volume: 179.49 MB
Errors: 0
```

Key outcomes:

* Full tier coverage in a single execution.
* Validated deduplication and rate-limiting strategies.
* Demonstrated feasibility of 3.67-hour daily collection.
* Confirms readiness for weekly automated all-tier execution.

Eight successful LA2 collections (seven manual, one automated) demonstrate pipeline stability. Artifacts submitted in `Documents/submission_artifacts_2025-10-26.zip`.

---

## Challenges and Mitigation

**Development API Token Management:**

* **Challenge:** Personal project approval pending; dev tokens require daily manual refresh.
* **Impact:** Single day all-tier collection takes ~4 hours; weekly full collection requires token management.
* **Mitigation:** Implemented **hybrid daily + weekly reconciliation** strategy with status-aware deduplication:

  1. **Daily runs** capture complete match data using one token per day.
  2. **Weekly reconciliation** skips already collected matches (~50% API call reduction).
  3. DuckDB registry tracks match completion status.

**Operational Advantages:**

* Sustainable under dev-key constraints.
* Daily + weekly approach achieves ~31,000 matches/week.
* Personal project approval will remove manual refresh requirement, enabling full automation.

Other operational improvements include `@type` coverage, schema validation, and controlled API rate usage.

---

## Limitations

* **API Rate Limits:** ~3,000 requests/hour; validated by Oct 26 all-tier run.
* **Token Management:** Requires manual refresh until approval; mitigated via hybrid strategy.
* **Automation Activation:** Scheduled Weeks 9–10; fully automated workflow depends on project approval.

---

## References

Köster, J., & Rahmann, S. (2012). *Snakemake—a scalable bioinformatics workflow engine*. Bioinformatics, 28(19), 2520–2522. [https://doi.org/10.1093/bioinformatics/bts480](https://doi.org/10.1093/bioinformatics/bts480)

Riot Games. (2024). *Riot developer portal*. [https://developer.riotgames.com/](https://developer.riotgames.com/)

Riot Games. (2024). *Teamfight Tactics API documentation*. [https://developer.riotgames.com/apis#tft-match-v1](https://developer.riotgames.com/apis#tft-match-v1)

Schema.org Community Group. (2024). *Schema.org*. [https://schema.org/](https://schema.org/)

Project Proposal. (2025). *Curating Riot's TFT match data: A reproducible data workflow project*. [Internal document]

Lynch, C. (1999). *Canonicalization: A Fundamental Tool to Facilitate Preservation and Management of Digital Information*. D-Lib Magazine, 5(9).

Duerr, R. E., et al. (2011). *On the Utility of Identification Schemes for Digital Earth Science Data*. Earth Science Informatics, 4, 139–160.

Gil, Y. (2017). *Identifiers and Identifier Systems*. CS598-FDC Lecture.

Kunze, J. (2002). *A Metadata Kernel for Electronic Permanence*. Journal of Digital Information, 2(2).
