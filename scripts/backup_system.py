#!/usr/bin/env python3
"""
Automated Backup System for TFT Data Curation Project

Provides automated backup functionality with compression, integrity verification,
and retention policy management.
"""

import os
import sys
import json
import hashlib
import tarfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupSystem:
    """Automated backup system with compression and integrity verification."""
    
    def __init__(self, backup_dir: str = "backups", config: Optional[Dict] = None):
        """
        Initialize backup system.
        
        Args:
            backup_dir: Directory for storing backups
            config: Backup configuration dictionary
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.config = config or {
            "compression": "gzip",
            "compression_level": 6,
            "verify_integrity": True,
            "checksum_algorithm": "sha256",
            "retention_days": 730,  # 2 years
            "backup_metadata": True
        }
        
        logger.info(f"Backup system initialized: {self.backup_dir}")
    
    def calculate_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """
        Calculate checksum for a file.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm (sha256, sha512, md5)
            
        Returns:
            Hexadecimal checksum string
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def create_backup(
        self,
        source_paths: List[str],
        backup_name: Optional[str] = None,
        backup_type: str = "full"
    ) -> Tuple[Path, Dict]:
        """
        Create a backup archive.
        
        Args:
            source_paths: List of paths to backup
            backup_name: Name for backup archive (auto-generated if None)
            backup_type: Type of backup (full, incremental, differential)
            
        Returns:
            Tuple of (backup_path, metadata_dict)
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
        
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        
        logger.info(f"Creating {backup_type} backup: {backup_path.name}")
        logger.info(f"Backing up {len(source_paths)} paths")
        
        # Collect files to backup
        files_to_backup = []
        total_size = 0
        
        for source_path in source_paths:
            path = Path(source_path)
            if not path.exists():
                logger.warning(f"Path does not exist: {source_path}")
                continue
            
            if path.is_file():
                files_to_backup.append(path)
                total_size += path.stat().st_size
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        files_to_backup.append(file_path)
                        total_size += file_path.stat().st_size
        
        if not files_to_backup:
            raise ValueError("No files found to backup")
        
        logger.info(f"Found {len(files_to_backup)} files ({total_size / 1024 / 1024:.2f} MB)")
        
        # Create compressed archive
        compression = self.config.get("compression", "gz")
        # Map compression names to tarfile format
        compression_map = {
            "gzip": "gz",
            "gz": "gz",
            "bz2": "bz2",
            "xz": "xz",
            "none": ""
        }
        tar_compression = compression_map.get(compression, "gz")
        compression_level = self.config.get("compression_level", 6)
        
        # tarfile doesn't support compression_level parameter directly
        # Compression level is handled by the underlying compression library
        with tarfile.open(backup_path, f"w:{tar_compression}" if tar_compression else "w") as tar:
            cwd = Path.cwd()
            for file_path in files_to_backup:
                # Use relative path in archive
                try:
                    # Try relative to current working directory
                    if file_path.is_absolute():
                        arcname = file_path.relative_to(cwd)
                    else:
                        # Already relative, use as-is
                        arcname = file_path
                except ValueError:
                    # If not in subpath, use filename only
                    arcname = file_path.name
                tar.add(file_path, arcname=str(arcname))
                logger.debug(f"Added to archive: {arcname}")
        
        # Calculate checksum
        checksum = None
        if self.config.get("verify_integrity", True):
            checksum = self.calculate_checksum(
                backup_path,
                self.config.get("checksum_algorithm", "sha256")
            )
            logger.info(f"Backup checksum ({self.config.get('checksum_algorithm', 'sha256')}): {checksum}")
        
        # Create metadata
        metadata = {
            "backup_name": backup_name,
            "backup_type": backup_type,
            "backup_path": str(backup_path),
            "backup_date": datetime.now().isoformat(),
            "source_paths": source_paths,
            "file_count": len(files_to_backup),
            "total_size_bytes": total_size,
            "compression": compression if compression != "gzip" else "gz",
            "compression_level": compression_level,
            "checksum": checksum,
            "checksum_algorithm": self.config.get("checksum_algorithm", "sha256"),
            "backup_size_bytes": backup_path.stat().st_size,
            "compression_ratio": total_size / backup_path.stat().st_size if backup_path.stat().st_size > 0 else 0
        }
        
        # Save metadata
        if self.config.get("backup_metadata", True):
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Metadata saved: {metadata_path}")
        
        logger.info(f"[SUCCESS] Backup created: {backup_path.name} ({backup_path.stat().st_size / 1024 / 1024:.2f} MB)")
        logger.info(f"   Compression ratio: {metadata['compression_ratio']:.2f}x")
        
        return backup_path, metadata
    
    def verify_backup(self, backup_path: Path, expected_checksum: Optional[str] = None) -> bool:
        """
        Verify backup integrity.
        
        Args:
            backup_path: Path to backup archive
            expected_checksum: Expected checksum (from metadata)
            
        Returns:
            True if backup is valid
        """
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        logger.info(f"Verifying backup: {backup_path.name}")
        
        # Verify archive can be opened
        try:
            with tarfile.open(backup_path, 'r:*') as tar:
                members = tar.getmembers()
                logger.info(f"Archive contains {len(members)} files")
        except Exception as e:
            logger.error(f"Failed to open archive: {e}")
            return False
        
        # Verify checksum if provided
        if expected_checksum:
            actual_checksum = self.calculate_checksum(
                backup_path,
                self.config.get("checksum_algorithm", "sha256")
            )
            
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
                return False
            else:
                logger.info("[SUCCESS] Checksum verification passed")
        
        logger.info("[SUCCESS] Backup verification successful")
        return True
    
    def restore_backup(
        self,
        backup_path: Path,
        restore_dir: str = "restored",
        verify: bool = True
    ) -> Path:
        """
        Restore a backup archive.
        
        Args:
            backup_path: Path to backup archive
            restore_dir: Directory to restore to
            verify: Verify backup before restoring
            
        Returns:
            Path to restored directory
        """
        if verify:
            metadata_path = backup_path.parent / f"{backup_path.stem.replace('.tar', '')}_metadata.json"
            expected_checksum = None
            
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    expected_checksum = metadata.get("checksum")
            
            if not self.verify_backup(backup_path, expected_checksum):
                raise ValueError("Backup verification failed")
        
        restore_path = Path(restore_dir)
        restore_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Restoring backup to: {restore_path}")
        
        with tarfile.open(backup_path, 'r:*') as tar:
            tar.extractall(restore_path)
        
        logger.info(f"[SUCCESS] Backup restored to: {restore_path}")
        return restore_path
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[Dict]:
        """
        List all backups.
        
        Args:
            backup_type: Filter by backup type (full, incremental, differential)
            
        Returns:
            List of backup metadata dictionaries
        """
        backups = []
        
        for metadata_file in self.backup_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                    if backup_type is None or metadata.get("backup_type") == backup_type:
                        # Check if backup file still exists
                        backup_path = Path(metadata.get("backup_path", ""))
                        if backup_path.exists():
                            metadata["exists"] = True
                            metadata["backup_size_mb"] = backup_path.stat().st_size / 1024 / 1024
                        else:
                            metadata["exists"] = False
                        
                        backups.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to read metadata {metadata_file}: {e}")
        
        # Sort by backup date
        backups.sort(key=lambda x: x.get("backup_date", ""), reverse=True)
        
        return backups
    
    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> int:
        """
        Remove backups older than retention period.
        
        Args:
            retention_days: Retention period in days (uses config if None)
            
        Returns:
            Number of backups removed
        """
        if retention_days is None:
            retention_days = self.config.get("retention_days", 730)
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        logger.info(f"Cleaning up backups older than {retention_days} days (before {cutoff_date.date()})")
        
        removed_count = 0
        
        for backup_metadata in self.list_backups():
            backup_date = datetime.fromisoformat(backup_metadata["backup_date"])
            
            if backup_date < cutoff_date:
                backup_path = Path(backup_metadata["backup_path"])
                metadata_path = backup_path.parent / f"{backup_path.stem.replace('.tar', '')}_metadata.json"
                
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info(f"Removed old backup: {backup_path.name}")
                    removed_count += 1
                
                if metadata_path.exists():
                    metadata_path.unlink()
        
        logger.info(f"[SUCCESS] Cleaned up {removed_count} old backups")
        return removed_count


def main():
    """Command-line interface for backup system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TFT Data Backup System")
    parser.add_argument("--backup-dir", default="backups", help="Backup directory")
    parser.add_argument("--source", nargs="+", required=False, help="Source paths to backup")
    parser.add_argument("--type", choices=["full", "incremental", "differential"], default="full", help="Backup type")
    parser.add_argument("--name", help="Backup name (auto-generated if not provided)")
    parser.add_argument("--verify", action="store_true", help="Verify backup after creation")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--cleanup", type=int, help="Clean up backups older than N days")
    parser.add_argument("--restore", help="Restore backup from archive path")
    parser.add_argument("--restore-dir", default="restored", help="Directory to restore to")
    
    args = parser.parse_args()
    
    backup_system = BackupSystem(backup_dir=args.backup_dir)
    
    if args.list:
        backups = backup_system.list_backups()
        print(f"\nFound {len(backups)} backups:\n")
        for backup in backups:
            print(f"  {backup['backup_name']}")
            print(f"    Type: {backup['backup_type']}")
            print(f"    Date: {backup['backup_date']}")
            print(f"    Size: {backup.get('backup_size_mb', 0):.2f} MB")
            print(f"    Files: {backup['file_count']}")
            print(f"    Exists: {backup.get('exists', False)}")
            print()
    elif args.cleanup:
        removed = backup_system.cleanup_old_backups(args.cleanup)
        print(f"Removed {removed} old backups")
    elif args.restore:
        restore_path = backup_system.restore_backup(
            Path(args.restore),
            restore_dir=args.restore_dir,
            verify=True
        )
        print(f"Backup restored to: {restore_path}")
    elif args.source:
        backup_path, metadata = backup_system.create_backup(
            source_paths=args.source,
            backup_name=args.name,
            backup_type=args.type
        )
        
        if args.verify:
            if backup_system.verify_backup(backup_path, metadata["checksum"]):
                print(f"[SUCCESS] Backup created and verified: {backup_path}")
            else:
                print(f"[ERROR] Backup created but verification failed: {backup_path}")
                sys.exit(1)
        else:
            print(f"[SUCCESS] Backup created: {backup_path}")


if __name__ == "__main__":
    main()

