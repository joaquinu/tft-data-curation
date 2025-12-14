# workflow/rules/backup.smk
# Data Backup and Preservation Rule

import os
from pathlib import Path

rule create_backup:
    """
    Create automated backup of workflow outputs.
    
    This rule creates a compressed backup archive of all workflow outputs
    including raw data, validated data, transformed data, provenance, and reports.
    """
    input:
        # All workflow outputs to backup
        raw_data="data/raw/tft_collection_{date}.json",
        validated_data="data/validated/tft_collection_{date}.json",
        transformed_data="data/transformed/tft_collection_{date}.jsonld",
        quality_report="reports/quality_{date}.json",
        provenance="provenance/workflow_{date}.prov.json",
        config_file="config/snakemake_config.yaml"
    output:
        backup_archive="backups/backup_{date}.tar.gz",
        backup_metadata="backups/backup_{date}_metadata.json"
    params:
        backup_type=lambda wildcards: config.get("backup", {}).get("type", "full"),
        backup_dir="backups"
    log:
        "logs/backup_{date}.log"
    shell:
        """
        # Ensure backup directory exists
        mkdir -p {params.backup_dir}
        
        # Create backup using Python script
        python3 scripts/backup_system.py \
            --backup-dir {params.backup_dir} \
            --source {input.raw_data} {input.validated_data} {input.transformed_data} {input.quality_report} {input.provenance} {input.config_file} \
            --type {params.backup_type} \
            --name backup_{wildcards.date} \
            --verify \
            2>&1 | tee {log}
        
        # Verify backup was created
        if [ ! -f {output.backup_archive} ]; then
            echo "[ERROR] Backup archive not created" >&2
            exit 1
        fi
        
        # Show backup file size
        BACKUP_SIZE=$(du -h {output.backup_archive} | cut -f1)
        echo "[SUCCESS] Backup created: {output.backup_archive} ({{BACKUP_SIZE}})"
        
        # Verify metadata file was created
        if [ ! -f {output.backup_metadata} ]; then
            echo "[WARNING] Backup metadata file not created" >&2
        else
            echo "[SUCCESS] Backup metadata: {output.backup_metadata}"
        fi
        """

rule verify_backup:
    """
    Verify backup integrity.
    
    This rule verifies that a backup archive is valid and can be restored.
    """
    input:
        backup_archive="backups/backup_{date}.tar.gz",
        backup_metadata="backups/backup_{date}_metadata.json"
    output:
        verification_report="backups/verification_{date}.json"
    log:
        "logs/verify_backup_{date}.log"
    shell:
        """
        # Extract expected checksum from metadata
        EXPECTED_CHECKSUM=$(python3 -c "
        import json
        with open('{input.backup_metadata}', 'r') as f:
            metadata = json.load(f)
            print(metadata.get('checksum', ''))
        ")
        
        # Verify backup
        python3 -c "
        import sys
        from pathlib import Path
        from scripts.backup_system import BackupSystem
        
        backup_system = BackupSystem()
        backup_path = Path('{input.backup_archive}')
        
        if backup_system.verify_backup(backup_path, '$EXPECTED_CHECKSUM'):
            print('[SUCCESS] Backup verification successful')
            sys.exit(0)
        else:
            print('[ERROR] Backup verification failed')
            sys.exit(1)
        " 2>&1 | tee {log}
        
        # Create verification report
        python3 -c "
        import json
        from pathlib import Path
        from datetime import datetime
        
        report = {{
            'backup_path': '{input.backup_archive}',
            'verification_date': datetime.now().isoformat(),
            'status': 'verified',
            'checksum_match': True
        }}
        
        with open('{output.verification_report}', 'w') as f:
            json.dump(report, f, indent=2)
        "
        """

rule cleanup_old_backups:
    """
    Clean up old backups based on governance retention policies.
    
    This rule removes backups older than the retention period specified by
    governance policies (from governance_policies.py) or config fallback.
    """
    params:
        retention_days=lambda wildcards: config.get("backup", {}).get("retention_days", 730),
        backup_dir="backups"
    output:
        cleanup_report="backups/cleanup_{date}.json"
    log:
        "logs/cleanup_backups_{date}.log"
    shell:
        """
        # Run cleanup with governance policy integration
        python3 -c "
        import json
        import sys
        from pathlib import Path
        from datetime import datetime
        
        sys.path.insert(0, str(Path('.').resolve()))
        
        from scripts.backup_system import BackupSystem
        from scripts.governance_policies import get_governance_policy
        
        # Get governance policy for dataset retention
        governance = get_governance_policy()
        dataset_policy = governance.get_retention_policy('dataset_snapshots')
        
        # Use governance policy retention if available, otherwise use config
        if dataset_policy and dataset_policy.retention_period.value != 'permanent':
            retention_days = governance._get_retention_days(dataset_policy.retention_period)
            print(f'Using governance retention policy: {{retention_days}} days')
        else:
            retention_days = {params.retention_days}
            print(f'Using config retention: {{retention_days}} days')
        
        # Run cleanup
        backup_system = BackupSystem(backup_dir='{params.backup_dir}')
        removed_count = backup_system.cleanup_old_backups(retention_days)
        
        # Create cleanup report with governance info
        report = {{
            'cleanup_date': datetime.now().isoformat(),
            'retention_days': retention_days,
            'backups_removed': removed_count,
            'governance_policy_applied': dataset_policy.to_dict() if dataset_policy else None,
            'status': 'completed'
        }}
        
        with open('{output.cleanup_report}', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f'[SUCCESS] Cleanup completed: {{removed_count}} backups removed')
        " 2>&1 | tee {log}
        """

