#!/usr/bin/env python3
"""
Archive Manager for TFT Data Curation Project

Creates self-contained, long-term accessible "Release Packages" by bundling:
1. Data files (JSON/Parquet)
2. Documentation (Data Dictionary, README, Final Report)
3. Metadata (Manifest, Checksums)
4. Context (Archive README)
"""

import os
import json
import shutil
import tarfile
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArchiveManager:
    """
    Manages the creation of long-term preservation archives.
    """
    
    def __init__(self, base_dir: str = ".", archive_dir: str = "archives"):
        """
        Initialize ArchiveManager.
        
        Args:
            base_dir: Project root directory
            archive_dir: Directory to store generated archives
        """
        self.base_dir = Path(base_dir).resolve()
        self.archive_dir = self.base_dir / archive_dir
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Critical documentation to include in every archive
        self.required_docs = [
            "Documents/DATA_DICTIONARY.md",
            "Documents/reports/final_report.md",
            "README.md",
            "LICENSE"
        ]
        
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_archive_readme(self, version: str, description: str, manifest: Dict) -> str:
        """Generate a human-readable README for the archive."""
        return f"""TFT Match Data Collection - Archive Package
=============================================

Version: {version}
Date: {datetime.now().strftime('%Y-%m-%d')}
Description: {description}

Contents
--------
1. /data          - Raw and processed data files
2. /documentation - Critical project documentation
3. /metadata      - Provenance and manifest files

Citation
--------
If you use this dataset, please cite:
Ugarte, J. (2025). TFT Match Data Collection [Data set]. GitHub.

Manifest Summary
----------------
Total Files: {manifest['total_files']}
Total Size: {manifest['total_size_mb']:.2f} MB
SHA-256 Checksum: See manifest.json

Documentation
-------------
- DATA_DICTIONARY.md: Detailed field descriptions
- final_report.md: Project methodology and results
- README.md: General project overview

License
-------
See LICENSE file.
"""

    def create_release_package(self, 
                             data_paths: List[str], 
                             version: str, 
                             description: str,
                             output_name: Optional[str] = None) -> Path:
        """
        Create a self-contained release package.
        
        Args:
            data_paths: List of data files/directories to include
            version: Version string (e.g., "1.0.0")
            description: Brief description of the archive content
            output_name: Optional custom name for the archive file
            
        Returns:
            Path to the created archive
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        if not output_name:
            output_name = f"tft_data_archive_v{version}_{timestamp}.tar.gz"
            
        archive_path = self.archive_dir / output_name
        staging_dir = self.archive_dir / f"staging_{timestamp}"
        
        try:
            # 1. Prepare Staging Directory
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            staging_dir.mkdir()
            
            (staging_dir / "data").mkdir()
            (staging_dir / "documentation").mkdir()
            (staging_dir / "metadata").mkdir()
            
            manifest = {
                "version": version,
                "creation_date": datetime.now().isoformat(),
                "description": description,
                "files": [],
                "total_size_bytes": 0
            }
            
            # 2. Copy Data Files
            logger.info("Copying data files...")
            for path_str in data_paths:
                src_path = self.base_dir / path_str
                if not src_path.exists():
                    logger.warning(f"Data path not found: {src_path}")
                    continue
                
                if src_path.is_file():
                    dst_path = staging_dir / "data" / src_path.name
                    shutil.copy2(src_path, dst_path)
                    self._add_to_manifest(manifest, dst_path, "data")
                elif src_path.is_dir():
                    dst_dir = staging_dir / "data" / src_path.name
                    shutil.copytree(src_path, dst_dir)
                    for f in dst_dir.rglob("*"):
                        if f.is_file():
                            self._add_to_manifest(manifest, f, "data")

            # 3. Copy Documentation
            logger.info("Copying documentation...")
            for doc_rel_path in self.required_docs:
                src_path = self.base_dir / doc_rel_path
                if src_path.exists():
                    dst_path = staging_dir / "documentation" / src_path.name
                    shutil.copy2(src_path, dst_path)
                    self._add_to_manifest(manifest, dst_path, "documentation")
                else:
                    logger.warning(f"Documentation missing: {src_path}")

            # 4. Generate Archive README
            logger.info("Generating Archive README...")
            manifest['total_files'] = len(manifest['files'])
            manifest['total_size_mb'] = manifest['total_size_bytes'] / (1024 * 1024)
            
            readme_content = self.create_archive_readme(version, description, manifest)
            readme_path = staging_dir / "ARCHIVE_README.txt"
            with open(readme_path, "w") as f:
                f.write(readme_content)
            self._add_to_manifest(manifest, readme_path, "root")

            # 5. Save Manifest
            manifest_path = staging_dir / "metadata" / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            
            # 5b. Export Governance Policy
            logger.info("Exporting governance policy...")
            try:
                import sys
                sys.path.insert(0, str(self.base_dir))
                from scripts.governance_policies import get_governance_policy
                
                governance = get_governance_policy()
                governance_policy = governance.export_governance_policy()
                
                governance_path = staging_dir / "metadata" / "governance_policy.json"
                with open(governance_path, "w") as f:
                    json.dump(governance_policy, f, indent=2)
                self._add_to_manifest(manifest, governance_path, "metadata")
                logger.info("[SUCCESS] Governance policy included in archive")
            except Exception as e:
                logger.warning(f"[WARNING] Could not export governance policy: {e}")
            
            # 6. Compress
            logger.info(f"Compressing archive to {archive_path}...")
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(staging_dir, arcname=f"tft_archive_v{version}")
                
            # 7. Verify
            final_checksum = self.calculate_checksum(archive_path)
            logger.info(f"[SUCCESS] Archive created successfully!")
            logger.info(f"   Path: {archive_path}")
            logger.info(f"   Size: {archive_path.stat().st_size / (1024*1024):.2f} MB")
            logger.info(f"   SHA-256: {final_checksum}")
            
            # Save checksum file next to archive
            checksum_path = Path(str(archive_path) + '.sha256')
            with open(checksum_path, "w") as f:
                f.write(f"{final_checksum}  {archive_path.name}\n")
                
            return archive_path

        finally:
            if staging_dir.exists():
                shutil.rmtree(staging_dir)

    def _add_to_manifest(self, manifest: Dict, file_path: Path, category: str):
        """Add file details to manifest."""
        rel_path = file_path.relative_to(file_path.parents[1] if category != "root" else file_path.parent)
        size = file_path.stat().st_size
        manifest["files"].append({
            "path": str(rel_path),
            "category": category,
            "size_bytes": size,
            "checksum_sha256": self.calculate_checksum(file_path)
        })
        manifest["total_size_bytes"] += size

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create a long-term preservation archive.")
    parser.add_argument("--version", required=True, help="Version of the dataset (e.g., 1.0.0)")
    parser.add_argument("--description", required=True, help="Description of the dataset")
    parser.add_argument("--data", nargs="+", required=True, help="Paths to data files/folders to include")
    parser.add_argument("--output", help="Custom output filename")
    
    args = parser.parse_args()
    
    manager = ArchiveManager()
    manager.create_release_package(
        data_paths=args.data,
        version=args.version,
        description=args.description,
        output_name=args.output
    )

if __name__ == "__main__":
    main()
