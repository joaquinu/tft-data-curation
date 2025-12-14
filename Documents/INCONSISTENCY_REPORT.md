# Repository Inconsistency Report

**Generated**: December 2025  
**Scope**: Complete repository analysis for inconsistencies in file references, naming conventions, configurations, and documentation

---

## 1. File Path Reference Inconsistencies

### 1.1 Missing or Incorrect File References

| Referenced File | Actual Location | Status | Files Referencing |
|----------------|-----------------|--------|------------------|
| `Documents/BACKUP_SYSTEM.md` | `Documents/BACKUP_SYSTEM_MANUAL.md` | ❌ Wrong name | README.md (line 176, 416), USER_GUIDE.md (line 84) |
| `Documents/SNAKEMAKE_IMPLEMENTATION_GUIDE.md` | **File does not exist** | ❌ Missing | README.md (lines 113, 174), setup_snakemake.sh (line 49), workflow/README.md (lines 995, 1008) |
| `Documents/PHASE4_VERIFICATION_REPORT.md` | **File does not exist** | ❌ Missing | README.md (line 187) |
| `Documents/PHASE5_VERIFICATION_REPORT.md` | **File does not exist** | ❌ Missing | README.md (line 188) |
| `Documents/WORKFLOW_INTEGRATION_TEST_RESULTS.md` | `Documents/no-tracking/WORKFLOW_INTEGRATION_TEST_RESULTS.md` | ❌ Wrong path | DOCUMENTATION_INDEX.md (line 34), SNAKEMAKE_WORKFLOW_DESIGN.md (line 663) |

**Note**: The actual verification file is `Documents/no-tracking/ALL_PHASES_VERIFICATION_AND_SUMMARIES.md`, which consolidates all phase verifications.

### 1.2 Documentation Index Accuracy

The `DOCUMENTATION_INDEX.md` correctly lists files in `no-tracking/` but other documents reference them incorrectly.

---

## 2. Project Name Inconsistencies

### 2.1 Repository Name vs. Documentation

| Location | Uses | Should Be |
|----------|------|-----------|
| **Repository name** | `tft-data-curation` | ✅ Correct |
| README.md | `tft-data-extraction` | ❌ Should be `tft-data-curation` |
| Code URIs (schema.py, identifier_system.py, etc.) | `http://tft-data-extraction.com/` | ⚠️ Consider updating to match repo name |
| Hardcoded paths in scripts | `/Users/jugarte/Documents/tft-data-extraction` | ❌ Should use relative paths or config |

**Files with `tft-data-extraction` references:**
- `README.md` (lines 55, 95, 208)
- `Documents/SCRIPT_DOCUMENTATION.md` (line 907)
- `Documents/PROVENANCE_SCHEMA.md` (multiple URIs)
- `scripts/identifier_system.py` (line 219)
- `scripts/schema.py` (line 18)
- `scripts/base_infrastructure.py` (line 63)
- `workflow/rules/provenance.smk` (multiple URIs)
- `scripts/generate_long_term_report.py` (line 16) - **Hardcoded absolute path**
- `scripts/research_analysis.py` (line 172) - **Hardcoded absolute path**

---

## 3. Region Naming Inconsistencies

### 3.1 Case Sensitivity Issues

The codebase mixes uppercase (`LA2`, `LA1`) and lowercase (`la2`, `la1`) region codes inconsistently:

| File | Format Used | Issue |
|------|-------------|-------|
| `config/config.yaml` | `LA2` (uppercase) | Mixed with lowercase in same file |
| `config/snakemake_config.yaml` | `"la2"` (lowercase string) | Different from main config |
| `Documents/SNAKEMAKE_WORKFLOW_DESIGN.md` | `"la2"` (lowercase) | Documentation uses lowercase |
| `workflow/README.md` | `"la2"` (lowercase) | Workflow docs use lowercase |
| `scripts/config_manager.py` | `"LA2"` (uppercase) | Default uses uppercase |
| `Documents/DATA_DICTIONARY.md` | Both `"LA2"` and `"la2"` | Mixed examples |

**Impact**: This could cause configuration mismatches when switching between Snakemake workflow and direct script execution.

**Recommendation**: Standardize on lowercase (`la2`, `la1`) as Riot API typically uses lowercase region codes.

---

## 4. Configuration File Inconsistencies

### 4.1 Rate Limiting Configuration

| File | Setting | Value | Issue |
|------|---------|-------|-------|
| `config/config.yaml` | `rate_limiting.requests_per_2min` | `100` | Different structure |
| `config/snakemake_config.yaml` | `api.rate_limit` | `100` | Different key name |
| `workflow/README.md` | Documentation | `100` | Matches but different key |

**Issue**: Same value but different configuration keys make it unclear which takes precedence.

### 4.2 Region Configuration Structure

| File | Structure | Example |
|------|-----------|--------|
| `config/config.yaml` | `global.api.region: LA2` | Top-level global config |
| `config/snakemake_config.yaml` | `api.region: "la2"` | Direct api config |
| `config/config.yaml` (weekly) | `parameters.regions: [LA2]` | List format |

