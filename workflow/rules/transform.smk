# workflow/rules/transform.smk
# Data Transformation Rule

rule transform_to_jsonld:
    """
    Transform validated data to JSON-LD format.
    
    This rule transforms the validated data to JSON-LD format
    using the schema.py script.
    """
    input:
        validated_data="data/validated/tft_collection_{date}.json"
    output:
        jsonld_data="data/transformed/tft_collection_{date}.jsonld"
    log:
        "logs/transform_{date}.log"
    shell:
        """
        # Ensure output directory exists
        mkdir -p $(dirname {output.jsonld_data})
        
        python3 scripts/transform_to_jsonld.py "{input.validated_data}" "{output.jsonld_data}" 2>&1 | tee {log}
        """


rule convert_to_parquet:
    """
    Convert JSON-LD data to optimized Parquet format.
    Creates matches.parquet and participants.parquet.
    """
    input:
        jsonld="data/transformed/tft_collection_{date}.jsonld"
    output:
        matches="data/parquet/{date}/matches.parquet",
        participants="data/parquet/{date}/participants.parquet"
    log:
        "logs/parquet_conversion_{date}.log"
    shell:
        """
        python3 scripts/convert_to_parquet.py --input {input.jsonld} --output data/parquet/{wildcards.date} > {log} 2>&1
        """
