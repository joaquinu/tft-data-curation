#!/usr/bin/env python3
"""
Test script for convert_to_parquet.py fix
Tests the script with various JSON-LD files to verify it works correctly
"""

import subprocess
import sys
from pathlib import Path
import json

def run_parquet_conversion_test(jsonld_file: Path, test_output_dir: Path):
    """Run the Parquet conversion script with a given JSON-LD file"""
    print(f"\n{'='*70}")
    print(f"Testing: {jsonld_file.name}")
    print(f"{'='*70}")
    
    # Clean up test directory
    import shutil
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)
    
    # Run the conversion
    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/convert_to_parquet.py",
                "--input", str(jsonld_file),
                "--output", str(test_output_dir)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Conversion successful!")
            print(result.stdout)
            
            # Verify output files
            matches_file = test_output_dir / "matches.parquet"
            participants_file = test_output_dir / "participants.parquet"
            
            if matches_file.exists() and participants_file.exists():
                print(f"✅ Output files created:")
                print(f"   - {matches_file} ({matches_file.stat().st_size / 1024:.1f} KB)")
                print(f"   - {participants_file} ({participants_file.stat().st_size / 1024:.1f} KB)")
                
                # Try to read the Parquet files to verify they're valid
                try:
                    import pandas as pd
                    df_matches = pd.read_parquet(matches_file)
                    df_participants = pd.read_parquet(participants_file)
                    print(f"✅ Parquet files are valid:")
                    print(f"   - Matches: {len(df_matches)} rows")
                    print(f"   - Participants: {len(df_participants)} rows")
                    return True
                except Exception as e:
                    print(f"❌ Error reading Parquet files: {e}")
                    return False
            else:
                print(f"❌ Output files missing!")
                return False
        else:
            print(f"❌ Conversion failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Conversion timed out (>60 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error running conversion: {e}")
        return False

def verify_jsonld_structure(jsonld_file: Path):
    """Verify the JSON-LD file has the expected structure"""
    print(f"\n📋 Verifying JSON-LD structure: {jsonld_file.name}")
    try:
        with open(jsonld_file, 'r') as f:
            data = json.load(f)
        
        print(f"   Top-level keys: {list(data.keys())[:10]}")
        
        if "matches" in data:
            matches = data["matches"]
            if isinstance(matches, dict):
                print(f"   ✅ Found {len(matches)} matches at top level (dict)")
                return True
            elif isinstance(matches, list):
                print(f"   ✅ Found {len(matches)} matches at top level (list)")
                return True
            else:
                print(f"   ⚠️  Matches exists but wrong type: {type(matches)}")
                return False
        else:
            print(f"   ⚠️  No 'matches' key at top level")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading JSON-LD: {e}")
        return False

def main():
    """Run tests on available JSON-LD files"""
    print("🧪 Testing convert_to_parquet.py Fix")
    print("="*70)
    
    # Find available JSON-LD files
    transformed_dir = Path("data/transformed")
    jsonld_files = list(transformed_dir.glob("tft_collection_*.jsonld"))
    
    if not jsonld_files:
        print("❌ No JSON-LD files found in data/transformed/")
        return 1
    
    print(f"Found {len(jsonld_files)} JSON-LD files to test")
    
    # Test with a few files (to avoid taking too long)
    test_files = jsonld_files[:3]  # Test first 3 files
    
    results = []
    for jsonld_file in test_files:
        # Verify structure first
        if not verify_jsonld_structure(jsonld_file):
            print(f"⚠️  Skipping {jsonld_file.name} - structure issue")
            continue
        
        # Test conversion
        test_output_dir = Path(f"data/parquet/test_{jsonld_file.stem}")
        success = run_parquet_conversion_test(jsonld_file, test_output_dir)
        results.append((jsonld_file.name, success))
        
        # Clean up test directory
        import shutil
        if test_output_dir.exists():
            shutil.rmtree(test_output_dir)
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 Test Summary")
    print(f"{'='*70}")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for filename, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {filename}")
    
    print(f"\n   Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("   🎉 All tests passed! The fix is working correctly.")
        return 0
    else:
        print("   ⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
