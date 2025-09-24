#!/bin/bash
# Crypto Robot - API Keys Setup Script
# This script helps you securely configure Binance API keys

echo "🔐 Crypto Robot - API Keys Setup"
echo "================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please make sure you're running this script from the project root directory."
    exit 1
fi

# Determine if this is for testnet or mainnet
MODE="mainnet"
if [ "$1" = "testnet" ]; then
    MODE="testnet"
    echo "🧪 Setting up TESTNET API keys"
    echo "Get testnet keys from: https://testnet.binance.vision/"
else
    echo "🏦 Setting up MAINNET API keys"
    echo "Get mainnet keys from: https://www.binance.com/en/my/settings/api-management"
fi

echo ""
echo "⚠️  SECURITY WARNINGS:"
echo "• Never share your API keys with anyone"
echo "• Use IP restrictions on your API keys"
echo "• Enable only necessary permissions (Spot Trading)"
echo "• Consider using testnet for initial testing"
echo ""

# Read API key
echo -n "Enter your Binance API Key: "
read -r API_KEY

if [ -z "$API_KEY" ]; then
    echo "❌ API key cannot be empty!"
    exit 1
fi

# Read secret key (hidden input)
echo -n "Enter your Binance Secret Key: "
read -s SECRET_KEY
echo ""

if [ -z "$SECRET_KEY" ]; then
    echo "❌ Secret key cannot be empty!"
    exit 1
fi

echo ""
echo "🔧 Configuring API keys..."

# Backup existing .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "📦 Backup created: .env.backup.$(date +%Y%m%d_%H%M%S)"

# Remove any existing API key lines
sed -i '/^BINANCE_API_KEY=/d' .env
sed -i '/^BINANCE_SECRET_KEY=/d' .env

# Add new API keys to .env
echo "" >> .env
echo "# Binance API Keys (configured via setup_keys.sh)" >> .env
echo "BINANCE_API_KEY='$API_KEY'" >> .env
echo "BINANCE_SECRET_KEY='$SECRET_KEY'" >> .env

echo "✅ API keys configured successfully!"
echo ""

if [ "$MODE" = "testnet" ]; then
    echo "🧪 TESTNET MODE:"
    echo "• Your keys are configured for Binance Testnet"
    echo "• Use testnet.binance.vision for testing"
    echo "• No real money will be used"
else
    echo "🏦 MAINNET MODE:"
    echo "• Your keys are configured for Binance Mainnet"
    echo "• REAL MONEY will be used for trading"
    echo "• Start with small amounts for testing"
fi

echo ""
echo "📝 Next steps:"
echo "1. Verify your API keys work: python src/binance_client.py"
echo "2. Check your account balance in the web interface"
echo "3. Start with simulation mode to test strategies"
echo "4. Review trading settings in .env file"
echo ""
echo "🚀 You can now start the crypto robot!"
