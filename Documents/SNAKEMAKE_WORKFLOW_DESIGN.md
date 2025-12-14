# Snakemake Workflow Design

**Project**: TFT Match Data Curation  
**Purpose**: Documentation for the implemented Snakemake workflow

---

## Overview

This guide provides step-by-step instructions for implementing Snakemake in the TFT data curation project, including installation, best practices, workflow design, and integration with existing Python scripts.

---

## 1. Installation and Configuration

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Existing project structure with Python scripts

### Installation

```bash
# Install Snakemake using pip (recommended)
pip install snakemake

# Or install with conda
conda install -c bioconda -c conda-forge snakemake

# Verify installation
snakemake --version
```

### Recommended: Install with Additional Tools

```bash
# Install with common dependencies for data science workflows
pip install snakemake graphviz pyyaml

# For better visualization
pip install snakemake[graphviz]
```

### Configuration Files

Create a `Snakefile` in the project root:

```python
# Snakefile
# TFT Data Curation Workflow

# Configuration
configfile: "config/snakemake_config.yaml"

# Workflow rules
include: "workflow/rules/collect.smk"
include: "workflow/rules/validate.smk"
include: "workflow/rules/transform.smk"
include: "workflow/rules/quality.smk"
```

Create `config/snakemake_config.yaml`:

```yaml
# Snakemake Configuration
# TFT Data Curation Workflow Configuration

# API Configuration
api:
  region: "la2"  # la2 or la1
  rate_limit: 100  # requests per 2 minutes
  
# Collection Configuration
collection:
  mode: "daily"  # daily or weekly
  tiers: ["DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]
  output_dir: "data/daily"
  
# Quality Assurance
quality:
  validation_enabled: true
  anomaly_detection: true
  quality_threshold: 0.8
  
# Provenance
provenance:
  enabled: true
  format: "w3c_prov"
  output_dir: "provenance"
```

---

## 2. Snakemake Best Practices

### 2.1 Workflow Structure

**Recommended Directory Structure:**

```
project_root/
├── Snakefile                    # Main workflow file
├── config/
│   ├── snakemake_config.yaml    # Workflow configuration
│   └── config.yaml              # Existing config
├── workflow/
│   ├── rules/
│   │   ├── collect.smk          # Data collection rules
│   │   ├── validate.smk        # Validation rules
│   │   ├── transform.smk       # Transformation rules
│   │   └── quality.smk          # Quality assurance rules
│   ├── scripts/
│   │   ├── collect_data.py      # Wrapper for collection
│   │   ├── validate_data.py     # Wrapper for validation
│   │   └── transform_data.py   # Wrapper for transformation
│   └── envs/
│       └── data_curation.yaml   # Conda environment (optional)
├── data/
│   ├── raw/                     # Raw collected data
│   ├── validated/               # Validated data
│   ├── transformed/             # Transformed data
│   └── final/                   # Final processed data
└── logs/
    └── snakemake.log            # Snakemake execution log
```

### 2.2 Rule Design Best Practices

**Key Principles:**

1. **One Rule Per Step**: Each rule should represent one logical step
2. **Input/Output Clarity**: Always specify clear input and output files
3. **Parameterization**: Use config files for parameters
4. **Reproducibility**: Include all dependencies and versions
5. **Error Handling**: Use shell commands with proper error handling

**Example Rule Structure:**

```python
# workflow/rules/collect.smk

rule collect_data:
    """
    Collect TFT match data from Riot API.
    
    This rule wraps the automated_collection.py script
    and ensures reproducible data collection.
    """
    input:
        config="config/snakemake_config.yaml"
    output:
        raw_data="data/raw/tft_collection_{date}.json",
        log="logs/collection_{date}.log"
    params:
        region=config["api"]["region"],
        mode=config["collection"]["mode"],
        api_key=lambda wildcards: os.environ.get("RIOT_API_KEY")
    log:
        "logs/snakemake_collect_{date}.log"
    shell:
        """
        python3 scripts/automated_collection.py \
            --mode {params.mode} \
            --region {params.region} \
            --output {output.raw_data} \
            --log {output.log} \
            2>&1 | tee {log}
        """
```

### 2.3 Parameterization Best Practices

**Use Configuration Files:**

```python
# In Snakefile or rule file
configfile: "config/snakemake_config.yaml"

# Access config in rules
rule example:
    params:
        region=config["api"]["region"],
        threshold=config["quality"]["quality_threshold"]
```

