# Provenance Schema Specification

## Overview

The provenance tracking system has been enhanced to full **W3C PROV** compliance, providing comprehensive data lineage tracking, integrity verification, and execution metadata.

---

## What Was Enhanced

### 1. W3C PROV Structure

**Before**: Simple JSON structure with basic workflow information
**After**: Full W3C PROV JSON-LD with proper entities, activities, agents, and relationships

**Components Added**:
- **Entities**: All data files (raw, validated, transformed, quality reports, config)
- **Activities**: Each workflow step as a PROV Activity
- **Agents**: Snakemake, workflow system, user, API source
- **Relationships**: `wasGeneratedBy`, `used`, `wasAttributedTo`, `wasAssociatedWith`, `wasInformedBy`

### 2. File Integrity Verification

**SHA-256 Checksums**: All input and output files now have SHA-256 checksums calculated and stored in provenance

**File Metadata Tracked**:
- File path
- File size (bytes)
- Modified timestamp
- SHA-256 checksum

### 3. Agent Tracking

**Agents Documented**:
- **Snakemake**: Workflow engine with version information
- **Workflow System**: TFT Data Curation Workflow with Python version and platform info
- **User**: Executor information (username, hostname)
- **API Source**: Riot Games API as data source

### 4. Activity Tracking

**Activities Documented**:
- `collection` - Data collection from Riot API
- `validation` - Data quality validation
- `transformation` - JSON-LD transformation
- `quality_assessment` - Quality metrics calculation
- `provenance_generation` - Provenance document creation
- `workflow_execution` - Complete workflow execution

Each activity includes:
- Start time
- Workflow step name
- Collection date (where applicable)

### 5. Enhanced Metadata

**Execution Metadata**:
- Workflow version
- Collection date
- Execution timestamp
- Snakemake version
- Python version
- Platform information
- User and hostname
- Workflow steps list

**Quality Metrics Integration**:
- Quality report data embedded in provenance
- Quality scores and metrics included

**Configuration Tracking**:
- Configuration file checksum
- Configuration content (if available)

### 6. PROV Relationships

**Relationship Types**:
- **wasGeneratedBy**: Links entities to activities that created them
- **used**: Links activities to entities they consumed
- **wasAttributedTo**: Links entities to agents responsible for them
- **wasAssociatedWith**: Links activities to agents that executed them
- **wasInformedBy**: Links activities that depend on other activities

---

## Provenance Document Structure

### W3C PROV JSON-LD Format

```json
{
  "@context": {
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
    "tft": "http://tft-data-extraction.com/schema#"
  },
  "@type": "prov:Bundle",
  "entity": [...],      // All data files
  "activity": [...],     // All workflow steps
  "agent": [...],       // All agents (software, users, organizations)
  "wasGeneratedBy": [...],  // Entity generation relationships
  "used": [...],        // Activity input relationships
  "wasAttributedTo": [...], // Entity attribution
  "wasAssociatedWith": [...], // Activity-agent associations
  "wasInformedBy": [...],    // Activity dependencies
  "metadata": {...}     // Execution metadata
}
```

---

## Features

### Complete W3C PROV Compliance
- Proper PROV namespace and context
- All PROV core classes (Entity, Activity, Agent)
- All PROV relationships
- JSON-LD format for semantic web compatibility

### File Integrity
- SHA-256 checksums for all files
- File size and modification time tracking
- Enables data integrity verification

### Complete Data Lineage
- Full workflow execution tracking
- Input/output relationships
- Activity dependencies
- Agent attribution

### Execution Context
- Software versions (Snakemake, Python)
- Platform information
- User and system information
- Configuration parameters

### Quality Metrics Integration
- Quality report data embedded
- Quality scores included in provenance
- Validation results tracked

---

## Usage

### Automatic Generation

Provenance is automatically generated when running the workflow:

```bash
snakemake --config collection_date=20251115
```

The provenance document will be created at:
```
provenance/workflow_20251115.prov.json
```

### Viewing Provenance

```bash
# View provenance document
cat provenance/workflow_20251115.prov.json | jq .

# Extract specific information
cat provenance/workflow_20251115.prov.json | jq '.entity[] | select(.prov:label == "Raw TFT Collection Data")'
cat provenance/workflow_20251115.prov.json | jq '.metadata'
```

### Verifying File Integrity

