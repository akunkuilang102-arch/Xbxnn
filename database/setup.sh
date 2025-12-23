#!/bin/bash
# setup.sh - Setup script for Spaceman Bot

echo "🚀 Setting up Spaceman Bot..."

# Install dependencies
pip install -r requirements.txt || pip3 install -r requirements.txt

# Create directories
mkdir -p database logs backups

echo "✅ Setup complete!"
echo "👉 Bot will start automatically on Railway"