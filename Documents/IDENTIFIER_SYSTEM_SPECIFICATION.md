# Riot TFT Data Identifier System Specification

## 1. Overview

This document defines the identifier system used for extracting, storing, and referencing **Riot Teamfight Tactics (TFT)** game data. It integrates best practices from digital preservation (Lynch, 1999), identifier theory (Kunze, 2002), and Earth Science identifier systems (Duerr et al., 2011).

The goal is to ensure:
- **Uniqueness** across matches, players, datasets, and derived objects.
- **Persistence** and **referential integrity** over time.
- **Scientific equivalence verification** through canonicalization and hashing.

### Core Concepts

An **identifier** is a name or label that uniquely distinguishes an entity within a specific context. An **identifier system** is a framework for creating, managing, resolving, and maintaining identifiers, defined by:
- **Syntax**: The structure of the identifier.
- **Infrastructure**: Mechanisms for creation, management, and resolution.
- **Governance**: Social organization ensuring persistence and trust.

**Persistence** refers to the long-term reliability of identifiers, not necessarily of the object itself. As Kunze (2002) notes: *"Persistence is a service quality, not a technical guarantee."*

---

## 2. Identifier Principles

| Concept | Description |
|----------|--------------|
| **Uniqueness** | Each identifier must be unique within its namespace. |
| **Persistence** | Identifiers must remain valid even if data moves or formats change. |
| **Opacity** | Identifiers do not encode semantics unless necessary. |
| **Resolution** | Identifiers should be resolvable to their corresponding entity or metadata. |
| **Canonicalization** | Equivalent data representations should map to the same canonical form and identifier. |

### Key Characteristics

Identifiers can be classified by their properties:

| Type | Description | Examples |
|------|-------------|----------|
| **Coordinated** | Managed by a central authority to ensure global uniqueness | DOI, Handle |
| **Decentralized** | Locally generated without central authority | UUID |
| **Natural** | Derived from intrinsic properties of an entity | Content-based hash |
| **Synthetic** | Algorithmically generated values | UUID, sequential IDs |
| **Opaque** | Contains no semantically meaningful information | UUID |
| **Transparent** | Encodes descriptive information within the identifier string | Namespaced labels |

---

## 3. Identifier Schemes Overview

This system employs multiple identifier schemes, each selected for specific use cases based on their characteristics:

| Scheme | Example | Key Features | Strengths | Limitations |
|--------|---------|--------------|-----------|-------------|
| **UUID** | `35d6c06a-4f51-11ef...` | 128-bit identifier (RFC 9562) | Globally unique, decentralized | Not time-ordered (v4), possible privacy concerns (v1) |
| **URN** | `urn:isbn:0451450523` | Persistent name in a namespace | Structured persistence | Not directly resolvable |
| **DOI** | `10.5334/dsj-2017-039` | Managed by registrars (Crossref) | Widely adopted, resolvable | Requires fees and central administration |
| **Handle** | `hdl:4263537/5555` | Foundation for DOIs | Flexible resolution | Requires server maintenance |
| **Content-based** | `sha256:...` | Derived from content hash | Verifiable integrity | ID changes with content modification |

### Use Cases (Duerr et al., 2011)

1. **Unique Identifier**: Unambiguously identify an object regardless of location (e.g., UUID).
2. **Unique Locator**: Locate the authoritative version of data (e.g., DOI, Handle).
3. **Citable Locator**: Enable persistent citation in scholarly works (e.g., DOI).
4. **Scientifically Unique Identifier**: Distinguish strictly identical scientific content, accounting for format changes via canonicalization.

---

## 4. Object Types and Identifier Schemes

The following table defines the identifier schemes used for each object type in the TFT data system:

| Object | Identifier System | Example | Purpose |
|--------|--------------------|----------|----------|
| **Match** | UUIDv7 (RFC 9562) | `urn:uuid:01890a2e-79f2-7c5b-b0b0-3d9c31a2b14f` | Unique match instance |
| **Player** | Riot PUUID | `puuid:K4s9VAbcD3...` | Stable player identity (Riot-managed) |
| **Game Version** | Riot semantic version | `tft:13.24` | Patch reference |
| **Item / Trait / Unit** | Namespaced label | `tft:13.24:item:InfinityEdge` | Stable reference across versions |
| **Dataset Snapshot** | SHA-256 Hash | `sha256:9df1e8d7b3...` | Verifies scientific equivalence |
| **Published Dataset** | DOI (DataCite / Zenodo) | `doi:10.1234/tft-data-2025-v1` | Persistent, citable locator |

### Rationale for Scheme Selection

- **UUIDv7 for Matches**: Provides time-ordered, globally unique identifiers suitable for high-volume match data.
- **Riot PUUID for Players**: Aligns with Riot API conventions and leverages their stable player identity system.
- **SHA-256 for Datasets**: Enables scientific equivalence verification through content-based identification.
- **DOI for Published Datasets**: Ensures persistent, citable references suitable for academic publication.

---

## 5. Canonicalization for Data Integrity

