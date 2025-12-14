#!/bin/bash
# Snakemake Setup Script for TFT Data Curation Project


set -e  # Exit on error

echo "=========================================="
echo "Snakemake Setup for TFT Data Curation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Install Snakemake
echo ""
echo "Installing Snakemake..."
pip install snakemake>=7.0.0

# Install optional dependencies
echo ""
echo "Installing optional dependencies..."
pip install graphviz pyyaml || echo "Warning: Optional dependencies not installed"

# Verify installation
echo ""
echo "Verifying Snakemake installation..."
snakemake --version || { echo "Error: Snakemake installation failed"; exit 1; }

# Create directory structure
echo ""
echo "Creating workflow directory structure..."
mkdir -p workflow/rules
mkdir -p workflow/scripts
mkdir -p workflow/envs
mkdir -p data/raw
mkdir -p data/validated
mkdir -p data/transformed
mkdir -p data/final
mkdir -p logs
mkdir -p reports
mkdir -p provenance

echo ""
echo "Snakemake setup complete!"
echo ""
echo "Next steps:"
echo "1. Review Documents/SNAKEMAKE_IMPLEMENTATION_GUIDE.md"
echo "2. Create config/snakemake_config.yaml"
echo "3. Create Snakefile in project root"
echo "4. Create workflow rules in workflow/rules/"
echo ""
echo "To test installation:"
echo "  snakemake --version"
echo "  snakemake --help"
echo ""

