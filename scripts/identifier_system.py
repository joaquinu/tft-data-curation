#!/usr/bin/env python3
"""
TFT Identifier System Implementation
===================================

This module implements the complete identifier system

Features:
- Canonical hash function for scientific equivalence
- UUIDv7 generation for sortable, collision-resistant IDs
- Dataset snapshot hashing
- Identifier resolution and validation
- Provenance metadata integration
"""

import json
import hashlib
import uuid
import os
try:
    import duckdb
except ImportError:
    raise ImportError("DuckDB is required. Install it with: pip install duckdb")
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class IdentifierType(Enum):
    """Types of identifiers supported by the system"""
    MATCH = "match"
    PLAYER = "player"
    DATASET = "dataset"
    PUBLISHED = "published"
    GAME_VERSION = "game_version"
    ITEM = "item"
    TRAIT = "trait"
    UNIT = "unit"

@dataclass
class IdentifierMetadata:
    """Metadata associated with an identifier"""
    identifier: str
    type: IdentifierType
    created_at: datetime
    canonical_hash: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None
    resolution_url: Optional[str] = None
    status: str = "active"  # active, migrated, deleted
    version: Optional[str] = None
    landing_page_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['type'] = self.type.value
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IdentifierMetadata':
        """Create from dictionary"""
        data['type'] = IdentifierType(data['type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

class PersistentRegistry:
    """Persistent storage for identifier registry using DuckDB"""
    
    def __init__(self, db_path: str = "identifier_registry.duckdb"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _get_connection(self):
        """Get or create DuckDB connection"""
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
        return self.conn
    
    def _init_database(self):
        """Initialize DuckDB database with proper schema"""
        conn = self._get_connection()
        
        # Create identifiers table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS identifiers (
                identifier VARCHAR PRIMARY KEY,
                type VARCHAR NOT NULL,
                created_at VARCHAR NOT NULL,
                canonical_hash VARCHAR,
                provenance JSON,
                resolution_url VARCHAR,
                status VARCHAR DEFAULT 'active',
                version VARCHAR,
                landing_page_url VARCHAR,
                updated_at VARCHAR DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create registry metadata table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registry_metadata (
                key VARCHAR PRIMARY KEY,
                value VARCHAR NOT NULL,
                updated_at VARCHAR DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON identifiers(type)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON identifiers(status)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON identifiers(created_at)
        """)
        
        conn.commit()
    
    def store_identifier(self, metadata: IdentifierMetadata):
        """Store identifier metadata in database"""
        conn = self._get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO identifiers 
            (identifier, type, created_at, canonical_hash, provenance, 
             resolution_url, status, version, landing_page_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.identifier, metadata.type.value, metadata.created_at.isoformat(),
            metadata.canonical_hash, json.dumps(metadata.provenance) if metadata.provenance else None,
            metadata.resolution_url, metadata.status, metadata.version, metadata.landing_page_url,
            datetime.now().isoformat()
        ))
        conn.commit()
    
    def get_identifier(self, identifier: str) -> Optional[IdentifierMetadata]:
        """Retrieve identifier metadata from database"""
        conn = self._get_connection()
        result = conn.execute("""
            SELECT identifier, type, created_at, canonical_hash, provenance,
                   resolution_url, status, version, landing_page_url
            FROM identifiers WHERE identifier = ?
        """, (identifier,)).fetchall()
        
        if result:
            row = result[0]
            return IdentifierMetadata(
                identifier=row[0], type=IdentifierType(row[1]), created_at=datetime.fromisoformat(row[2]),
                canonical_hash=row[3], provenance=json.loads(row[4]) if row[4] else None,
                resolution_url=row[5], status=row[6], version=row[7], landing_page_url=row[8]
            )
        return None
    
    def list_identifiers(self, limit: int = None) -> List[IdentifierMetadata]:
        """List all identifiers from database"""
        conn = self._get_connection()
        query = "SELECT identifier, type, created_at, canonical_hash, provenance, resolution_url, status, version, landing_page_url FROM identifiers ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        results = conn.execute(query).fetchall()
        
        identifiers = []
        for row in results:
            identifiers.append(IdentifierMetadata(
                identifier=row[0], type=IdentifierType(row[1]), created_at=datetime.fromisoformat(row[2]),
                canonical_hash=row[3], provenance=json.loads(row[4]) if row[4] else None,
                resolution_url=row[5], status=row[6], version=row[7], landing_page_url=row[8]
            ))
        return identifiers
    
    def update_status(self, identifier: str, status: str, landing_page_url: Optional[str] = None):
        """Update identifier status"""
        conn = self._get_connection()
        conn.execute("""
            UPDATE identifiers 
            SET status = ?, landing_page_url = ?, updated_at = ?
            WHERE identifier = ?
        """, (status, landing_page_url, datetime.now().isoformat(), identifier))
        conn.commit()
    
    def export_registry(self) -> Dict[str, Any]:
        """Export complete registry"""
        identifiers = self.list_identifiers()
        return {
            "registry_version": "2.0",
            "exported_at": datetime.now().isoformat(),
            "total_identifiers": len(identifiers),
            "database_path": self.db_path,
            "database_type": "DuckDB",
            "identifiers": {metadata.identifier: metadata.to_dict() for metadata in identifiers}
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()

class TFTIdentifierSystem:
    """
    TFT identifier system

    """
    
    def __init__(self, base_namespace: str = "http://tft-data-extraction.com/", 
                 registry_path: str = "identifier_registry.duckdb"):
        self.base_namespace = base_namespace
        self.registry = PersistentRegistry(registry_path)
        self.identifier_registry: Dict[str, IdentifierMetadata] = {}
        self._load_registry_cache()
    
    def _load_registry_cache(self):
        """Load registry data into memory cache for fast access"""
        try:
            identifiers = self.registry.list_identifiers()
            for metadata in identifiers:
                self.identifier_registry[metadata.identifier] = metadata
            logger.info(f"Loaded {len(identifiers)} identifiers into cache")
        except Exception as e:
            logger.warning(f"Failed to load registry cache: {e}")
    
    def _store_identifier(self, metadata: IdentifierMetadata):
        """Store identifier in both persistent registry and cache"""
        self.registry.store_identifier(metadata)
        self.identifier_registry[metadata.identifier] = metadata
        logger.debug(f"Stored identifier: {metadata.identifier}")
        
    def canonical_hash(self, obj: Any) -> str:
        """
        Canonical hash function for data integrity verification
        
        Implements Lynch (1999) canonicalization principles:
        - Ensures different serializations of same data produce same hash
        - Enables scientific equivalence verification
        - Preserves referential integrity during format migrations
        
        Args:
            obj: Data object to canonicalize and hash
            
        Returns:
            SHA-256 hash of canonical representation
        """
        try:
            canon = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            return hashlib.sha256(canon.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Canonical hash generation failed: {e}")
            raise
    
    def generate_uuidv7(self) -> str:
        """
        Generate UUIDv7 for sortable, collision-resistant identifiers
        
        UUIDv7 (RFC 9562) provides:
        - Time-based ordering
        - Collision resistance
        - No central authority required
        
        Note: Falls back to UUID4 if UUIDv7 is not available
        
        Returns:
            UUID string in URN format
        """
        try:
            uuid_obj = uuid.uuid7()
        except AttributeError:
            uuid_obj = uuid.uuid4()
            
        return f"urn:uuid:{uuid_obj}"
    
    def create_match_identifier(self, riot_match_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create persistent match identifier
        """
        internal_uuid = self.generate_uuidv7()
        
        identifier_metadata = IdentifierMetadata(
            identifier=internal_uuid,
            type=IdentifierType.MATCH,
            created_at=datetime.now(),
            provenance={
                "riot_match_id": riot_match_id,
                "original_source": "riot_api",
                "canonicalization_method": "uuidv7",
                "metadata": metadata or {}
            }
        )
        
        # Store identifier persistently
        self._store_identifier(identifier_metadata)
        
        logger.debug(f"Created match identifier: {internal_uuid} for Riot match: {riot_match_id}")
        return internal_uuid
    
    def create_player_identifier(self, puuid: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create player identifier using Riot PUUID
        """
        player_id = f"puuid:{puuid}"
        
        identifier_metadata = IdentifierMetadata(
            identifier=player_id,
            type=IdentifierType.PLAYER,
            created_at=datetime.now(),
            provenance={
                "puuid": puuid,
                "source": "riot_api",
                "global_uniqueness": True,
                "metadata": metadata or {}
            }
        )
        
        self._store_identifier(identifier_metadata)
        return player_id
    
    def create_dataset_identifier(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create content-based dataset identifier using canonical hash
        """
        # Generate canonical hash
        canonical_hash = self.canonical_hash(data)
        dataset_id = f"sha256:{canonical_hash}"
        
        identifier_metadata = IdentifierMetadata(
            identifier=dataset_id,
            type=IdentifierType.DATASET,
            created_at=datetime.now(),
            canonical_hash=canonical_hash,
            provenance={
                "hash_algorithm": "sha256",
                "canonicalization_method": "json_sort_keys",
                "content_based": True,
                "metadata": metadata or {}
            }
        )
        
        self._store_identifier(identifier_metadata)
        logger.debug(f"Created dataset identifier: {dataset_id}")
        return dataset_id
    
    def create_game_version_identifier(self, version: str) -> str:
        """
        Create game version identifier
        """
        version_id = f"tft:{version}"
        
        identifier_metadata = IdentifierMetadata(
            identifier=version_id,
            type=IdentifierType.GAME_VERSION,
            created_at=datetime.now(),
            provenance={
                "version": version,
                "source": "riot_api",
                "semantic_versioning": True
            }
        )
        
        self._store_identifier(identifier_metadata)
        return version_id
    
    def create_item_identifier(self, item_name: str, version: str) -> str:
        """
        Create namespaced item identifier
        """
        item_id = f"tft:{version}:item:{item_name}"
        
        identifier_metadata = IdentifierMetadata(
            identifier=item_id,
            type=IdentifierType.ITEM,
            created_at=datetime.now(),
            provenance={
                "item_name": item_name,
                "version": version,
                "stable_across_versions": True
            }
        )
        
        self._store_identifier(identifier_metadata)
        return item_id
    
    def verify_scientific_equivalence(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> bool:
        """
        Verify scientific equivalence between two datasets
        """
        try:
            hash1 = self.canonical_hash(data1)
            hash2 = self.canonical_hash(data2)
            
            equivalent = hash1 == hash2
            
            logger.debug(f"Scientific equivalence check: {equivalent} (hash1: {hash1[:8]}..., hash2: {hash2[:8]}...)")
            return equivalent
            
        except Exception as e:
            logger.error(f"Scientific equivalence verification failed: {e}")
            return False
    
    def resolve_identifier(self, identifier: str) -> Optional[IdentifierMetadata]:
        """
        Resolve identifier to its metadata
        """
        if identifier in self.identifier_registry:
            return self.identifier_registry[identifier]
        
        metadata = self.registry.get_identifier(identifier)
        if metadata:
            self.identifier_registry[identifier] = metadata
        return metadata
    
    def get_identifier_provenance(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get provenance information for an identifier
        """
        metadata = self.resolve_identifier(identifier)
        return metadata.provenance if metadata else None
    
    def create_collection_identifier(self, collection_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create comprehensive identifier set for a data collection
        """
        identifiers = {}
        
        identifiers['dataset_id'] = self.create_dataset_identifier(collection_data)
        
        timestamp = datetime.now().isoformat()
        identifiers['collection_id'] = f"collection:{timestamp}"
        
        if 'matches' in collection_data:
            match_identifiers = {}
            for match_id, match_data in collection_data['matches'].items():
                persistent_id = self.create_match_identifier(match_id, match_data)
                match_identifiers[match_id] = persistent_id
            identifiers['match_identifiers'] = match_identifiers
        
        if 'players' in collection_data:
            player_identifiers = {}
            for puuid, player_data in collection_data['players'].items():
                player_id = self.create_player_identifier(puuid, player_data)
                player_identifiers[puuid] = player_id
            identifiers['player_identifiers'] = player_identifiers
        
        return identifiers
    
    def add_identifier_metadata(self, data: Dict[str, Any], identifiers: Dict[str, str]) -> Dict[str, Any]:
        """
        Add identifier metadata to data structure
        """
        enhanced_data = data.copy()
        
        enhanced_data['@identifiers'] = identifiers
        enhanced_data['@canonicalization'] = {
            "method": "json_sort_keys",
            "algorithm": "sha256",
            "timestamp": datetime.now().isoformat()
        }
        
        enhanced_data['@provenance'] = {
            "identifier_system": "tft_v1",
            "canonicalization_standard": "lynch_1999",
            "generated_at": datetime.now().isoformat()
        }
        
        return enhanced_data
    
    def export_identifier_registry(self) -> Dict[str, Any]:
        """
        Export the complete identifier registry
        """
        return self.registry.export_registry()
    
    def update_identifier_status(self, identifier: str, status: str, landing_page_url: Optional[str] = None):
        """Update identifier status (active, migrated, deleted) with landing page"""
        self.registry.update_status(identifier, status, landing_page_url)
        if identifier in self.identifier_registry:
            self.identifier_registry[identifier].status = status
            self.identifier_registry[identifier].landing_page_url = landing_page_url
    
    def create_doi_identifier(self, dataset_id: str, metadata: Dict[str, Any]) -> str:
        """Create DOI identifier for published datasets"""
        timestamp = datetime.now().strftime("%Y%m%d")
        doi_suffix = f"tft-data-{timestamp}-{dataset_id[:8]}"
        doi = f"10.1234/{doi_suffix}"
        
        identifier_metadata = IdentifierMetadata(
            identifier=f"doi:{doi}",
            type=IdentifierType.PUBLISHED,
            created_at=datetime.now(),
            provenance={
                "doi": doi,
                "dataset_id": dataset_id,
                "publisher": "TFT Data Extraction Project",
                "publication_date": datetime.now().isoformat(),
                "metadata": metadata
            },
            resolution_url=f"https://doi.org/{doi}",
            status="active"
        )
        
        self._store_identifier(identifier_metadata)
        logger.info(f"Created DOI identifier: {doi}")
        return f"doi:{doi}"
    
    def create_handle_identifier(self, prefix: str, suffix: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create Handle-based persistent identifier"""
        handle = f"hdl:{prefix}/{suffix}"
        
        identifier_metadata = IdentifierMetadata(
            identifier=handle,
            type=IdentifierType.PUBLISHED,
            created_at=datetime.now(),
            provenance={
                "handle": handle,
                "prefix": prefix,
                "suffix": suffix,
                "resolution_service": "hdl.handle.net",
                "metadata": metadata or {}
            },
            resolution_url=f"https://hdl.handle.net/{prefix}/{suffix}",
            status="active"
        )
        
        self._store_identifier(identifier_metadata)
        logger.info(f"Created Handle identifier: {handle}")
        return handle
    
    def create_transparent_identifier(self, entity_type: str, entity_name: str, 
                                   version: Optional[str] = None, 
                                   additional_info: Optional[Dict[str, str]] = None) -> str:
        """Create transparent identifier with semantic information for debugging"""
        parts = [entity_type, entity_name]
        
        if version:
            parts.append(f"v{version}")
        
        if additional_info:
            for key, value in additional_info.items():
                parts.append(f"{key}:{value}")
        
        transparent_id = "tft:" + ":".join(parts)
        
        identifier_metadata = IdentifierMetadata(
            identifier=transparent_id,
            type=IdentifierType.ITEM,  # Default type, could be parameterized
            created_at=datetime.now(),
            provenance={
                "entity_type": entity_type,
                "entity_name": entity_name,
                "version": version,
                "additional_info": additional_info or {},
                "transparent": True,
                "debugging_purpose": True
            },
            status="active"
        )
        
        self._store_identifier(identifier_metadata)
        logger.debug(f"Created transparent identifier: {transparent_id}")
        return transparent_id
    
    def create_versioned_dataset_identifier(self, base_dataset_id: str, version: str, 
                                          changes: Optional[Dict[str, Any]] = None) -> str:
        """Create versioned dataset identifier"""
        versioned_id = f"{base_dataset_id}:v{version}"
        
        identifier_metadata = IdentifierMetadata(
            identifier=versioned_id,
            type=IdentifierType.DATASET,
            created_at=datetime.now(),
            version=version,
            provenance={
                "base_dataset_id": base_dataset_id,
                "version": version,
                "changes": changes or {},
                "versioned": True,
                "parent_identifier": base_dataset_id
            },
            status="active"
        )
        
        self._store_identifier(identifier_metadata)
        logger.info(f"Created versioned dataset identifier: {versioned_id}")
        return versioned_id
    
    def create_landing_page(self, identifier: str, status: str = "active", 
                          redirect_url: Optional[str] = None) -> Dict[str, Any]:
        """Create landing page information for identifier resolution"""
        landing_page = {
            "identifier": identifier,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "resolution_url": f"{self.base_namespace}resolve/{identifier}",
            "redirect_url": redirect_url,
            "metadata": {
                "system": "TFT Identifier System",
                "version": "2.0",
                "governance_policy": "tft_data_retention_v1"
            }
        }
        
        landing_page_url = f"{self.base_namespace}landing/{identifier}"
        self.update_identifier_status(identifier, status, landing_page_url)
        
        return landing_page

def create_canonical_hash(data: Any) -> str:
    """Convenience function for canonical hash generation"""
    system = TFTIdentifierSystem()
    return system.canonical_hash(data)

def verify_data_equivalence(data1: Dict[str, Any], data2: Dict[str, Any]) -> bool:
    """Convenience function for scientific equivalence verification"""
    system = TFTIdentifierSystem()
    return system.verify_scientific_equivalence(data1, data2)

def generate_match_uuid() -> str:
    """Convenience function for UUIDv7 generation"""
    system = TFTIdentifierSystem()
    return system.generate_uuidv7()
