# Workflow Integration Test Plan

## Overview

This document outlines the comprehensive integration testing strategy for the TFT Data Curation Snakemake workflow. The tests verify end-to-end functionality across all pipeline stages:

1. Data Collection
2. Validation
3. Transformation
4. Quality Assessment
5. Provenance Tracking
6. Backup
7. Cross-Cycle Validation

---

## Test Environment

### Test Data
- **Source**: Existing collection files in `data/raw/`
- **Test Dates**: 20251101, 20251102, 20251103, 20251104, 20251105
- **Rationale**: Using existing data avoids API rate limit consumption and ensures reproducible tests

### Prerequisites
- Snakemake installed and configured
- All workflow rules implemented (`workflow/rules/*.smk`)
- Test data available in `data/raw/`
- Python 3.8+ with required dependencies

---

## Test Scenarios

### Scenario 1: Single Date Execution

**Objective**: Verify workflow executes correctly for a single collection date

**Test Steps**:
1. Execute: `snakemake --config collection_date=20251101 -j 1`
2. Verify all outputs generated for date 20251101
3. Validate output content and structure

**Expected Outputs**:
- `data/raw/tft_collection_20251101.json` (already exists)
- `data/validated/tft_collection_20251101.json`
- `reports/validation_20251101.json`
- `data/transformed/tft_collection_20251101.jsonld`
- `reports/quality_20251101.json`
- `provenance/workflow_20251101.prov.json`
- `backups/backup_20251101.tar.gz`
- `reports/cross_cycle_20251101.json`

**Success Criteria**:
- Workflow completes without errors
- All 8 output files generated
- All files contain valid data structures
- Quality score >= 80%
- Cross-cycle validation report generated

---

### Scenario 2: Multiple Date Execution

**Objective**: Verify workflow handles multiple dates with parallel processing

**Test Steps**:
1. Execute: `snakemake --config collection_date=[20251102,20251103,20251104] -j 2`
2. Verify outputs for all three dates
3. Check parallel processing efficiency

**Expected Outputs**:
- All 8 output files for each of the 3 dates (24 files total)

**Success Criteria**:
- Workflow completes without errors
- All outputs generated for all dates
- Parallel processing works correctly (jobs run concurrently)
- Cross-cycle validation shows trends across dates
- No race conditions or file conflicts

---

### Scenario 3: Incremental Execution

**Objective**: Verify workflow only processes new dates (incremental updates)

**Test Steps**:
1. Ensure outputs exist for dates 20251101-20251104
2. Execute: `snakemake --config collection_date=20251105 -j 1`
3. Verify only new date is processed

**Expected Behavior**:
- Snakemake skips existing outputs (20251101-20251104)
- Only processes new date (20251105)
- Cross-cycle validation includes all dates

**Success Criteria**:
- Workflow completes quickly (only processes new date)
- Existing outputs unchanged
- New outputs generated for 20251105
- Cross-cycle validation updated with new date

---

### Scenario 4: Dry Run Validation

**Objective**: Verify workflow DAG is correct without executing

**Test Steps**:
1. Execute: `snakemake --config collection_date=[20251101,20251102,20251103] -n`
2. Review DAG structure and job dependencies

**Success Criteria**:
- Dry run completes without errors
- Correct number of jobs identified
- Dependencies properly ordered
- No circular dependencies

---

## Validation Criteria

### 1. Data Collection (`data/raw/tft_collection_{date}.json`)

**Checks**:
- File exists and is valid JSON
- Contains required top-level keys: `@context`, `players`, `matches`, `static_data`
- File size > 0 bytes
- Data structure matches expected schema

### 2. Validation (`data/validated/`, `reports/validation_{date}.json`)

**Checks**:
- Validated data file exists
- Validation report contains:
  - `validation.is_valid` (boolean)
  - `quality_score` (0.0-1.0)
  - `validation.errors` (list)
- Quality score >= 0.8 (80%)
- Validated data matches raw data structure

### 3. Transformation (`data/transformed/tft_collection_{date}.jsonld`)

**Checks**:
- File exists and is valid JSON-LD
- Contains `@context` with schema.org references
- Maintains data integrity from raw input
- Includes semantic metadata

### 4. Quality Assessment (`reports/quality_{date}.json`)

**Checks**:
- Quality report exists
- Contains metrics:
  - `overall_score` (0-100)
  - `completeness` score
  - `consistency` score
- Scores within valid ranges
- Detailed breakdown by category

### 5. Provenance Tracking (`provenance/workflow_{date}.prov.json`)

