#!/bin/bash

# Create .env file with embedded certificate content
# Usage: ./tools/create-env-with-certs.sh <hostname> <output-file>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    echo "Usage: $0 <hostname> <output-file>"
    echo ""
    echo "Parameters:"
    echo "  hostname     - Certificate hostname (e.g., crypto-robot.local)"
    echo "  output-file  - Output .env file path"
    echo ""
    echo "Examples:"
    echo "  $0 crypto-robot.local .env-local"
    echo "  $0 jack.crypto-robot-itechsource.com .env-production"
    echo ""
    echo "This script:"
    echo "  1. Reads certificate files from certificates/<hostname>/"
    echo "  2. Embeds certificate content as strings in .env file"
    echo "  3. Creates a complete .env file ready for Docker deployment"
}

# Parse arguments
if [ $# -ne 2 ]; then
    print_error "Invalid number of arguments"
    show_usage
    exit 1
fi

HOSTNAME="$1"
OUTPUT_FILE="$2"

# Validate hostname
if [ -z "$HOSTNAME" ]; then
    print_error "Hostname cannot be empty"
    exit 1
fi

# Certificate paths
CERT_DIR="certificates/$HOSTNAME"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

print_status "Creating .env file with embedded certificates"
print_status "Hostname: $HOSTNAME"
print_status "Certificate directory: $CERT_DIR"
print_status "Output file: $OUTPUT_FILE"

# Check if certificate files exist
if [ ! -f "$CERT_FILE" ]; then
    print_error "Certificate file not found: $CERT_FILE"
    print_error "Please generate certificates first using:"
    print_error "  ./tools/generate-certificates.sh $HOSTNAME self-signed"
    print_error "  or"
    print_error "  ./tools/generate-certificates.sh $HOSTNAME letsencrypt"
    exit 1
fi

if [ ! -f "$KEY_FILE" ]; then
    print_error "Private key file not found: $KEY_FILE"
    exit 1
fi

# Read certificate content
print_status "Reading certificate files..."
CERT_CONTENT=$(cat "$CERT_FILE")
KEY_CONTENT=$(cat "$KEY_FILE")

# Validate certificate content
if ! echo "$CERT_CONTENT" | grep -q "BEGIN CERTIFICATE"; then
    print_error "Invalid certificate format in $CERT_FILE"
    exit 1
fi

if ! echo "$KEY_CONTENT" | grep -q "BEGIN.*PRIVATE KEY"; then
    print_error "Invalid private key format in $KEY_FILE"
    exit 1
fi

print_success "Certificate files validated"

# Determine configuration based on hostname
if [[ "$HOSTNAME" == "crypto-robot.local" ]]; then
    FLASK_PORT="5000"
    FLASK_PROTOCOL="http"
    CERTIFICATE_TYPE="self-signed"
    DEBUG="true"
    BINANCE_TESTNET="true"
    STARTING_CAPITAL="100"
    API_KEY_PLACEHOLDER="your_testnet_api_key"
    SECRET_KEY_PLACEHOLDER="your_testnet_secret_key"
else
    FLASK_PORT="5443"
    FLASK_PROTOCOL="https"
    CERTIFICATE_TYPE="letsencrypt"
    DEBUG="false"
    BINANCE_TESTNET="false"
    STARTING_CAPITAL="1000"
    API_KEY_PLACEHOLDER="your_production_api_key"
    SECRET_KEY_PLACEHOLDER="your_production_secret_key"
fi

# Create .env file
print_status "Creating .env file: $OUTPUT_FILE"

cat > "$OUTPUT_FILE" << EOF
# Environment configuration for $HOSTNAME
# Generated on $(date)

# Flask Configuration
FLASK_PORT=$FLASK_PORT
FLASK_PROTOCOL=$FLASK_PROTOCOL
FLASK_HOST=0.0.0.0

# Certificate Configuration
HOSTNAME=$HOSTNAME
CERTIFICATE_TYPE=$CERTIFICATE_TYPE

# SSL Certificate Content (embedded as strings)
SSL_CERT_CONTENT="$CERT_CONTENT"

SSL_KEY_CONTENT="$KEY_CONTENT"

# Application Configuration
DEBUG=$DEBUG
BINANCE_TESTNET=$BINANCE_TESTNET
BINANCE_API_KEY=$API_KEY_PLACEHOLDER
BINANCE_SECRET_KEY=$SECRET_KEY_PLACEHOLDER

# Portfolio Configuration
STARTING_CAPITAL=$STARTING_CAPITAL
DEFAULT_CALIBRATION_PROFILE=moderate_realistic
ENABLE_CALIBRATION=true

# Additional Configuration
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=30
EOF

# Set proper permissions
chmod 600 "$OUTPUT_FILE"

print_success ".env file created successfully: $OUTPUT_FILE"

# Show summary
print_status "Configuration Summary:"
echo "  Hostname: $HOSTNAME"
echo "  Flask Port: $FLASK_PORT"
echo "  Flask Protocol: $FLASK_PROTOCOL"
echo "  Certificate Type: $CERTIFICATE_TYPE"
echo "  Debug Mode: $DEBUG"
echo "  Binance Testnet: $BINANCE_TESTNET"
echo "  Starting Capital: $STARTING_CAPITAL"

print_warning "IMPORTANT: Update the API keys in $OUTPUT_FILE before use!"
print_warning "Replace $API_KEY_PLACEHOLDER and $SECRET_KEY_PLACEHOLDER with actual values"

# Show next steps
print_status "Next steps:"
echo "  1. Edit $OUTPUT_FILE and update API keys"
echo "  2. Test locally: docker run -e ENV_CONTENT=\"\$(base64 -w 0 $OUTPUT_FILE)\" -e CERTIFICATE=\"$HOSTNAME\" crypto-robot"
echo "  3. For GitHub Actions: base64 -w 0 $OUTPUT_FILE (copy to GitHub environment secret)"

print_success "Environment file creation completed!"