#!/bin/bash
# Crypto Robot API Key Injection Script
# Injects Binance API keys from GitHub secrets into .env file

set -e

echo "🔑 Crypto Robot API Key Injection"
echo "================================="

# Configuration
APP_PATH="/opt/crypto-robot"
ENV_FILE="$APP_PATH/.env"
ENV_BACKUP="$APP_PATH/.env.backup"

# Function to validate inputs
validate_inputs() {
    echo "🔍 Validating inputs..."
    
    # Check if hostname is provided
    if [ -z "$HOSTNAME" ]; then
        echo "❌ HOSTNAME environment variable not set"
        echo "💡 Expected format: crypto-robot.local, jack_robot.crypto-vision.com, etc."
        exit 1
    fi
    
    # Generate secret name from hostname
    # Convert hostname to uppercase and replace dots/hyphens with underscores
    SECRET_NAME=$(echo "$HOSTNAME" | tr '[:lower:]' '[:upper:]' | sed 's/[.-]/_/g')
    SECRET_NAME="${SECRET_NAME}_KEYS"
    
    echo "✅ Hostname: $HOSTNAME"
    echo "✅ Secret name: $SECRET_NAME"
}

# Function to retrieve API keys from GitHub secret
retrieve_api_keys() {
    echo "🔍 Retrieving API keys from GitHub secret: $SECRET_NAME"
    
    # Check if the secret environment variable exists
    local secret_var_name="$SECRET_NAME"
    local secret_content="${!secret_var_name}"
    
    if [ -z "$secret_content" ]; then
        echo "❌ GitHub secret not found: $SECRET_NAME"
        echo "💡 Ensure the secret is configured in GitHub with the correct name"
        echo "💡 Expected environment variable: $SECRET_NAME"
        exit 1
    fi
    
    echo "✅ GitHub secret found and retrieved"
    
    # Parse secret content - support both JSON and key=value formats
    if echo "$secret_content" | grep -q "^BINANCE_API_KEY="; then
        # Key=Value format
        echo "📋 Using key=value format for API keys"
        BINANCE_API_KEY=$(echo "$secret_content" | grep "^BINANCE_API_KEY=" | cut -d'=' -f2-)
        BINANCE_SECRET_KEY=$(echo "$secret_content" | grep "^BINANCE_SECRET_KEY=" | cut -d'=' -f2-)
        
    elif echo "$secret_content" | grep -q "{"; then
        # JSON format
        echo "📋 Using JSON format for API keys"
        if command -v jq &> /dev/null; then
            # Use jq if available
            BINANCE_API_KEY=$(echo "$secret_content" | jq -r '.BINANCE_API_KEY // empty')
            BINANCE_SECRET_KEY=$(echo "$secret_content" | jq -r '.BINANCE_SECRET_KEY // empty')
        else
            # Fallback to basic parsing if jq is not available
            echo "⚠️  jq not available, using basic JSON parsing"
            BINANCE_API_KEY=$(echo "$secret_content" | grep -o '"BINANCE_API_KEY"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"BINANCE_API_KEY"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
            BINANCE_SECRET_KEY=$(echo "$secret_content" | grep -o '"BINANCE_SECRET_KEY"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"BINANCE_SECRET_KEY"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
        fi
    else
        echo "❌ Unrecognized secret format"
        echo "💡 Supported formats:"
        echo "   Key=Value: BINANCE_API_KEY=your_key"
        echo "             BINANCE_SECRET_KEY=your_secret"
        echo "   JSON: {\"BINANCE_API_KEY\": \"your_key\", \"BINANCE_SECRET_KEY\": \"your_secret\"}"
        exit 1
    fi
    
    # Validate extracted keys (API keys are required)
    if [ -z "$BINANCE_API_KEY" ] || [ -z "$BINANCE_SECRET_KEY" ]; then
        echo "❌ Failed to extract API keys from secret"
        echo "💡 Supported formats:"
        echo "   Key=Value format:"
        echo "     BINANCE_API_KEY=your_key"
        echo "     BINANCE_SECRET_KEY=your_secret"
        echo "   JSON format:"
        echo "     {\"BINANCE_API_KEY\": \"your_key\", \"BINANCE_SECRET_KEY\": \"your_secret\"}"
        exit 1
    fi
    
    # Basic validation of key format
    if [ ${#BINANCE_API_KEY} -lt 10 ] || [ ${#BINANCE_SECRET_KEY} -lt 10 ]; then
        echo "❌ API keys appear to be too short (possible parsing error)"
        exit 1
    fi
    
    echo "✅ API keys extracted and validated"
}

# Function to backup existing .env file
backup_env_file() {
    if [ -f "$ENV_FILE" ]; then
        echo "💾 Backing up existing .env file..."
        cp "$ENV_FILE" "$ENV_BACKUP"
        echo "✅ Backup created: $ENV_BACKUP"
    else
        echo "⚠️  No existing .env file found"
    fi
}

# Function to inject API keys into .env file
inject_api_keys() {
    echo "🔧 Injecting API keys into .env file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ .env file not found: $ENV_FILE"
        echo "💡 Ensure the base .env file exists before running this script"
        exit 1
    fi
    
    # Create temporary file for modifications
    local temp_file=$(mktemp)
    
    # Process the .env file line by line
    while IFS= read -r line; do
        case "$line" in
            BINANCE_API_KEY=*)
                echo "BINANCE_API_KEY=$BINANCE_API_KEY" >> "$temp_file"
                echo "✅ Updated BINANCE_API_KEY"
                ;;
            BINANCE_SECRET_KEY=*)
                echo "BINANCE_SECRET_KEY=$BINANCE_SECRET_KEY" >> "$temp_file"
                echo "✅ Updated BINANCE_SECRET_KEY"
                ;;
            *)
                echo "$line" >> "$temp_file"
                ;;
        esac
    done < "$ENV_FILE"
    
    # Replace original file with modified version
    mv "$temp_file" "$ENV_FILE"
    
    # Set proper permissions
    chmod 600 "$ENV_FILE"
    chown ec2-user:ec2-user "$ENV_FILE" 2>/dev/null || true
    
    echo "✅ API keys injected successfully"
}

# Function to validate injection
validate_injection() {
    echo "🔍 Validating API key injection..."
    
    # Check if keys were properly injected (without showing the actual keys)
    if grep -q "^BINANCE_API_KEY=" "$ENV_FILE" && grep -q "^BINANCE_SECRET_KEY=" "$ENV_FILE"; then
        echo "✅ API key entries found in .env file"
    else
        echo "❌ API key entries not found in .env file"
        exit 1
    fi
    
    # Verify keys are not the default placeholder values
    if grep -q "BINANCE_API_KEY=your_binance_api_key_here" "$ENV_FILE"; then
        echo "❌ BINANCE_API_KEY still contains placeholder value"
        exit 1
    fi
    
    if grep -q "BINANCE_SECRET_KEY=your_binance_secret_key_here" "$ENV_FILE"; then
        echo "❌ BINANCE_SECRET_KEY still contains placeholder value"
        exit 1
    fi
    
    echo "✅ API key injection validated"
}

# Function to display summary
display_summary() {
    echo ""
    echo "🎉 API Key Injection Complete!"
    echo "=============================="
    echo "📁 Environment file: $ENV_FILE"
    echo "💾 Backup file: $ENV_BACKUP"
    echo "🔑 Secret source: $SECRET_NAME"
    echo "🏷️  Hostname: $HOSTNAME"
    echo ""
    echo "📋 API Keys Updated:"
    echo "  ✅ BINANCE_API_KEY"
    echo "  ✅ BINANCE_SECRET_KEY"
    echo ""
    echo "ℹ️  Note: Flask configuration (FLASK_HOST, FLASK_PORT, USE_HTTPS) is managed in .env file"
    echo ""
    echo "🔒 Security Notes:"
    echo "  - API keys are now configured in .env file"
    echo "  - File permissions set to 600 (owner read/write only)"
    echo "  - Backup of original .env file created"
    echo ""
    echo "🚀 Next Steps:"
    echo "  - Verify application can load the .env file"
    echo "  - Test API connectivity with Binance"
    echo "  - Start the robot or webapp services"
    echo ""
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Environment Variables (required):"
    echo "  HOSTNAME                    Target hostname (e.g., jack_robot.crypto-vision.com)"
    echo "  <HOSTNAME_UPPER>_KEYS      GitHub secret containing API keys (JSON or key=value format)"
    echo ""
    echo "Options:"
    echo "  --validate-only            Only validate inputs without injecting keys"
    echo "  --restore-backup           Restore from backup file"
    echo "  --help                     Show this help message"
    echo ""
    echo "Examples:"
    echo "  HOSTNAME=jack_robot.crypto-vision.com $0"
    echo "  HOSTNAME=crypto-robot.local $0"
    echo ""
    echo "GitHub Secret Formats:"
    echo "  Key=Value format:"
    echo '    BINANCE_API_KEY=your_api_key'
    echo '    BINANCE_SECRET_KEY=your_secret_key'
    echo "  JSON format:"
    echo '    {"BINANCE_API_KEY": "your_api_key", "BINANCE_SECRET_KEY": "your_secret_key"}'
    echo ""
}

# Function to restore from backup
restore_backup() {
    echo "🔄 Restoring .env file from backup..."
    
    if [ ! -f "$ENV_BACKUP" ]; then
        echo "❌ Backup file not found: $ENV_BACKUP"
        exit 1
    fi
    
    cp "$ENV_BACKUP" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    chown ec2-user:ec2-user "$ENV_FILE" 2>/dev/null || true
    
    echo "✅ .env file restored from backup"
}

# Parse command line arguments
VALIDATE_ONLY=false
RESTORE_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --restore-backup)
            RESTORE_BACKUP=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution flow
main() {
    if [ "$RESTORE_BACKUP" = true ]; then
        restore_backup
        exit 0
    fi
    
    echo "🚀 Starting API key injection..."
    
    validate_inputs
    
    if [ "$VALIDATE_ONLY" = true ]; then
        echo "✅ Validation completed successfully"
        exit 0
    fi
    
    retrieve_api_keys
    backup_env_file
    inject_api_keys
    validate_injection
    display_summary
    
    echo "🎉 API key injection completed successfully!"
}

# Error handling
trap 'echo "❌ API key injection failed at line $LINENO. Exit code: $?"' ERR

# Execute main function
main "$@"