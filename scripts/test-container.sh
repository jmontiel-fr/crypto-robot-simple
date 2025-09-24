#!/bin/bash
# Test script for container functionality without Docker

set -e

echo "🧪 Testing Container Scripts Locally"
echo "===================================="

# Set up test environment
export ENV_CONTENT=""
export CERTIFICATE="crypto-robot.local"
export MODE="webapp"

# Test directory structure
echo "📁 Checking directory structure..."
if [ ! -d "robot" ]; then
    echo "❌ robot directory not found"
    exit 1
fi

if [ ! -d "certificates" ]; then
    echo "❌ certificates directory not found"
    exit 1
fi

echo "✅ Directory structure OK"

# Test .env file handling
echo ""
echo "📝 Testing .env file handling..."

# Create a test .env content
TEST_ENV_CONTENT=$(cat robot/.env | base64 -w 0)
export ENV_CONTENT="$TEST_ENV_CONTENT"

echo "✅ ENV_CONTENT created (${#ENV_CONTENT} characters)"

# Test certificate selection
echo ""
echo "🔒 Testing certificate selection..."

if [ -d "certificates/crypto-robot.local" ]; then
    echo "✅ crypto-robot.local certificates found"
else
    echo "❌ crypto-robot.local certificates not found"
fi

if [ -d "certificates/jack.crypto-robot-itechsource.com" ]; then
    echo "✅ jack.crypto-robot-itechsource.com certificates found"
else
    echo "⚠️  jack.crypto-robot-itechsource.com certificates not found"
fi

# Test script permissions
echo ""
echo "🔧 Testing script permissions..."

for script in scripts/*.sh; do
    if [ -x "$script" ]; then
        echo "✅ $script is executable"
    else
        echo "❌ $script is not executable"
        chmod +x "$script"
        echo "🔧 Fixed permissions for $script"
    fi
done

# Test environment variable decoding
echo ""
echo "🧪 Testing ENV_CONTENT decoding..."

# Create temporary test file
TEMP_ENV=$(mktemp)
echo "$ENV_CONTENT" | base64 -d > "$TEMP_ENV"

if [ $? -eq 0 ]; then
    echo "✅ ENV_CONTENT decoding successful"
    echo "📊 Decoded .env size: $(wc -l < "$TEMP_ENV") lines"
    
    # Show first few lines (without sensitive data)
    echo "📋 Sample configuration:"
    grep -E "^(FLASK_|DOMAIN_|USE_HTTPS)" "$TEMP_ENV" | head -5
else
    echo "❌ ENV_CONTENT decoding failed"
fi

# Cleanup
rm -f "$TEMP_ENV"

# Test Flask configuration extraction
echo ""
echo "🌐 Testing Flask configuration extraction..."

# Simulate configuration extraction
if [ -f "robot/.env" ]; then
    FLASK_PORT=$(grep "^FLASK_PORT=" robot/.env | cut -d'=' -f2 || echo "5000")
    FLASK_HOST=$(grep "^FLASK_HOST=" robot/.env | cut -d'=' -f2 || echo "0.0.0.0")
    USE_HTTPS=$(grep "^USE_HTTPS=" robot/.env | cut -d'=' -f2 || echo "false")
    DOMAIN_NAME=$(grep "^DOMAIN_NAME=" robot/.env | cut -d'=' -f2 || echo "crypto-robot.local")
    
    echo "✅ Configuration extracted:"
    echo "   🔌 Port: $FLASK_PORT"
    echo "   🏠 Host: $FLASK_HOST"
    echo "   🔒 HTTPS: $USE_HTTPS"
    echo "   🏷️  Domain: $DOMAIN_NAME"
else
    echo "❌ robot/.env file not found"
fi

echo ""
echo "🎉 Container script testing completed!"
echo ""
echo "💡 To test with Docker:"
echo "   cd docker"
echo "   ./build.sh"
echo "   docker run -e ENV_CONTENT=\"\$(base64 -w 0 ../robot/.env)\" -e CERTIFICATE=\"crypto-robot.local\" -p 5000:5000 jmontiel/crypto-robot:latest"