**Use Wildcards for Dynamic Parameters:**

```python
rule process_by_date:
    input:
        "data/raw/collection_{date}.json"
    output:
        "data/processed/collection_{date}.json"
    params:
        date="{date}"
    shell:
        "python3 scripts/process.py --date {params.date} {input} {output}"
```

**Use Lambda Functions for Dynamic Values:**

```python
rule collect_data:
    params:
        api_key=lambda wildcards: os.environ.get("RIOT_API_KEY"),
        timestamp=lambda wildcards: datetime.now().isoformat()
```

### 2.4 Provenance Tracking

**Include Provenance in Rules:**

```python
rule collect_with_provenance:
    input:
        config="config/snakemake_config.yaml"
    output:
        data="data/raw/collection_{date}.json",
        provenance="provenance/collection_{date}.prov.json"
    params:
        workflow_version="1.0.0",
        collection_date="{date}"
    shell:
        """
        python3 scripts/collect_with_provenance.py \
            --output {output.data} \
            --provenance {output.provenance} \
            --workflow-version {params.workflow_version} \
            --date {params.collection_date}
        """
```

### 2.5 Error Handling and Logging

**Use Log Files:**

```python
rule collect_data:
    log:
        "logs/collect_{date}.log"
    shell:
        "python3 scripts/collect.py 2>&1 | tee {log}"
```

**Use Retry Logic:**

```python
rule collect_data:
    retries: 3
    shell:
        "python3 scripts/collect.py"
```

**Use Checkpoints for Dynamic Workflows:**

```python
checkpoint collect_data:
    output:
        "data/raw/collection_{date}.json"
    shell:
        "python3 scripts/collect.py --date {wildcards.date}"

rule process_collection:
    input:
        "data/raw/collection_{date}.json"
    output:
        "data/processed/collection_{date}.json"
    shell:
        "python3 scripts/process.py {input} {output}"
```

---

## 3. Workflow Design for TFT Data Curation

### 3.1 Proposed Workflow Structure

```
┌─────────────────────────────────────────────────────────┐
│                    SNAKEMAKE WORKFLOW                   │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │   COLLECT    │───▶│   VALIDATE   │                  │
│  │  (Raw Data)  │    │  (Schema QA) │                  │
│  └──────────────┘    └──────────────┘                  │
│         │                    │                          │
│         │                    ▼                          │
│         │            ┌──────────────┐                  │
│         │            │   TRANSFORM │                  │
│         │            │  (JSON-LD)   │                  │
│         │            └──────────────┘                  │
│         │                    │                          │
│         │                    ▼                          │
│         │            ┌──────────────┐                  │
│         └───────────▶│   QUALITY    │                  │
│                      │  (Metrics)   │                  │
│                      └──────────────┘                  │
│                             │                            │
│                             ▼                            │
│                      ┌──────────────┐                   │
│                      │   PRESERVE   │                   │
│                      │ (Provenance) │                   │
│                      └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Rule Implementation

**Collection Rule:**

```python
# workflow/rules/collect.smk

rule collect_tft_data:
    """
    Collect TFT match data from Riot API.
    """
    input:
        config="config/snakemake_config.yaml"
    output:
        raw_data="data/raw/tft_collection_{date}.json",
        log="logs/collection_{date}.log"
    params:
        region=config["api"]["region"],
        mode=config["collection"]["mode"],
        api_key=lambda: os.environ.get("RIOT_API_KEY", "")
    log:
        "logs/snakemake_collect_{date}.log"
    shell:
        """
        python3 scripts/automated_collection.py \
            --mode {params.mode} \
            --region {params.region} \
            --output {output.raw_data} \
            --log {output.log} \
            2>&1 | tee {log}
        """
```

**Validation Rule:**

```python
# workflow/rules/validate.smk

