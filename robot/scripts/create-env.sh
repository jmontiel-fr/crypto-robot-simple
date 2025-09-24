#!/bin/bash

# Environment initialization script for crypto-robot deployment
# This script handles .env file setup for EC2 deployment
# Usage: ./scripts/create-env.sh [source_file] [target_file]

set -e  # Exit on any error

# Configuration
DEFAULT_SOURCE_FILE=".env-aws"
DEFAULT_TARGET_FILE=".env"
APP_DIR="/opt/crypto-robot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [source_file] [target_file]"
    echo ""
    echo "Parameters:"
    echo "  source_file  - Source .env file (default: $DEFAULT_SOURCE_FILE)"
    echo "  target_file  - Target .env file (default: $DEFAULT_TARGET_FILE)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Copy .env-aws to .env"
    echo "  $0 .env-prod .env           # Copy .env-prod to .env"
    echo "  $0 .env-local .env-backup   # Copy .env-local to .env-backup"
    echo ""
    echo "Environment Variables:"
    echo "  APP_DIR      - Application directory (default: $APP_DIR)"
    echo ""
    echo "This script:"
    echo "  1. Validates source file exists and is readable"
    echo "  2. Creates backup of existing target file if it exists"
    echo "  3. Copies source to target with proper permissions"
    echo "  4. Validates the new .env file format"
    echo "  5. Reports configuration summary"
}

