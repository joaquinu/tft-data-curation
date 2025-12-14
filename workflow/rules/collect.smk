# workflow/rules/collect.smk
# Data Collection Rule
#
# Note: collection_date normalization is handled in Snakefile before rules are included

import os

rule collect_tft_data:
    """
    Clean version: all ${VAR} patterns escaped for Snakemake.
    """

    wildcard_constraints:
        date = r"\d{8}"

    input:
        config="config/snakemake_config.yaml"

    output:
        raw_data="data/raw/tft_collection_{date}.json",
        log="logs/collection_{date}.log"

    params:
        mode=lambda wc: config.get("collection", {}).get("mode", "weekly"),
        output_dir=lambda wc: config.get("collection", {}).get("output_dir", "data/raw"),
        date=lambda wc: wc.date if hasattr(wc, "date") else ""

    log:
        "logs/snakemake_collect_{date}.log"

    shell:
        r"""
        mkdir -p {params.output_dir}
        mkdir -p $(dirname {output.raw_data})

        # Load .env
        if [ -f .env ]; then
            set -a
            source .env
            set +a
        fi

        # Require API key
        if [ -z "$RIOT_API_KEY" ]; then
            echo "ERROR: RIOT_API_KEY is missing" >&2
            exit 1
        fi

        DATE="{params.date}"

        if [ ! -z "$DATE" ]; then
            ############################################
            # DATE MODE
            ############################################

            # Ensure log file directory exists and create empty log file
            mkdir -p $(dirname {output.log})
            touch {output.log}

            read START_TIME END_TIME <<< $(python3 workflow/scripts/calc_timestamps.py "$DATE")

            export START_TIME
            export END_TIME
            export DATE_STR="$DATE"
            export OUTPUT_DIR="{params.output_dir}"
            export LOG_FILE="{output.log}"

            python3 workflow/scripts/collect_date_mode.py 2>&1 | tee -a {log}

            # Verify the expected output file exists
            if [ ! -f {output.raw_data} ]; then
                echo "ERROR: Expected output file {output.raw_data} was not created" >&2
                exit 1
            fi

            # Verify log file exists (ensure it was created by the script)
            if [ ! -f {output.log} ]; then
                echo "ERROR: Log file {output.log} was not created" >&2
                exit 1
            fi

        else
            ############################################
            # WEEKLY MODE
            ############################################

            python3 scripts/automated_collection.py \
                --mode {params.mode} \
                --output-dir {params.output_dir} \
                --log-file {output.log} \
                2>&1 | tee {log}

            # For weekly mode, find the latest file and copy it
            LATEST=$(ls -1t {params.output_dir}/tft_*_collection_*.json 2>/dev/null | head -1)
            
            if [ -z "$LATEST" ]; then
                echo "ERROR: No output JSON produced" >&2
                exit 1
            fi

            cp "$LATEST" {output.raw_data}
        fi
        """
