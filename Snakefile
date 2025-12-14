# Snakefile
# TFT Data Curation Workflow

# Configuration
configfile: "config/snakemake_config.yaml"

# Normalize collection_date to always be a list (must be done before rules are included)
# This ensures that when rules access config.get("collection_date"), it's already normalized
collection_date_raw = config.get("collection_date", ["20251027"])
if isinstance(collection_date_raw, str):
    config["collection_date"] = [collection_date_raw]
elif not isinstance(collection_date_raw, list):
    config["collection_date"] = [str(collection_date_raw)]

# Import rule files (after config normalization)
include: "workflow/rules/collect.smk"
include: "workflow/rules/validate.smk"
include: "workflow/rules/transform.smk"
include: "workflow/rules/quality.smk"
include: "workflow/rules/provenance.smk"
include: "workflow/rules/backup.smk"

# Function to normalize collection_date (handles --config overrides)
def get_collection_dates():
    """Get collection_date as a list, normalizing if needed"""
    coll_date = config.get("collection_date", ["20251027"])
    if isinstance(coll_date, str):
        return [coll_date]
    elif not isinstance(coll_date, list):
        return [str(coll_date)]
    return coll_date

# Normalize collection_date in config itself (for use in rules)
collection_dates = get_collection_dates()
config["collection_date"] = collection_dates

# Default target rule
# Usage: snakemake --config collection_date=20251027
# Or: snakemake --config collection_date=20251027 all
rule all:
    input:
        expand(
            "data/transformed/tft_collection_{date}.jsonld",
            date=get_collection_dates()
        ),
        expand(
            "reports/quality_{date}.json",
            date=get_collection_dates()
        ),
        expand(
            "provenance/workflow_{date}.prov.json",
            date=get_collection_dates()
        ),
        expand(
            "reports/cross_cycle_{date}.json",
            date=get_collection_dates()
        ),
        # Include backup if enabled
        expand(
            "backups/backup_{date}.tar.gz",
            date=get_collection_dates()
        ) if config.get("backup", {}).get("auto_backup", True) else [],
        expand(
            "data/parquet/{date}/matches.parquet",
            date=get_collection_dates()
        )