```bash
# Extract checksum from provenance
cat provenance/workflow_20251115.prov.json | jq '.entity[] | select(.prov:label == "Raw TFT Collection Data") | .tft:sha256'

# Verify file checksum
sha256sum data/raw/tft_collection_20251115.json
```

---

## Example Provenance Document

```json
{
  "@context": {
    "prov": "http://www.w3.org/ns/prov#",
    "tft": "http://tft-data-extraction.com/schema#"
  },
  "@type": "prov:Bundle",
  "entity": [
    {
      "@id": "http://tft-data-extraction.com/workflow/20251115/entity/raw_data",
      "@type": "prov:Entity",
      "prov:label": "Raw TFT Collection Data",
      "tft:sha256": "abc123...",
      "tft:file_size": 4500000,
      "tft:modified_time": "2025-11-15T22:58:17Z"
    }
  ],
  "activity": [
    {
      "@id": "http://tft-data-extraction.com/workflow/20251115/activity/collection",
      "@type": "prov:Activity",
      "prov:label": "Data Collection",
      "prov:startedAtTime": "2025-11-15T22:58:17Z"
    }
  ],
  "agent": [
    {
      "@id": "http://tft-data-extraction.com/workflow/20251115/agent/snakemake",
      "@type": "prov:SoftwareAgent",
      "prov:label": "Snakemake",
      "tft:version": "7.32.0"
    }
  ],
  "wasGeneratedBy": [
    {
      "prov:entity": "http://tft-data-extraction.com/workflow/20251115/entity/raw_data",
      "prov:activity": "http://tft-data-extraction.com/workflow/20251115/activity/collection",
      "prov:time": "2025-11-15T22:58:17Z"
    }
  ]
}
```

---

## Benefits

### 1. Reproducibility
- Complete execution context captured
- All inputs and outputs tracked with checksums
- Configuration parameters documented

### 2. Data Integrity
- SHA-256 checksums enable verification
- File metadata for audit trails
- Quality metrics embedded

### 3. Compliance
- W3C PROV standard compliance
- Semantic web compatible (JSON-LD)
- Interoperable with PROV tools

### 4. Traceability
- Complete data lineage
- Activity dependencies
- Agent attribution

### 5. Auditability
- Execution metadata
- User and system information
- Timestamps for all operations

---

## Integration Points

### With Identifier System
- Provenance can reference dataset identifiers
- SHA-256 checksums align with canonical hashing
- Supports identifier resolution

### With Backup System
- Provenance included in backups
- Checksums enable backup verification
- Metadata supports recovery procedures

### With Quality Assurance
- Quality metrics embedded in provenance
- Validation results tracked
- Quality scores included

---

## Technical Details

### Dependencies
- Python 3.8+
- Standard library: `json`, `hashlib`, `pathlib`, `datetime`, `platform`, `getpass`, `subprocess`
- Optional: `yaml` (PyYAML) for config parsing (with fallback)

### Performance
- Checksum calculation: ~1-2 seconds per file (depends on size)
- Provenance generation: <5 seconds total
- Minimal overhead on workflow execution

### File Format
- **Format**: JSON-LD (W3C PROV)
- **Encoding**: UTF-8
- **Size**: ~5-10 KB per provenance document

---

## Validation

### W3C PROV Compliance
The provenance documents follow W3C PROV-DM (Data Model) specification:
- Proper namespace usage
- Correct PROV classes
- Valid relationships
- JSON-LD structure

### Tools for Validation
- **PROV Validator**: https://provenance.ecs.soton.ac.uk/validator/
- **JSON-LD Playground**: https://json-ld.org/playground/
- **PROV Toolbox**: https://provenance.ecs.soton.ac.uk/toolbox/

---

## Future Enhancements

### Potential Additions
1. **Temporal Tracking**: More granular timestamps for each activity
2. **Error Tracking**: Capture errors and warnings in provenance
3. **Resource Usage**: Track CPU, memory, network usage
4. **External Dependencies**: Track external API calls and dependencies
5. **Version Control**: Link to Git commits and versions

---

## References

- **W3C PROV Specification**: https://www.w3.org/TR/prov-dm/
- **W3C PROV-O (Ontology)**: https://www.w3.org/TR/prov-o/
- **JSON-LD Specification**: https://www.w3.org/TR/json-ld/
- **Project Identifier System**: `Documents/riot_tft_identifier_system.md`

