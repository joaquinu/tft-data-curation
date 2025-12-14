# Creating Your Final Report Submission Artifact

This guide explains how to create a comprehensive archive package for your final report submission.

---

## Quick Start: Create Submission Archive

### Option 1: Using Snakemake (Recommended - Easiest)

This method automatically includes all required documentation and creates a complete archive:

```bash
# Create archive for your final submission
snakemake archive_release --cores 1 \
    --config date=20251214 \
    version=1.0.0 \
    archive_description="Final Report Submission - TFT Data Curation Project"
```

**What this includes:**
- ✅ Data files from `data/raw/tft_collection_{date}.json`
- ✅ Documentation: `DATA_DICTIONARY.md`, `final_report.md`, `README.md`, `LICENSE`
- ✅ Metadata: `manifest.json` with checksums
- ✅ Archive README with citation information
- ✅ SHA-256 checksum file for integrity verification

**Output:**
- `archives/tft_data_archive_v1.0.0_20251214.tar.gz`
- `archives/tft_data_archive_v1.0.0_20251214.tar.gz.sha256`

---

### Option 2: Using archive_manager.py Directly (More Control)

If you want to include multiple data files or customize what's included:

```bash
# Create archive with specific data files
python3 scripts/archive_manager.py \
    --version 1.0.0 \
    --description "Final Report Submission - TFT Data Curation Project" \
    --data data/raw/tft_collection_20251214.json \
           data/parquet/matches.parquet \
           data/parquet/participants.parquet \
    --output final_submission_archive.tar.gz
```

**What this includes:**
- ✅ All data files you specify with `--data`
- ✅ Required documentation (automatically included)
- ✅ Metadata and checksums
- ✅ Archive README

---

## What Gets Included in the Archive

The archive creates a self-contained package with this structure:

```
tft_archive_v1.0.0/
├── ARCHIVE_README.txt          # Human-readable archive information
├── data/
│   └── tft_collection_20251214.json  # Your data files
├── documentation/
│   ├── DATA_DICTIONARY.md      # Field-level documentation
│   ├── final_report.md         # Your final report
│   ├── README.md               # Project overview
│   └── LICENSE                 # License file
└── metadata/
    ├── manifest.json            # Complete file manifest with checksums
    └── governance_policy.json   # Governance metadata (if available)
```

---

## For Course Submission

### Recommended: Create a Complete Project Archive

For your final report submission, you may want to create an archive that includes **all project artifacts**, not just data. Here's how:

#### Step 1: Create a Submission-Specific Archive Script

Create a file `create_submission_archive.sh`:

```bash
#!/bin/bash
# Create comprehensive submission archive

VERSION="1.0.0"
DATE=$(date +%Y%m%d)
ARCHIVE_NAME="tft_data_curation_final_submission_${DATE}.tar.gz"

echo "Creating submission archive: ${ARCHIVE_NAME}"

# Create temporary staging directory
STAGING_DIR="submission_staging"
rm -rf ${STAGING_DIR}
mkdir -p ${STAGING_DIR}

# Copy essential project files
echo "Copying project files..."

# Source code
cp -r scripts ${STAGING_DIR}/
cp -r quality_assurance ${STAGING_DIR}/
cp -r workflow ${STAGING_DIR}/
cp -r tests ${STAGING_DIR}/

# Configuration
cp -r config ${STAGING_DIR}/

# Documentation (exclude no-tracking for cleaner submission)
mkdir -p ${STAGING_DIR}/Documents
cp Documents/*.md ${STAGING_DIR}/Documents/ 2>/dev/null || true
cp -r Documents/reports ${STAGING_DIR}/Documents/

# Root files
cp README.md ${STAGING_DIR}/
cp LICENSE ${STAGING_DIR}/
cp requirements.txt ${STAGING_DIR}/
cp Snakefile ${STAGING_DIR}/

# Sample data (optional - include one collection as example)
mkdir -p ${STAGING_DIR}/data/raw
# Copy your most recent or best collection
# cp data/raw/tft_collection_20251214.json ${STAGING_DIR}/data/raw/ 2>/dev/null || true

# Create archive
echo "Compressing archive..."
tar -czf ${ARCHIVE_NAME} -C ${STAGING_DIR} .

# Calculate checksum
sha256sum ${ARCHIVE_NAME} > ${ARCHIVE_NAME}.sha256

# Cleanup
rm -rf ${STAGING_DIR}

echo ""
echo "✅ Submission archive created: ${ARCHIVE_NAME}"
echo "✅ Checksum file: ${ARCHIVE_NAME}.sha256"
echo ""
echo "Archive size: $(du -h ${ARCHIVE_NAME} | cut -f1)"
echo "SHA-256: $(cat ${ARCHIVE_NAME}.sha256 | cut -d' ' -f1)"
```

