#!/usr/bin/env python3
"""
TFT Identifier System Governance Policies
=========================================

This module implements formal governance structures for the TFT identifier system,
including retention policies, resolution guarantees, and stewardship responsibilities.

Based on the requirements from Documents/identifiers_and_systems_knowledge.md
Section 7: Elements of a Persistent Identifier System
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class DataRetentionPeriod(Enum):
    """Data retention periods for different entity types"""
    PERMANENT = "permanent"
    TEN_YEARS = "10_years"
    FIVE_YEARS = "5_years"
    THREE_YEARS = "3_years"
    ONE_YEAR = "1_year"
    SIX_MONTHS = "6_months"

class IdentifierStatus(Enum):
    """Status of identifiers in the system"""
    ACTIVE = "active"
    MIGRATED = "migrated"
    DEPRECATED = "deprecated"
    DELETED = "deleted"
    ARCHIVED = "archived"

@dataclass
class RetentionPolicy:
    """Retention policy for specific entity types"""
    entity_type: str
    retention_period: DataRetentionPeriod
    description: str
    exceptions: List[str]
    review_frequency: str
    last_reviewed: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "retention_period": self.retention_period.value,
            "description": self.description,
            "exceptions": self.exceptions,
            "review_frequency": self.review_frequency,
            "last_reviewed": self.last_reviewed.isoformat()
        }

@dataclass
class ResolutionGuarantee:
    """Service level guarantees for identifier resolution"""
    metric: str
    target_value: str
    measurement_period: str
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "target_value": self.target_value,
            "measurement_period": self.measurement_period,
            "description": self.description
        }

class TFTIdentifierGovernance:
    """
    Formal governance structure for TFT identifier system
    
    Implements the governance and stewardship requirements from
    Documents/identifiers_and_systems_knowledge.md
    """
    
    def __init__(self):
        self.policies = self._initialize_retention_policies()
        self.guarantees = self._initialize_resolution_guarantees()
        self.policy_version = "1.0"
        self.effective_date = datetime.now()
    
    def _initialize_retention_policies(self) -> Dict[str, RetentionPolicy]:
        """Initialize data retention policies"""
        return {
            "match_data": RetentionPolicy(
                entity_type="match",
                retention_period=DataRetentionPeriod.PERMANENT,
                description="TFT match data retained permanently - no PII involved, valuable for long-term research and analysis",
                exceptions=["Test matches may be purged after 1 year"],
                review_frequency="annual",
                last_reviewed=datetime.now()
            ),
            "player_data": RetentionPolicy(
                entity_type="player",
                retention_period=DataRetentionPeriod.TEN_YEARS,
                description="TFT player data retained for 10 years - no PII involved, contains only game-related statistics and performance data",
                exceptions=["High-performing players may be retained permanently"],
                review_frequency="annual",
                last_reviewed=datetime.now()
            ),
            "dataset_snapshots": RetentionPolicy(
                entity_type="dataset",
                retention_period=DataRetentionPeriod.PERMANENT,
                description="Dataset snapshots retained permanently for scientific reproducibility",
                exceptions=["Temporary datasets may have shorter retention"],
                review_frequency="biannual",
                last_reviewed=datetime.now()
            ),
            "published_datasets": RetentionPolicy(
                entity_type="published",
                retention_period=DataRetentionPeriod.PERMANENT,
                description="Published datasets with DOIs retained permanently",
                exceptions=["Retraction requests may change retention"],
                review_frequency="annual",
                last_reviewed=datetime.now()
            ),
            "identifier_registry": RetentionPolicy(
                entity_type="registry",
                retention_period=DataRetentionPeriod.PERMANENT,
                description="Identifier registry metadata retained permanently",
                exceptions=["Test identifiers may be purged"],
                review_frequency="quarterly",
                last_reviewed=datetime.now()
            )
        }
    
    def _initialize_resolution_guarantees(self) -> List[ResolutionGuarantee]:
        """Initialize service level guarantees"""
        return [
            ResolutionGuarantee(
                metric="Uptime",
                target_value="99.9%",
                measurement_period="monthly",
                description="Identifier resolution service availability"
            ),
            ResolutionGuarantee(
                metric="Response Time",
                target_value="<100ms",
                measurement_period="daily",
                description="Average response time for identifier resolution"
            ),
            ResolutionGuarantee(
                metric="Data Integrity",
                target_value="100%",
                measurement_period="continuous",
                description="Canonical hash verification success rate"
            ),
            ResolutionGuarantee(
                metric="Backup Frequency",
                target_value="Daily",
                measurement_period="daily",
                description="Registry backup completion"
            ),
            ResolutionGuarantee(
                metric="Recovery Time",
                target_value="<4 hours",
                measurement_period="incident-based",
                description="Time to restore service after failure"
            )
        ]
    
    
    def get_retention_policy(self, entity_type: str) -> Optional[RetentionPolicy]:
        """Get retention policy for specific entity type"""
        return self.policies.get(entity_type)
    
    def should_retain_identifier(self, identifier_type: str, created_date: datetime) -> bool:
        """Determine if identifier should be retained based on policy"""
        policy = self.get_retention_policy(identifier_type)
        if not policy:
            return True  # Default to retain if no policy
        
        if policy.retention_period == DataRetentionPeriod.PERMANENT:
            return True
        
        # Calculate retention period
        retention_days = self._get_retention_days(policy.retention_period)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        return created_date > cutoff_date
    
    def _get_retention_days(self, period: DataRetentionPeriod) -> int:
        """Convert retention period to days"""
        period_mapping = {
            DataRetentionPeriod.SIX_MONTHS: 180,
            DataRetentionPeriod.ONE_YEAR: 365,
            DataRetentionPeriod.THREE_YEARS: 1095,
            DataRetentionPeriod.FIVE_YEARS: 1825,
            DataRetentionPeriod.TEN_YEARS: 3650,
            DataRetentionPeriod.PERMANENT: float('inf')
        }
        return period_mapping.get(period, 365)  # Default to 1 year
    
    def get_resolution_guarantees(self) -> List[ResolutionGuarantee]:
        """Get all resolution service guarantees"""
        return self.guarantees
    
    def export_governance_policy(self) -> Dict[str, Any]:
        """Export complete governance policy document"""
        return {
            "governance_version": self.policy_version,
            "effective_date": self.effective_date.isoformat(),
            "last_updated": datetime.now().isoformat(),
            "retention_policies": {
                entity_type: policy.to_dict() 
                for entity_type, policy in self.policies.items()
            },
            "resolution_guarantees": [
                guarantee.to_dict() for guarantee in self.guarantees
            ],
            "compliance_requirements": [
                "All identifiers must have associated retention policy",
                "Resolution service must meet defined guarantees",
                "Policies must be reviewed according to schedule",
                "Backup and recovery procedures must be tested quarterly"
            ]
        }
    
    def validate_compliance(self, identifier_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate identifier compliance with governance policies"""
        entity_type = identifier_metadata.get("type", "unknown")
        created_at = datetime.fromisoformat(identifier_metadata.get("created_at", datetime.now().isoformat()))
        
        policy = self.get_retention_policy(entity_type)
        
        compliance_result = {
            "identifier": identifier_metadata.get("identifier"),
            "entity_type": entity_type,
            "compliance_status": "compliant",
            "retention_policy_applied": policy.to_dict() if policy else None,
            "should_retain": self.should_retain_identifier(entity_type, created_at),
            "issues": [],
            "recommendations": []
        }
        
        # Check retention compliance
        if not self.should_retain_identifier(entity_type, created_at):
            compliance_result["compliance_status"] = "non-compliant"
            compliance_result["issues"].append("Identifier exceeds retention period")
            compliance_result["recommendations"].append("Consider archival or deletion")
        
        # Check if policy exists
        if not policy:
            compliance_result["compliance_status"] = "warning"
            compliance_result["issues"].append("No retention policy defined for entity type")
            compliance_result["recommendations"].append("Define retention policy for this entity type")
        
        return compliance_result

# Convenience functions
def get_governance_policy() -> TFTIdentifierGovernance:
    """Get the current governance policy instance"""
    return TFTIdentifierGovernance()

def check_identifier_compliance(identifier_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Check identifier compliance with governance policies"""
    governance = get_governance_policy()
    return governance.validate_compliance(identifier_metadata)