rule validate_collection:
    """
    Validate collected data using quality assurance modules.
    """
    input:
        raw_data="data/raw/tft_collection_{date}.json"
    output:
        validated_data="data/validated/tft_collection_{date}.json",
        validation_report="reports/validation_{date}.json"
    params:
        quality_threshold=config["quality"]["quality_threshold"]
    log:
        "logs/validate_{date}.log"
    shell:
        """
        python3 -c "
        import json
        from quality_assurance import validate_json_structure, calculate_data_quality_score
        
        with open('{input.raw_data}', 'r') as f:
            data = json.load(f)
        
        validation_result = validate_json_structure(data)
        quality_score = calculate_data_quality_score(data)
        
        report = {{
            'validation': validation_result,
            'quality_score': quality_score,
            'threshold': {params.quality_threshold},
            'passed': quality_score >= {params.quality_threshold}
        }}
        
        with open('{output.validation_report}', 'w') as f:
            json.dump(report, f, indent=2)
        
        if quality_score >= {params.quality_threshold}:
            import shutil
            shutil.copy('{input.raw_data}', '{output.validated_data}')
        else:
            raise ValueError(f'Quality score {{quality_score}} below threshold {{params.quality_threshold}}')
        " 2>&1 | tee {log}
        """
```

**Transformation Rule:**

```python
# workflow/rules/transform.smk

rule transform_to_jsonld:
    """
    Transform validated data to JSON-LD format.
    """
    input:
        validated_data="data/validated/tft_collection_{date}.json"
    output:
        jsonld_data="data/transformed/tft_collection_{date}.jsonld"
    log:
        "logs/transform_{date}.log"
    shell:
        """
        python3 scripts/schema.py \
            --input {input.validated_data} \
            --output {output.jsonld_data} \
            --format jsonld \
            2>&1 | tee {log}
        """
```

**Quality Metrics Rule:**

```python
# workflow/rules/quality.smk

rule calculate_quality_metrics:
    """
    Calculate comprehensive quality metrics for processed data.
    """
    input:
        jsonld_data="data/transformed/tft_collection_{date}.jsonld"
    output:
        quality_report="reports/quality_{date}.json"
    log:
        "logs/quality_{date}.log"
    shell:
        """
        python3 -c "
        import json
        from quality_assurance.quality_metrics import calculate_comprehensive_metrics
        
        with open('{input.jsonld_data}', 'r') as f:
            data = json.load(f)
        
        metrics = calculate_comprehensive_metrics(data)
        
        with open('{output.quality_report}', 'w') as f:
            json.dump(metrics, f, indent=2)
        " 2>&1 | tee {log}
        """
```

**Provenance Rule:**

```python
# workflow/rules/provenance.smk

rule generate_provenance:
    """
    Generate W3C PROV provenance information for the workflow.
    """
    input:
        raw_data="data/raw/tft_collection_{date}.json",
        validated_data="data/validated/tft_collection_{date}.json",
        transformed_data="data/transformed/tft_collection_{date}.jsonld"
    output:
        provenance="provenance/workflow_{date}.prov.json"
    params:
        workflow_version="1.0.0",
        collection_date="{date}"
    log:
        "logs/provenance_{date}.log"
    shell:
        """
        python3 -c "
        import json
        from datetime import datetime
        
        provenance = {{
            '@context': 'https://www.w3.org/ns/prov',
            '@type': 'WorkflowExecution',
            'workflow_version': '{params.workflow_version}',
            'execution_date': datetime.now().isoformat(),
            'collection_date': '{params.collection_date}',
            'inputs': [
                '{input.raw_data}',
                '{input.validated_data}',
                '{input.transformed_data}'
            ],
            'output': '{output.provenance}',
            'snakemake_version': '$(snakemake --version)'
        }}
        
        with open('{output.provenance}', 'w') as f:
            json.dump(provenance, f, indent=2)
        " 2>&1 | tee {log}
        """
```

### 3.3 Main Workflow File

```python
# Snakefile

# Configuration
configfile: "config/snakemake_config.yaml"

# Import rule files
include: "workflow/rules/collect.smk"
include: "workflow/rules/validate.smk"
include: "workflow/rules/transform.smk"
include: "workflow/rules/quality.smk"
include: "workflow/rules/provenance.smk"

# Default target
rule all:
    input:
        "data/transformed/tft_collection_{date}.jsonld",
        "reports/quality_{date}.json",
        "provenance/workflow_{date}.prov.json"
    params:
        date=config.get("collection_date", datetime.now().strftime("%Y%m%d"))
```

---

## 4. Integration with Existing Scripts

### 4.1 Wrapper Scripts

Create wrapper scripts that interface between Snakemake and existing Python modules:

```python
# workflow/scripts/collect_data.py