**Checks**:
- Provenance file exists and is valid W3C PROV
- Contains required elements:
  - Activities (data collection, transformation, etc.)
  - Entities (input/output files)
  - Agents (software, user)
- Includes temporal tracking:
  - `prov:startedAtTime`
  - `prov:endedAtTime`
- Relationships properly defined (`wasDerivedFrom`, `wasGeneratedBy`, etc.)

### 6. Backup (`backups/backup_{date}.tar.gz`)

**Checks**:
- Backup archive exists
- Archive is valid tar.gz format
- Contains expected files:
  - Raw data
  - Validated data
  - Transformed data
- Archive can be extracted successfully
- Integrity checksums valid (if included)

### 7. Cross-Cycle Validation (`reports/cross_cycle_{date}.json`)

**Checks**:
- Cross-cycle report exists
- Contains required sections:
  - `cycles_analyzed` (count)
  - `continuity_analysis` (player retention/churn)
  - `stability_analysis` (volume trends)
- Identifies expected patterns:
  - Player retention rates
  - Volume stability
  - Anomaly detection
- Report updates with each new collection

---

## Test Execution

### Automated Testing

**Command**:
```bash
python3 scripts/test_workflow_integration.py --dates 20251101,20251102,20251103,20251104,20251105
```

**What It Does**:
1. Runs dry-run validation
2. Executes single date test (20251101)
3. Executes multiple date test (20251102, 20251103, 20251104)
4. Verifies all outputs for each date
5. Generates comprehensive test report

**Output**:
- `Documents/no-tracking/WORKFLOW_INTEGRATION_TEST_RESULTS.md` (human-readable report)
- `Documents/no-tracking/WORKFLOW_INTEGRATION_TEST_RESULTS.json` (machine-readable results)

### Manual Testing

**Step-by-Step**:

1. **Clean Environment** (optional):
   ```bash
   # Backup existing outputs
   mkdir -p test_backup
   cp -r data/validated test_backup/
   cp -r data/transformed test_backup/
   cp -r reports test_backup/
   cp -r provenance test_backup/
   cp -r backups test_backup/
   ```

2. **Dry Run Test**:
   ```bash
   snakemake --config collection_date=[20251101,20251102,20251103] -n
   ```

3. **Single Date Test**:
   ```bash
   snakemake --config collection_date=20251101 -j 1
   ```

4. **Verify Outputs**:
   ```bash
   ls -lh data/validated/tft_collection_20251101.json
   ls -lh data/transformed/tft_collection_20251101.jsonld
   ls -lh reports/quality_20251101.json
   ls -lh reports/validation_20251101.json
   ls -lh reports/cross_cycle_20251101.json
   ls -lh provenance/workflow_20251101.prov.json
   ls -lh backups/backup_20251101.tar.gz
   ```

5. **Multiple Date Test**:
   ```bash
   snakemake --config collection_date=[20251102,20251103,20251104] -j 2
   ```

6. **Incremental Test**:
   ```bash
   snakemake --config collection_date=20251105 -j 1
   ```

---

## Success Criteria

### Overall Test Suite

- All test scenarios execute without errors
- All expected outputs generated for each test date
- Output files contain valid data structures
- Quality scores meet thresholds (>= 80%)
- Cross-cycle validation detects expected trends
- Provenance tracking is complete and W3C PROV compliant
- Backup archives are valid and restorable
- Test report documents all results comprehensively

### Performance Benchmarks

- Single date execution: < 5 minutes
- Multiple date execution (3 dates, parallel): < 10 minutes
- Incremental execution: < 3 minutes
- Dry run: < 30 seconds

---

## Troubleshooting

### Common Issues

**Issue**: Workflow fails with "Missing input files"
- **Cause**: Test data not in `data/raw/`
- **Solution**: Verify test data exists or adjust test dates

**Issue**: Cross-cycle validation fails
- **Cause**: Insufficient historical data
- **Solution**: Ensure at least 2 collection cycles exist

**Issue**: Backup creation fails
- **Cause**: Disk space or permissions
- **Solution**: Check available disk space and write permissions

**Issue**: Quality score below threshold
- **Cause**: Data quality issues in test data
- **Solution**: Review validation report for specific issues

---


## Next Steps

After successful integration testing:

1. **Review Results**: Analyze test report for any issues
2. **Address Failures**: Fix any failed tests
3. **Performance Optimization**: Optimize slow stages if needed
4. **Documentation Update**: Update workflow documentation with test results
5. **Production Deployment**: Deploy tested workflow for regular use