# Function to validate .env file format
validate_env_file() {
    local env_file="$1"
    local validation_errors=0
    
    print_status "Validating .env file format: $env_file"
    
    # Check for required variables
    local required_vars=(
        "FLASK_PORT"
        "FLASK_PROTOCOL"
        "FLASK_HOST"
        "HOSTNAME"
        "BINANCE_API_KEY"
        "BINANCE_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file"; then
            print_warning "Missing required variable: $var"
            validation_errors=$((validation_errors + 1))
        fi
    done
    
    # Check for common format issues
    if grep -q "^[[:space:]]*#" "$env_file"; then
        print_status "Found commented lines (this is normal)"
    fi
    
    # Check for empty values
    local empty_vars=$(grep -E "^[A-Z_]+=\s*$" "$env_file" | cut -d'=' -f1 || true)
    if [ -n "$empty_vars" ]; then
        print_warning "Found variables with empty values:"
        echo "$empty_vars" | while read -r var; do
            echo "  - $var"
        done
    fi
    
    # Check for suspicious patterns
    if grep -q "localhost" "$env_file"; then
        print_warning "Found 'localhost' in configuration - may not work in containerized environment"
    fi
    
    if [ $validation_errors -eq 0 ]; then
        print_success "Environment file validation passed"
        return 0
    else
        print_error "Environment file validation found $validation_errors issues"
        return 1
    fi
}

# Function to show configuration summary
show_config_summary() {
    local env_file="$1"
    
    print_status "Configuration Summary from $env_file:"
    echo "=================================="
    
    # Extract and display key configuration values
    local flask_port=$(grep "^FLASK_PORT=" "$env_file" | cut -d'=' -f2 | tr -d '"' || echo "not set")
    local flask_protocol=$(grep "^FLASK_PROTOCOL=" "$env_file" | cut -d'=' -f2 | tr -d '"' || echo "not set")
    local flask_host=$(grep "^FLASK_HOST=" "$env_file" | cut -d'=' -f2 | tr -d '"' || echo "not set")
    local hostname=$(grep "^HOSTNAME=" "$env_file" | cut -d'=' -f2 | tr -d '"' || echo "not set")
    local binance_testnet=$(grep "^BINANCE_TESTNET=" "$env_file" | cut -d'=' -f2 | tr -d '"' || echo "not set")
    local debug=$(grep "^DEBUG=" "$env_file" | cut -d'=' -f2 | tr -d '"' || echo "not set")
    
    echo "Flask Configuration:"
    echo "  Protocol: $flask_protocol"
    echo "  Host: $flask_host"
    echo "  Port: $flask_port"
    echo ""
    echo "Application Configuration:"
    echo "  Hostname: $hostname"
    echo "  Debug Mode: $debug"
    echo "  Binance Testnet: $binance_testnet"
    echo ""
    
    # Check if API keys are configured
    if grep -q "^BINANCE_API_KEY=.\+" "$env_file"; then
        echo "Binance API: ✅ API key configured"
    else
        echo "Binance API: ❌ API key not configured"
    fi
    
    if grep -q "^BINANCE_SECRET_KEY=.\+" "$env_file"; then
        echo "Binance Secret: ✅ Secret key configured"
    else
        echo "Binance Secret: ❌ Secret key not configured"
    fi
    
    echo "=================================="
}

# Function to create backup
create_backup() {
    local target_file="$1"
    local backup_file="${target_file}.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [ -f "$target_file" ]; then
        print_status "Creating backup: $backup_file"
        cp "$target_file" "$backup_file"
        print_success "Backup created successfully"
        return 0
    else
        print_status "No existing target file to backup"
        return 0
    fi
}

# Function to set proper permissions
set_permissions() {
    local env_file="$1"
    
    print_status "Setting secure permissions for $env_file"
    
    # Set file permissions to be readable only by owner
    chmod 600 "$env_file"
    
    # Verify permissions
    local perms=$(stat -c "%a" "$env_file" 2>/dev/null || stat -f "%A" "$env_file" 2>/dev/null || echo "unknown")
    print_success "File permissions set to: $perms"
}

# Main function
main() {
    # Parse arguments
    local source_file="${1:-$DEFAULT_SOURCE_FILE}"
    local target_file="${2:-$DEFAULT_TARGET_FILE}"
    
    # Handle help
    if [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    print_status "Environment initialization starting..."
    print_status "Source file: $source_file"
    print_status "Target file: $target_file"
    print_status "Working directory: $(pwd)"
    
    # Change to app directory if it exists and we're not already there
    if [ -d "$APP_DIR" ] && [ "$(pwd)" != "$APP_DIR" ]; then
        print_status "Changing to application directory: $APP_DIR"
        cd "$APP_DIR"
    fi
    
    # Validate source file exists
    if [ ! -f "$source_file" ]; then
        print_error "Source file not found: $source_file"
        print_error "Please ensure the source .env file exists"
        exit 1
    fi
    
    # Check if source file is readable
    if [ ! -r "$source_file" ]; then
        print_error "Source file is not readable: $source_file"
        print_error "Please check file permissions"
        exit 1
    fi
    
    print_success "Source file found and readable: $source_file"
    
    # Create backup of existing target file
    create_backup "$target_file"
    
    # Copy source to target
    print_status "Copying $source_file to $target_file"
    cp "$source_file" "$target_file"
    
    # Set proper permissions
    set_permissions "$target_file"
    
    # Validate the new .env file
    if validate_env_file "$target_file"; then
        print_success "Environment file validation successful"
    else
        print_warning "Environment file validation found issues, but continuing..."
    fi
    
    # Show configuration summary
    show_config_summary "$target_file"
    
    print_success "Environment initialization completed successfully!"
    print_status "Target file: $(pwd)/$target_file"
    
    # Provide next steps
    echo ""
    print_status "Next steps:"
    echo "  1. Review the configuration summary above"
    echo "  2. Test the application with the new environment"
    echo "  3. Use Docker commands with ENV_CONTENT=\$(base64 robot7/$target_file)"
    echo ""
    
    # Show Docker usage example
    print_status "Docker usage example:"
    echo "  docker run -d --name crypto-robot \\"
    echo "    -e ENV_CONTENT=\"\$(base64 -w 0 robot7/$target_file)\" \\"
    echo "    -e CERTIFICATE=\"$hostname\" \\"
    echo "    -p $flask_port:$flask_port \\"
    echo "    jmontiel/crypto-robot:latest"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi