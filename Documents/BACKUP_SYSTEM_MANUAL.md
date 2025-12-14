# Automated Backup System Documentation


## Overview

The automated backup system provides comprehensive data preservation capabilities for the TFT Data Curation Project. It includes automated backups, integrity verification, retention policies, and recovery procedures.

---

## Features

### Core Capabilities

1. **Automated Backups**
   - Full, incremental, and differential backup strategies
   - Compressed archives (gzip)
   - Automatic backup after workflow completion
   - Configurable backup frequency

2. **Integrity Verification**
   - SHA-256 checksum calculation
   - Automatic verification after backup creation
   - Verification before restore operations
   - Checksum stored in metadata

3. **Retention Management**
   - Configurable retention periods
   - Automatic cleanup of old backups
   - Retention policies by backup type

4. **Recovery Procedures**
   - Restore from backup archives
   - Verification before restore
   - Metadata tracking for all backups

---

## Architecture

### Components

1. **`scripts/backup_system.py`** - Core backup functionality
2. **`workflow/rules/backup.smk`** - Snakemake workflow integration
3. **`config/snakemake_config.yaml`** - Backup configuration

### Backup Flow

```
Workflow Completion
       ↓
   [create_backup]
       ↓
  Compress Files
       ↓
  Calculate Checksum
       ↓
  Save Metadata
       ↓
  Verify Backup
       ↓
  Backup Complete
```

---

## Usage

### Automatic Backup (Recommended)

Backups are automatically created after workflow completion when `auto_backup: true` in config:

```bash
# Run workflow - backup created automatically
snakemake --cores 4 --config collection_date=20251115
```

### Manual Backup

#### Create a Backup

```bash
# Full backup
python3 scripts/backup_system.py \
    --backup-dir backups \
    --source data/raw data/validated data/transformed provenance reports \
    --type full \
    --verify

# Incremental backup
python3 scripts/backup_system.py \
    --backup-dir backups \
    --source data/raw \
    --type incremental \
    --name incremental_backup_20251115
```

#### List Backups

```bash
python3 scripts/backup_system.py --backup-dir backups --list
```

#### Verify Backup

```bash
# Verification is automatic during creation with --verify flag
# Manual verification can be done via Snakemake rule:
snakemake verify_backup --config collection_date=20251115
```

#### Restore Backup

```bash
python3 scripts/backup_system.py \
    --backup-dir backups \
    --restore backups/backup_full_20251115.tar.gz \
    --restore-dir restored
```

#### Cleanup Old Backups

```bash
# Remove backups older than 730 days (2 years)
python3 scripts/backup_system.py \
    --backup-dir backups \
    --cleanup 730
```

### Snakemake Integration

#### Create Backup Rule

```bash
snakemake create_backup --config collection_date=20251115
```

#### Verify Backup Rule

```bash
snakemake verify_backup --config collection_date=20251115
```

#### Cleanup Rule

```bash
snakemake cleanup_old_backups --config collection_date=20251115
```

---

## Configuration

### Snakemake Config (`config/snakemake_config.yaml`)

```yaml
backup:
  enabled: true
  type: "full"  # full, incremental, differential
  retention_days: 730  # 2 years
  verify_integrity: true
  compression: "gzip"
  compression_level: 6
  auto_backup: true  # Automatically backup after workflow completion
```

### Backup Types

1. **Full Backup**
   - Complete backup of all specified files
   - Use case: Initial backup, weekly/monthly backups
   - Retention: 2 years (configurable)

2. **Incremental Backup**
   - Only files changed since last backup
   - Use case: Daily backups
   - Retention: 30 days (configurable)

3. **Differential Backup**
   - All changes since last full backup
   - Use case: Weekly backups
   - Retention: 6 months (configurable)

---

## Backup Contents

### What Gets Backed Up

- **Raw Data**: `data/raw/tft_collection_{date}.json`
- **Validated Data**: `data/validated/tft_collection_{date}.json`
- **Transformed Data**: `data/transformed/tft_collection_{date}.jsonld`
- **Quality Reports**: `reports/quality_{date}.json`
- **Provenance**: `provenance/workflow_{date}.prov.json`
- **Configuration**: `config/snakemake_config.yaml`

### Backup Structure

```
backups/
├── backup_full_20251115.tar.gz
├── backup_full_20251115_metadata.json
├── backup_incremental_20251116.tar.gz
├── backup_incremental_20251116_metadata.json
└── verification_full_20251115.json
```

### Metadata Format

```json
{
  "backup_name": "backup_full_20251115",
  "backup_type": "full",
  "backup_path": "backups/backup_full_20251115.tar.gz",
  "backup_date": "2025-11-15T23:30:00",
  "source_paths": [
    "data/raw/tft_collection_20251115.json",
    "data/validated/tft_collection_20251115.json",
    ...
  ],
  "file_count": 6,
  "total_size_bytes": 9437184,
  "compression": "gz",
  "compression_level": 6,
  "checksum": "a1b2c3d4e5f6...",
  "checksum_algorithm": "sha256",
  "backup_size_bytes": 3145728,
  "compression_ratio": 3.0
}
```