Canonicalization ensures that different serializations of the same data produce the same identifier. This is foundational for **scientific equivalence verification** (Lynch, 1999).

### Theoretical Foundation

Clifford Lynch introduced canonicalization for digital preservation. Key principles:

- **Canonical Form**: Defines the essential characteristics of a digital object.
- **Verification**: By applying a canonicalization function `C(D)`, hashes can verify integrity across format migrations: `HASH(C(D)) == HASH(C(R(D)))`.
- **Identity**: Helps define what constitutes "scientific identity" (invariant properties).

### Canonical Hash Function (Python Example)

```python
import json, hashlib

def canonical_hash(obj):
    canon = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()
```

This function guarantees that logically identical JSON data will generate the same SHA-256 hash, regardless of:
- Key ordering
- Whitespace differences
- Formatting variations

### Benefits

- Enables **scientific equivalence checks** between dataset versions.
- Preserves **referential integrity** during format migrations.
- Facilitates **authenticity verification** (HASH(C(D)) == HASH(C(R(D)))).
- Supports **provenance tracking** and integrity verification.

### Applications

- Provenance tracking and integrity verification.
- Format-invariant dataset comparison.
- Authenticity verification across data transformations.

---

## 6. Identifier Structure

Each identifier follows a consistent, parseable structure.

### Example Schema (JSON)

```json
{
  "match_id": "urn:uuid:01890a2e-79f2-7c5b-b0b0-3d9c31a2b14f",
  "player_id": "puuid:K4s9VAbcD3...",
  "dataset_id": "sha256:9df1e8d7b3...",
  "published_id": "doi:10.1234/tft-data-2025-v1",
  "version": "tft:13.24"
}
```

---

## 7. Recommendations

| Area | Recommendation |
|------|----------------|
| **Match IDs** | Generate using **UUIDv7** for sortability and collision resistance. |
| **Player IDs** | Use Riot's **PUUID**, maintaining alignment with Riot API conventions. |
| **Dataset Hashing** | Use canonical JSON + **SHA-256** to ensure reproducibility. |
| **Data Publication** | Assign **DOIs** via Zenodo or Figshare for public datasets. |
| **Metadata Integrity** | Include canonicalization rules and hash algorithms in provenance metadata. |
| **Governance** | Maintain a local **Handle/DOI registry** or metadata index for resolution. |
| **Persistence Policy** | Define internal retention guarantees for match and player data. |

### Best Practices

- Use **DOIs or Handles** for public, citable datasets.
- Use **UUIDs** for internal tracking or decentralized generation.
- Implement **canonicalization + hashing** to verify equivalence across formats.
- Maintain **tombstone pages** for deleted or migrated resources.
- Establish **governance structures** for longer-term persistence.

### Challenges and Mitigations

| Challenge | Mitigation Strategy |
|-----------|---------------------|
| **Link Rot** | Use persistent identifiers (DOI, Handle) rather than URLs for long-term references. |
| **Authority Dependence** | Maintain local registry/index for resolution even if external services change. |
| **Scalability** | Use decentralized schemes (UUID) for high-volume internal data; reserve DOI for published datasets. |
| **Equivalence** | Implement canonicalization to handle reformatted-but-identical data. |
| **Metadata Binding** | Include identifier schemes and canonicalization rules in provenance metadata. |

---

## 8. Example Identifier Hierarchy

```
match:urn:uuid:01890a2e-79f2-7c5b-b0b0-3d9c31a2b14f
player:puuid:K4s9VAbcD3...
dataset:sha256:9df1e8d7b3...
published:doi:10.1234/tft-data-2025-v1
```

---

## 9. System Elements

An identifier system requires three key elements:

1. **Scheme**: Syntax and rules (e.g., `10.<prefix>/<suffix>` for DOI).
2. **Resolution**: Infrastructure to interpret identifiers (e.g., Handle servers, local registries).
3. **Governance**: Institutional stewardship ensuring long-term maintenance.

---

## 10. Evaluation Criteria

| Criteria | Optimal Examples | Use Case |
|----------|------------------|----------|
| **Global Uniqueness** | UUID, DOI | Robust ID generation |
| **Resolvability** | DOI, Handle, ARK | Citation and access |
| **Decentralization** | UUID | System-edge generation |
| **Metadata Integration** | DOI, ORCID | Discovery and credit |
| **Format Invariance** | Canonicalization | Scientific equivalence verification |

---

## 11. References

- Lynch, C. (1999). *Canonicalization: A Fundamental Tool to Facilitate Preservation and Management of Digital Information.* D-Lib Magazine, 5(9).
- Duerr, R. E., et al. (2011). *On the Utility of Identification Schemes for Digital Earth Science Data.* Earth Science Informatics, 4:139–160.
- Kunze, J. (2002). *A Metadata Kernel for Electronic Permanence.* Journal of Digital Information, 2(2).
- Gil, Y. (2017). *Identifiers and Identifier Systems.* CS598-FDC Lecture / Geoscience Paper of the Future.
