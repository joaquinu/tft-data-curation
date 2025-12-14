# Snakemake Workflow Usage - Quick Reference

**Quick reference guide for Snakemake workflow usage**

> **For detailed documentation**, see [`workflow/README.md`](../workflow/README.md) (871 lines)

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Snakemake installed: `pip install snakemake>=7.0.0`
- Riot API key: `export RIOT_API_KEY="your_key"`

### Basic Commands

```bash
# Set API key (REQUIRED)
export RIOT_API_KEY="your_api_key_here"

# Dry run (see what would execute)
snakemake --dry-run --config collection_date=20251101

# Run workflow for specific date
snakemake --cores 8 --config collection_date=20251101

# Run all workflow steps
snakemake --cores 8

# Run specific rule
snakemake collect_tft_data --config collection_date=20251101
```

---

## Common Use Cases

### Date-Based Collection

```bash
# Collect data for November 1, 2025
snakemake --cores 8 --config collection_date=20251101

# Multiple dates
snakemake --cores 8 --config collection_date="['20251101', '20251102']"
```

### Weekly Collection

```bash
# Weekly mode (default)
snakemake --cores 8
```

### Workflow Steps

The workflow executes these steps in order:

1. **`collect_tft_data`** - Collect raw data from API
2. **`validate_collection`** - Validate data structure
3. **`transform_to_jsonld`** - Transform to JSON-LD format
4. **`calculate_quality_metrics`** - Calculate quality scores
5. **`validate_cross_cycle`** - Validate retention and volume trends
6. **`generate_provenance`** - Generate W3C PROV provenance
7. **`create_backup`** - Create automated backup

### Run Specific Steps

```bash
# Only collect data
snakemake collect_tft_data --config collection_date=20251101

# Collect and validate
snakemake validate_collection --config collection_date=20251101

# Run from collection to quality assessment
snakemake calculate_quality_metrics --config collection_date=20251101
```

---

## Configuration

### Configuration File

Edit `config/snakemake_config.yaml`:

```yaml
collection_date: ["20251101"]  # Date(s) to collect
collection_period: weekly      # Or: daily, weekly
output_dirs:
  raw: data/raw
  validated: data/validated
  transformed: data/transformed
```

### Environment Variables

Create `.env` file in project root:

```bash
RIOT_API_KEY=your_api_key_here
```

Or export in shell:

```bash
export RIOT_API_KEY="your_api_key_here"
```

---

## Output Files

After running the workflow, you'll find:

- **Raw Data**: `data/raw/tft_collection_20251101.json`
- **Validated Data**: `data/validated/tft_collection_20251101_validated.json`
- **Transformed Data**: `data/transformed/tft_collection_20251101.jsonld`
- **Quality Report**: `reports/quality/tft_collection_20251101_quality.json`
- **Provenance**: `provenance/workflow_20251101.prov.json`
- **Backup**: `backups/tft_collection_20251101_backup.zip`
- **Logs**: `logs/collection_20251101.log`

---

## Troubleshooting

### Common Issues

**Issue**: `RIOT_API_KEY is missing`
```bash
# Solution: Set API key
export RIOT_API_KEY="your_key"
# Or create .env file
echo "RIOT_API_KEY=your_key" > .env
```

**Issue**: `No such file or directory` for scripts
```bash
# Solution: Run from project root
cd /path/to/tft-data-extraction
snakemake --config collection_date=20251101
```

**Issue**: `WorkflowError: Target rules may not contain wildcards`
```bash
# Solution: Specify concrete output file
snakemake data/raw/tft_collection_20251101.json
```

**Issue**: `ModuleNotFoundError`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

---

## Advanced Usage

### Parallel Execution

```bash
# Use 8 cores
snakemake --cores 8 --config collection_date=20251101

# Use all available cores
snakemake --cores all --config collection_date=20251101
```

### Rerun Incomplete

```bash
# Rerun incomplete jobs
snakemake --rerun-incomplete --config collection_date=20251101
```

### Force Execution

```bash
# Force rerun all rules
snakemake --forceall --config collection_date=20251101
```

### Clean Output

```bash
# Remove all output files
snakemake --delete-all-output

# Remove specific rule output
snakemake --delete-temp-output
```

### Multi-week Testing
```bash
# Simulate 4 weeks of data
python3 scripts/simulate_multi_week_data.py --weeks 4
```

---

## Workflow Rules

| Rule | Input | Output | Description |
|------|-------|--------|-------------|
| `collect_tft_data` | config | `data/raw/*.json`, `logs/collection_*.log` | Collect raw data from API |
| `validate_collection` | `data/raw/*.json` | `data/validated/*.json` | Validate data structure |
| `transform_to_jsonld` | `data/validated/*.json` | `data/transformed/*.jsonld` | Transform to JSON-LD |
| `calculate_quality_metrics` | `data/validated/*.json` | `reports/quality/*.json` | Calculate quality scores |
| `validate_cross_cycle` | `reports/quality/*.json` | `reports/cross_cycle/*.json` | Validate cross-cycle trends |
| `generate_provenance` | All outputs | `provenance/*.prov.json` | Generate provenance |
| `create_backup` | All outputs | `backups/*.zip` | Create backup |

---

## Best Practices

1. **Always use dry-run first**: `snakemake --dry-run`
2. **Set API key in `.env` file**: More reliable than shell export
3. **Use specific dates**: `--config collection_date=20251101`
4. **Check logs**: Review `logs/collection_*.log` for issues
5. **Verify outputs**: Check output files exist after execution
6. **Use multiple cores**: `--cores 8` for faster execution

---

## Additional Resources

- **Full Documentation**: [`workflow/README.md`](../workflow/README.md)
- **Workflow Architecture**: [`SNAKEMAKE_WORKFLOW_DESIGN.md`](SNAKEMAKE_WORKFLOW_DESIGN.md)
- **Documentation Index**: [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md)



## Advanced Features

### Archive Release (Long-term Preservation)

```bash
# Create publication-ready archive
snakemake archive_release --cores 1 --config date=20251105 version=1.0.0 archive_description="TFT Set 12 Data"
```

**Output**: Self-contained archive with data, documentation, and metadata suitable for publication.

### Checkpoint & Resume System

**Automatic** - No configuration needed!

```bash
# Start collection
snakemake --cores 8 --config collection_date=20251102

# If interrupted (Ctrl+C) or token expires (403), checkpoint is saved

# Update token and resume
export RIOT_API_KEY="new_token"
snakemake --cores 8 --config collection_date=20251102
# Automatically resumes from checkpoint
```

---

## More Information

For complete documentation, see [`workflow/README.md`](../workflow/README.md)