#### Step 2: Run the Script

```bash
chmod +x create_submission_archive.sh
./create_submission_archive.sh
```

---

## Alternative: Use Archive Manager for Data-Only Submission

If your submission should focus on the **data artifact** (as required by some courses), use the Snakemake method:

```bash
# Use your most recent or best collection
snakemake archive_release --cores 1 \
    --config date=20251214 \
    version=1.0.0 \
    archive_description="Final Report Submission - TFT Match Data Collection"
```

This creates a **publication-ready data archive** that includes:
- Your collected data
- Complete documentation
- Provenance metadata
- Integrity verification

---

## Verification

After creating your archive, verify it:

```bash
# Extract and verify
tar -tzf archives/tft_data_archive_v1.0.0_20251214.tar.gz

# Verify checksum
sha256sum -c archives/tft_data_archive_v1.0.0_20251214.tar.gz.sha256

# Check contents
tar -xzf archives/tft_data_archive_v1.0.0_20251214.tar.gz
ls -la tft_archive_v1.0.0/
```

---

## What to Submit

### For Data Curation Course Submission:

1. **Data Archive** (created with `archive_release`):
   - `archives/tft_data_archive_v1.0.0_YYYYMMDD.tar.gz`
   - `archives/tft_data_archive_v1.0.0_YYYYMMDD.tar.gz.sha256`

2. **Final Report**:
   - `Documents/reports/final_report.md`

3. **Supporting Documentation** (optional but recommended):
   - `Documents/DATA_DICTIONARY.md`
   - `Documents/USER_GUIDE.md`
   - `README.md`

### For Complete Project Submission:

Submit the entire repository as a `.zip` or `.tar.gz` file, or use the comprehensive archive script above.

---

## Quick Reference

| Method | Use Case | Command |
|--------|----------|---------|
| **Snakemake** | Data archive with documentation | `snakemake archive_release --config date=YYYYMMDD version=1.0.0` |
| **archive_manager.py** | Custom data files | `python3 scripts/archive_manager.py --version 1.0.0 --data file1.json file2.json --description "..."` |
| **Custom Script** | Complete project archive | Use `create_submission_archive.sh` above |

---

## Troubleshooting

### Issue: "Data file not found"
**Solution**: Make sure the data file exists:
```bash
ls -la data/raw/tft_collection_20251214.json
```

### Issue: "Documentation missing"
**Solution**: Verify required docs exist:
```bash
ls Documents/DATA_DICTIONARY.md Documents/reports/final_report.md README.md LICENSE
```

### Issue: Archive too large
**Solution**: Exclude large data files or use compression:
```bash
# Exclude large backups/logs
tar --exclude='backups' --exclude='logs' -czf archive.tar.gz .
```

---

## Next Steps

1. ✅ Create your archive using one of the methods above
2. ✅ Verify the archive contents
3. ✅ Test extracting the archive on a different machine
4. ✅ Submit according to your course requirements

---

**Last Updated**: December 2025

