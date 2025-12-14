"""
Example script for TFT data collection using the optimized match collector.

This script demonstrates how to use the TFTMatchCollector for data collection.
Note: This is an example script. The actual workflow uses Snakemake.
"""

import os
import json
from datetime import datetime
from scripts.optimized_match_collector import create_match_collector

def main():
    API_KEY = os.getenv("RIOT_API_KEY") or "YOUR_API_KEY_HERE"
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please set your API key via RIOT_API_KEY environment variable!")
        return
    
    collector = create_match_collector(API_KEY)
    
    print("=== TFT Data Collector (Optimized) ===\n")
    print("This script demonstrates the optimized match collector.")
    print("For production use, run the Snakemake workflow instead.\n")
    
    # Example: Collect matches for a small number of players
    print("Example: Collecting matches for top 10 players (last 7 days)...")
    print("Uncomment the code below to run:")
    
    
    print("\nFor production data collection, use:")
    print("  snakemake --cores 8 --config collection_date=20251101")
    print("\nOr for weekly automated collection:")
    print("  snakemake --cores 8")

if __name__ == "__main__":
    main()
