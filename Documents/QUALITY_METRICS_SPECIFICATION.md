# Data Quality Metrics Specification

**Implementation**: `quality_assurance/quality_metrics.py`

---

## 1. Overview

This document specifies the comprehensive quality assessment model used for the TFT Data Curation project. The quality score (0-100) provides a quantitative measure of dataset reliability, completeness, and structural integrity.

The model is designed to be:
- **Security-Aware**: Sensitive fields like API keys are explicitly excluded from completeness checks.
- **Context-Aware**: Matches involving unranked players are not penalized for missing ranked statistics.
- **Robust**: It accounts for transient API failures while enforcing strict structural validation.

---

## 2. Quality Score Component Weights

The overall quality score is a weighted average of five key components:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Completeness** | 25% | Presence of required fields (security/context aware). |
| **Consistency** | 20% | Data consistency across logical sections. |
| **Accuracy** | 20% | Validity of values (e.g., placements 1-8, levels 1-10). |
| **Integrity** | 15% | Player-match relationship integrity. |
| **Structure** | 20% | Tree-based hierarchical validation (Collection → Players → Matches). |

### Structure Component
The **Structure** component (20%) implements tree-based hierarchical validation. It verifies:
- The integrity of the root `TFTDataCollection` structure.
- The recursive validity of `Match` → `Participants` → `Units`/`Traits`.
- Cross-hierarchy linkages between `Players` and their `Matches`.

---

## 3. Field Requirements

### Required Fields (Must be present)
These fields are mandatory for data to be considered complete:
- `collectionInfo.timestamp`
- `collectionInfo.extractionLocation`
- `collectionInfo.dataVersion`
- `player.puuid`
- `player.leaguePoints`

### Optional Fields (Excluded from penalties)
The following fields are treated as optional based on specific rationale:

| Field | Rationale |
|-------|-----------|
| `collectionInfo.apiKey` | **Security**: API keys are strictly excluded from storage. |
| `player.summonerId` | **Reliability**: Summmoner V4 API endpoints may fail independently of match data. |
| `player.summonerLevel` | **Reliability**: May fail to fetch if Summoner API is unstable. |
| `player.tier` | **Context**: Only exists for players with ranked history. |
| `player.rank` | **Context**: Only exists for players with ranked history. |

---

## 4. Validation Logic

### Tree-Based Validation
The system uses `quality_assurance/tree_validator.py` to perform deep structural checks. A dataset must satisfy the JSON-LD schema hierarchy:
1. **Root Integration**: Validates high-level keys (`players`, `matches`, `collectionInfo`).
2. **Entity Integrity**: Ensures every `puuid` in `matches` exists in the `players` registry.
3. **Leaf Validity**: Checks that nested arrays (`units`, `traits`) are well-formed.

### Handling API Failures
To improve robustness, the collection pipeline implements the following strategies:
1. **Retry Logic**: API calls for player details are retried twice before fallback.
2. **Leaderboard Fallback**: If the Summmoner API fails, data is backfilled from pre-fetched leaderboard snapshots where possible.
3. **Graceful Degradation**: Missing optional fields do not fail the batch but are noted in logs.

---

## 5. Quality Grading Scale

Based on the calculated score, datasets are assigned a quality grade:

| Score Range | Grade | Definition |
|-------------|-------|------------|
| **90 - 100** | **A** | **High Quality**: Complete, consistent, and structurally perfect. |
| **80 - 89** | **B** | **Good**: High completeness with minor non-critical gaps. |
| **70 - 79** | **C** | **Acceptable**: Structurally sound but may lack optional context. |
| **< 70** | **D/F** | **Poor**: Significant data loss or structural corruption. |

**Current Baseline Performance**:
- **Completeness**: ~100% (Weighted)
- **Structure**: >94%
- **Overall Grade**: A (Typical score > 96.0)

---

## 6. Conclusion

The implemented quality model ensures that the dataset is assessed fairly and rigorously. By decoupling security concerns and API instability from the core quality score, the system provides a true reflection of the data's utility for analysis while maintaining high standards for structural integrity.