**Issue**: Three different ways to specify region across configs.

### 4.3 Collection Mode Values

| File | Allowed Values | Issue |
|------|----------------|-------|
| `config/snakemake_config.yaml` | `"weekly"` or `"incremental"` | Comment says script only accepts these |
| `config/config.yaml` | `daily`, `weekly`, `monthly` | Different set of modes |
| `scripts/automated_collection.py` | Unknown | Need to verify what it accepts |

**Issue**: Unclear which modes are actually supported by which components.

---

## 5. Documentation Structure Inconsistencies

### 5.1 File Organization

- **Active documentation** is in `Documents/`
- **Archived/legacy documentation** is in `Documents/no-tracking/`
- **Issue**: README.md references files in `Documents/` that are actually in `Documents/no-tracking/`

### 5.2 Documentation Index vs. Actual Files

The `DOCUMENTATION_INDEX.md` correctly categorizes files but:
- Lists `WORKFLOW_INTEGRATION_TEST_RESULTS.md` in main docs (line 34) but file is in `no-tracking/`

---

## 6. Code Hardcoded Paths

### 6.1 Absolute Paths in Code

| File | Line | Hardcoded Path | Issue |
|------|------|----------------|-------|
| `scripts/generate_long_term_report.py` | 16 | `/Volumes/joaquinu/UIUC 2/tft-data-extraction` | User-specific path |
| `scripts/research_analysis.py` | 172 | `/Users/jugarte/Documents/tft-data-extraction` | User-specific path |

**Issue**: These paths won't work for other users or on different systems.

---

## 7. URI/Namespace Inconsistencies

### 7.1 Schema URIs

Multiple files define schema URIs with `tft-data-extraction`:
- `Documents/PROVENANCE_SCHEMA.md`: `http://tft-data-extraction.com/schema#`
- `scripts/schema.py`: `http://tft-data-extraction.com/`
- `workflow/rules/provenance.smk`: `http://tft-data-extraction.com/workflow/...`

**Issue**: URIs use old project name instead of `tft-data-curation`.

---

## 8. Summary of Critical Issues

### High Priority (Breaks Functionality)

1. ❌ **Hardcoded absolute paths** in `generate_long_term_report.py` and `research_analysis.py`
2. ❌ **Missing file**: `SNAKEMAKE_IMPLEMENTATION_GUIDE.md` referenced in multiple places
3. ⚠️ **Region case mismatch** between config files could cause runtime errors

### Medium Priority (Confusing but Works)

2. ⚠️ **Wrong file name** for BACKUP_SYSTEM.md (should be BACKUP_SYSTEM_MANUAL.md)
3. ⚠️ **Project name inconsistency** (`tft-data-extraction` vs `tft-data-curation`)

### Low Priority (Cosmetic)

1. ⚠️ **URI namespaces** use old project name
2. ⚠️ **Configuration key naming** inconsistencies (rate_limit vs requests_per_2min)

---

## 9. Recommended Fixes

### Immediate Actions

1. **Fix file references in README.md**:
   - Update `BACKUP_SYSTEM.md` → `BACKUP_SYSTEM_MANUAL.md`

2. **Remove or create missing file**:
   - Either create `SNAKEMAKE_IMPLEMENTATION_GUIDE.md` or remove references
   - Update references to point to `SNAKEMAKE_WORKFLOW_DESIGN.md` or `SNAKEMAKE_WORKFLOW_USAGE.md`

3. **Fix hardcoded paths**:
   - Replace absolute paths with relative paths or config-based paths
   - Use `Path(__file__).parent` or similar for relative resolution

### Standardization Actions

1. **Standardize region codes**: Use lowercase (`la2`, `la1`) consistently
2. **Update project name**: Replace `tft-data-extraction` with `tft-data-curation` in documentation
3. **Standardize config keys**: Align rate limiting keys between config files
4. **Update URIs**: Consider updating schema URIs to match repository name (or keep as-is if they're published)

---

## 10. Files Requiring Updates

### Documentation Files
- `README.md` - Fix file paths and project name
- `Documents/USER_GUIDE.md` - Fix BACKUP_SYSTEM.md reference
- `setup_snakemake.sh` - Update or remove SNAKEMAKE_IMPLEMENTATION_GUIDE reference
- `workflow/README.md` - Update or remove SNAKEMAKE_IMPLEMENTATION_GUIDE reference

### Configuration Files
- `config/config.yaml` - Standardize region codes to lowercase
- `config/snakemake_config.yaml` - Align with main config structure

### Code Files
- `scripts/generate_long_term_report.py` - Remove hardcoded path
- `scripts/research_analysis.py` - Remove hardcoded path
- `scripts/schema.py` - Consider updating URI namespace
- `scripts/identifier_system.py` - Consider updating URI namespace
- `workflow/rules/provenance.smk` - Consider updating URI namespace

---

**End of Report**