rule archive_release:
    """
    Create a long-term preservation archive (Release Package).
    
    This rule creates a self-contained archive with data, documentation, and metadata
    suitable for long-term preservation and publication.
    
    Usage: snakemake archive_release --config date=20251105 version=1.0.0 archive_description="TFT Set 12 Data"
    
    Required config parameters:
    - date: Collection date (e.g., 20251105)
    - version: Archive version (e.g., 1.0.0)
    - archive_description: Description of the archive content
    """
    input:
        data_dict="Documents/DATA_DICTIONARY.md",
        final_report="Documents/reports/final_report.md",
        readme="README.md",
        license="LICENSE"
    run:
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        # Get config parameters
        date = config.get("date")
        version = config.get("version", "1.0.0")
        description = config.get("archive_description", "TFT Match Data Collection")
        
        if not date:
            print("[ERROR] 'date' parameter is required. Use --config date=20251105", file=sys.stderr)
            sys.exit(1)
        
        # Define paths
        data_file = f"data/raw/tft_collection_{date}.json"
        archive_name = f"tft_data_archive_v{version}_{date}.tar.gz"
        log_file = f"logs/archive_{version}_{date}.log"
        
        # Validate all input files exist
        missing_files = []
        if not Path(data_file).exists():
            missing_files.append(data_file)
        if not Path('{input.data_dict}').exists():
            missing_files.append('{input.data_dict}')
        if not Path('{input.final_report}').exists():
            missing_files.append('{input.final_report}')
        if not Path('{input.readme}').exists():
            missing_files.append('{input.readme}')
        if not Path('{input.license}').exists():
            missing_files.append('{input.license}')
        
        if missing_files:
            print(f"[ERROR] Required input files not found:", file=sys.stderr)
            for file in missing_files:
                print(f"  - {file}", file=sys.stderr)
            sys.exit(1)
        
        # Create archives directory
        Path("archives").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Run archive_manager.py
        cmd = [
            "python3", "scripts/archive_manager.py",
            "--version", version,
            "--description", description,
            "--data", data_file,
            "--output", archive_name
        ]
        
        print(f"[INFO] Creating archive: {archive_name}")
        print(f"   Version: {version}")
        print(f"   Date: {date}")
        print(f"   Description: {description}")
        
        # Execute command and capture output
        with open(log_file, "w") as log:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            log.write(result.stdout)
            print(result.stdout)
            
            if result.returncode != 0:
                print(f"[ERROR] Archive creation failed. See {log_file} for details.", file=sys.stderr)
                sys.exit(1)
        
        # Verify outputs
        archive_path = Path(f"archives/{archive_name}")
        checksum_path = Path(f"archives/{archive_name}.sha256")
        
        if not archive_path.exists():
            print(f"[ERROR] Archive not created at {archive_path}", file=sys.stderr)
            sys.exit(1)
        
        if not checksum_path.exists():
            print(f"[ERROR] Checksum file not created at {checksum_path}", file=sys.stderr)
            sys.exit(1)
        
        # Export governance policy to archive metadata
        governance_metadata_path = Path(f"archives/governance_policy_{version}_{date}.json")
        try:
            from scripts.governance_policies import get_governance_policy
            governance = get_governance_policy()
            governance_policy = governance.export_governance_policy()
            with open(governance_metadata_path, 'w') as f:
                json.dump(governance_policy, f, indent=2)
            print(f"[SUCCESS] Governance policy exported: {governance_metadata_path}")
        except Exception as e:
            print(f"[WARNING] Could not export governance policy: {e}")
        
        # Show success message
        archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
        print(f"[SUCCESS] Archive created: {archive_path} ({archive_size_mb:.2f} MB)")
        print(f"[SUCCESS] Checksum: {checksum_path}")
        print(f"[SUCCESS] Log: {log_file}")