---

## Retention Policies

### Default Retention

| Backup Type | Retention Period | Rationale |
|-------------|------------------|-----------|
| Full | 730 days (2 years) | Long-term preservation |
| Incremental | 30 days | Quick recovery window |
| Differential | 180 days (6 months) | Medium-term retention |

### Custom Retention

Configure in `config/snakemake_config.yaml`:

```yaml
backup:
  retention_days: 365  # 1 year
```

---

## Integrity Verification

### Automatic Verification

- Checksum calculated during backup creation
- Verification performed automatically with `--verify` flag
- Checksum stored in metadata file

### Manual Verification

```bash
# Via Python script
python3 -c "
from scripts.backup_system import BackupSystem
from pathlib import Path

backup_system = BackupSystem()
backup_path = Path('backups/backup_full_20251115.tar.gz')
metadata_path = Path('backups/backup_full_20251115_metadata.json')

# Load expected checksum
import json
with open(metadata_path) as f:
    metadata = json.load(f)
    expected_checksum = metadata['checksum']

# Verify
if backup_system.verify_backup(backup_path, expected_checksum):
    print('✅ Backup is valid')
else:
    print('❌ Backup verification failed')
"
```

---

## Recovery Procedures

### Restore from Backup

1. **Verify Backup Integrity**
   ```bash
   python3 scripts/backup_system.py \
       --backup-dir backups \
       --restore backups/backup_full_20251115.tar.gz \
       --restore-dir restored \
       --verify
   ```

2. **Restore Files**
   ```bash
   # Files will be extracted to restored/ directory
   # Maintains original directory structure
   ```

3. **Validate Restored Data**
   ```bash
   # Check file integrity
   # Verify checksums if available
   # Test data access
   ```

### Disaster Recovery

1. **Identify Latest Valid Backup**
   ```bash
   python3 scripts/backup_system.py --backup-dir backups --list
   ```

2. **Restore from Backup**
   ```bash
   python3 scripts/backup_system.py \
       --restore backups/backup_full_20251115.tar.gz \
       --restore-dir restored
   ```

3. **Verify Restored Data**
   - Check file counts
   - Verify checksums
   - Test data access

4. **Merge with Existing Data** (if needed)
   - Compare restored data with current data
   - Merge if necessary
   - Update metadata

---

## Best Practices

### Backup Strategy

1. **Full Backups**: Weekly or monthly
2. **Incremental Backups**: Daily (if needed)
3. **Differential Backups**: Weekly (alternative to incremental)

### Storage Recommendations

1. **Local Storage**: Primary backup location
2. **External Drive**: Secondary backup (manual)
3. **Cloud Storage**: Long-term archive (future enhancement)

### Monitoring

1. **Check Backup Logs**: `logs/backup_{date}.log`
2. **Verify Backup Integrity**: Regular verification
3. **Monitor Storage**: Ensure sufficient space
4. **Review Retention**: Clean up old backups regularly

---

## Troubleshooting

### Common Issues

#### Issue 1: Backup Creation Fails

**Error**: `No files found to backup`

**Solution**:
- Verify source paths exist
- Check file permissions
- Ensure files are not empty

#### Issue 2: Checksum Mismatch

**Error**: `Checksum mismatch during verification`

**Solution**:
- Backup file may be corrupted
- Recreate backup
- Check disk space and permissions

#### Issue 3: Restore Fails

**Error**: `Failed to open archive`

**Solution**:
- Verify backup file is not corrupted
- Check file permissions
- Ensure sufficient disk space

---

## Future Enhancements

### Planned Features

1. **Cloud Backup Integration**
   - AWS S3 support
   - Google Cloud Storage support
   - Azure Blob Storage support

2. **Incremental Backup Logic**
   - Track file changes
   - Only backup modified files
   - Reduce backup size

3. **Backup Scheduling**
   - Cron integration
   - Snakemake scheduling
   - Automated cleanup

4. **Backup Encryption**
   - Optional encryption for sensitive data
   - Key management
   - Secure storage

---

## Examples

### Example 1: Full Backup After Workflow

```bash
# Run workflow with automatic backup
snakemake --cores 4 --config collection_date=20251115

# Backup automatically created:
# backups/backup_full_20251115.tar.gz
```

### Example 2: Manual Incremental Backup

```bash
python3 scripts/backup_system.py \
    --backup-dir backups \
    --source data/raw/tft_collection_20251115.json \
    --type incremental \
    --name incremental_20251115 \
    --verify
```

### Example 3: List and Cleanup

```bash
# List all backups
python3 scripts/backup_system.py --backup-dir backups --list

# Cleanup backups older than 1 year
python3 scripts/backup_system.py --backup-dir backups --cleanup 365
```