#!/usr/bin/env python3
"""
Wrapper script for Snakemake to call automated_collection.py
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.automated_collection import AutomatedCollector
from scripts.config_manager import create_config_manager

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log", required=True)
    
    args = parser.parse_args()
    
    # Load configuration
    config_manager = create_config_manager()
    config = config_manager.get_config()
    
    # Update config with Snakemake parameters
    config['collection_mode'] = args.mode
    config['region'] = args.region
    config['output_file'] = args.output
    config['log_file'] = args.log
    
    # Run collection
    collector = AutomatedCollector(config)
    collector.run()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 4.2 Environment Variables

**Set API Key:**

```bash
# In shell or .env file
export RIOT_API_KEY="your_api_key_here"
```

**Use in Snakemake:**

```python
rule collect_data:
    params:
        api_key=lambda: os.environ.get("RIOT_API_KEY", "")
    shell:
        "python3 scripts/collect.py --api-key {params.api_key}"
```

---

## 5. Execution and Usage

### 5.1 Basic Execution

```bash
# Run workflow with default target
snakemake

# Run specific rule
snakemake collect_tft_data

# Run with specific date
snakemake --config collection_date=20251027

# Dry run (show what would be executed)
snakemake --dry-run

# Show execution plan
snakemake --dry-run --printshellcmds
```

### 5.2 Advanced Execution

```bash
# Run with multiple cores
snakemake --cores 4

# Run with conda environment
snakemake --use-conda

# Generate workflow diagram
snakemake --dag | dot -Tsvg > workflow_dag.svg

# Generate rule graph
snakemake --rulegraph | dot -Tsvg > workflow_rules.svg

# Run with logging
snakemake --log-handler-script workflow/scripts/log_handler.py
```

### 5.3 Configuration Override

```bash
# Override config values
snakemake --config api.region=la1 collection.mode=weekly

# Use different config file
snakemake --configfile config/production_config.yaml
```

---

## 6. Testing and Validation

## 6. Testing and Validation

### 6.1 Integration Testing Strategy
The workflow is validated using a comprehensive integration test suite defined in `WORKFLOW_INTEGRATION_TEST_PLAN.md`.

**Test Scenarios:**
1. **Single Date Execution**: End-to-end processing for one day.
2. **Multiple Date Execution**: Parallel processing validation.
3. **Incremental Execution**: Verifying checkpointing and new data handling.

### 6.2 Test Results
The latest test results confirm the stability and correctness of the workflow.

- **Status**: PASSED

### 6.3 Ongoing Validation
To validate changes to the workflow:
```bash
# Run the integration test suite
python3 scripts/test_workflow_integration.py --dates 20251101,20251102
```

---

## 7. Documentation and Maintenance

### 7.1 Workflow Documentation

Add docstrings to rules:

```python
rule collect_tft_data:
    """
    Collect TFT match data from Riot API.
    
    This rule:
    - Collects match data using automated_collection.py
    - Outputs raw JSON data
    - Generates collection logs
    
    Input: Configuration file
    Output: Raw JSON data file and log file
    """
```

### 7.2 Version Control

```bash
# Track workflow files
git add Snakefile workflow/ config/snakemake_config.yaml

# Commit workflow changes
git commit -m "Add Snakemake workflow for reproducible data pipeline"
```

---


---

## 9. Resources

### Official Documentation

- [Snakemake Documentation](https://snakemake.readthedocs.io/)
- [Snakemake Tutorial](https://snakemake.readthedocs.io/en/stable/tutorial/tutorial.html)
- [Best Practices](https://snakemake.readthedocs.io/en/stable/snakefiles/best_practices.html)

### Example Workflows

- [Snakemake Workflow Catalog](https://snakemake.github.io/snakemake-workflow-catalog/)
- [Bioinformatics Workflows](https://github.com/snakemake-workflows)

### Community

- [Snakemake GitHub](https://github.com/snakemake/snakemake)
- [Snakemake Forum](https://github.com/snakemake/snakemake/discussions)

---

## 10. Troubleshooting

### Common Issues

**Issue**: Import errors in rules
**Solution**: Use absolute imports or add project root to PYTHONPATH

**Issue**: Configuration not loading
**Solution**: Check YAML syntax, use `configfile:` directive

**Issue**: Wildcards not matching
**Solution**: Check wildcard patterns, use `expand()` for multiple files

**Issue**: Dependencies not found
**Solution**: Use conda environments or virtual environments

