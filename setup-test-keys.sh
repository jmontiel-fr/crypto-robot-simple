#!/bin/bash

# Setup Test Keys Script
# This script exports Binance API keys for testing purposes
# Source: .env-jacky file

echo "Setting up Binance test keys..."

# Binance API Configuration
export BINANCE_API_KEY='2N2yZpY20F1RdFrn8cuGabkZJ2LGMFmgOOtneo53bWSP1nMbK2m7PcnLMOYeJ7rX'
export BINANCE_SECRET_KEY='vYZHzyeZnPJEFmdWmCYn1TIIKxjKOBYIwJ2mWpO3jcauZnu5iyVW9pqepluBTC7P'

echo "Binance API keys have been exported to environment variables:"
echo "BINANCE_API_KEY: ${BINANCE_API_KEY:0:10}..."
echo "BINANCE_SECRET_KEY: ${BINANCE_SECRET_KEY:0:10}..."
echo ""
echo "Usage:"
echo "  source ./setup-test-keys.sh    # To export variables in current shell"
echo "  ./setup-test-keys.sh           # To run script (variables won't persist)"
echo ""
echo "Note: These keys are for testing purposes only."
echo "Keep your API keys secure and never share them publicly."
