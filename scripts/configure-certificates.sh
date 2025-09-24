#!/bin/bash
# Crypto Robot Certificate Configuration Script
# Configures SSL certificates for direct Python deployment

set -e

echo "🔒 Crypto Robot Certificate Configuration"
echo "========================================"

# Configuration
APP_PATH="/opt/crypto-robot"
CERT_BASE_DIR="$APP_PATH/certificates"
ENV_FILE="$APP_PATH/.env"

# Function to validate hostname
validate_hostname() {
    local hostname="$1"
    
    if [ -z "$hostname" ]; then
        echo "❌ Hostname not provided"
        return 1
    fi
    
    # Basic hostname validation
    if [[ ! "$hostname" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        echo "❌ Invalid hostname format: $hostname"
        return 1
    fi
    
    echo "✅ Hostname validated: $hostname"
    return 0
}

# Function to create certificate directory structure
create_cert_directories() {
    local hostname="$1"
    local cert_dir="$CERT_BASE_DIR/$hostname"
    
    echo "📁 Creating certificate directories..."
    
    # Create base certificate directory
    mkdir -p "$CERT_BASE_DIR"
    chmod 755 "$CERT_BASE_DIR"
    
    # Create hostname-specific directory
    mkdir -p "$cert_dir"
    chmod 700 "$cert_dir"  # Restrictive permissions for certificate directory
    
    # Set ownership
    chown -R ec2-user:ec2-user "$CERT_BASE_DIR"
    
    echo "✅ Certificate directories created: $cert_dir"
}

# Function to extract certificates from environment variables
extract_certificates_from_env() {
    local hostname="$1"
    local cert_dir="$CERT_BASE_DIR/$hostname"
    
    echo "🔍 Extracting certificates from environment variables..."
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ Environment file not found: $ENV_FILE"
        return 1
    fi
    
    # Load environment variables
    source "$ENV_FILE"
    
    # Check if certificate content exists in environment
    if [ -n "$SSL_CERT_CONTENT" ] && [ -n "$SSL_KEY_CONTENT" ]; then
        echo "📄 Extracting certificate content..."
        
        # Extract certificate
        echo "$SSL_CERT_CONTENT" > "$cert_dir/cert.pem"
        chmod 644 "$cert_dir/cert.pem"
        
        # Extract private key
        echo "$SSL_KEY_CONTENT" > "$cert_dir/key.pem"
        chmod 600 "$cert_dir/key.pem"
        
        # Set ownership
        chown ec2-user:ec2-user "$cert_dir/cert.pem" "$cert_dir/key.pem"
        
        echo "✅ Certificates extracted successfully"
        return 0
    else
        echo "⚠️  SSL certificate content not found in environment variables"
        return 1
    fi
}

# Function to copy certificates from files
copy_certificates_from_files() {
    local hostname="$1"
    local cert_file="$2"
    local key_file="$3"
    local cert_dir="$CERT_BASE_DIR/$hostname"
    
    echo "📋 Copying certificates from files..."
    
    # Validate input files
    if [ ! -f "$cert_file" ]; then
        echo "❌ Certificate file not found: $cert_file"
        return 1
    fi
    
    if [ ! -f "$key_file" ]; then
        echo "❌ Private key file not found: $key_file"
        return 1
    fi
    
    # Copy certificate
    cp "$cert_file" "$cert_dir/cert.pem"
    chmod 644 "$cert_dir/cert.pem"
    
    # Copy private key
    cp "$key_file" "$cert_dir/key.pem"
    chmod 600 "$cert_dir/key.pem"
    
    # Set ownership
    chown ec2-user:ec2-user "$cert_dir/cert.pem" "$cert_dir/key.pem"
    
    echo "✅ Certificates copied successfully"
}

# Function to validate certificates
validate_certificates() {
    local hostname="$1"
    local cert_dir="$CERT_BASE_DIR/$hostname"
    local cert_file="$cert_dir/cert.pem"
    local key_file="$cert_dir/key.pem"
    
    echo "🔍 Validating certificates..."
    
    # Check if files exist
    if [ ! -f "$cert_file" ] || [ ! -f "$key_file" ]; then
        echo "❌ Certificate files not found"
        return 1
    fi
    
    # Validate certificate format
    if ! openssl x509 -in "$cert_file" -noout -text >/dev/null 2>&1; then
        echo "❌ Invalid certificate format"
        return 1
    fi
    
    # Validate private key format
    if ! openssl rsa -in "$key_file" -noout -check >/dev/null 2>&1; then
        echo "❌ Invalid private key format"
        return 1
    fi
    
    # Check if certificate and key match
    local cert_modulus=$(openssl x509 -noout -modulus -in "$cert_file" 2>/dev/null | openssl md5)
    local key_modulus=$(openssl rsa -noout -modulus -in "$key_file" 2>/dev/null | openssl md5)
    
    if [ "$cert_modulus" != "$key_modulus" ]; then
        echo "❌ Certificate and private key do not match"
        return 1
    fi
    
    # Check certificate expiration
    local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
    local expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
    local current_epoch=$(date +%s)
    
    if [ "$expiry_epoch" -le "$current_epoch" ]; then
        echo "❌ Certificate has expired"
        return 1
    fi
    
    local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [ "$days_until_expiry" -lt 30 ]; then
        echo "⚠️  Certificate expires in $days_until_expiry days"
    else
        echo "✅ Certificate valid for $days_until_expiry days"
    fi
    
    # Check certificate subject
    local cert_subject=$(openssl x509 -subject -noout -in "$cert_file" | sed 's/subject=//')
    echo "📋 Certificate subject: $cert_subject"
    
    # Check certificate SAN (Subject Alternative Names)
    local san_names=$(openssl x509 -text -noout -in "$cert_file" | grep -A1 "Subject Alternative Name" | tail -1 | sed 's/DNS://g' | sed 's/,//g' || echo "")
    if [ -n "$san_names" ]; then
        echo "📋 SAN names: $san_names"
    fi
    
    echo "✅ Certificate validation completed"
    return 0
}

# Function to update environment file with certificate paths
update_env_certificate_paths() {
    local hostname="$1"
    local cert_dir="$CERT_BASE_DIR/$hostname"
    
    echo "🔧 Updating environment file with certificate paths..."
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ Environment file not found: $ENV_FILE"
        return 1
    fi
    
    # Create backup
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d-%H%M%S)"
    
    # Update certificate paths
    local cert_path="$cert_dir/cert.pem"
    local key_path="$cert_dir/key.pem"
    
    # Update or add SSL_CERT_PATH
    if grep -q "^SSL_CERT_PATH=" "$ENV_FILE"; then
        sed -i "s|^SSL_CERT_PATH=.*|SSL_CERT_PATH=$cert_path|" "$ENV_FILE"
    else
        echo "SSL_CERT_PATH=$cert_path" >> "$ENV_FILE"
    fi
    
    # Update or add SSL_KEY_PATH
    if grep -q "^SSL_KEY_PATH=" "$ENV_FILE"; then
        sed -i "s|^SSL_KEY_PATH=.*|SSL_KEY_PATH=$key_path|" "$ENV_FILE"
    else
        echo "SSL_KEY_PATH=$key_path" >> "$ENV_FILE"
    fi
    
    # Update or add DOMAIN_NAME
    if grep -q "^DOMAIN_NAME=" "$ENV_FILE"; then
        sed -i "s|^DOMAIN_NAME=.*|DOMAIN_NAME=$hostname|" "$ENV_FILE"
    else
        echo "DOMAIN_NAME=$hostname" >> "$ENV_FILE"
    fi
    
    # Ensure HTTPS is enabled if certificates are configured
    if grep -q "^USE_HTTPS=" "$ENV_FILE"; then
        sed -i "s|^USE_HTTPS=.*|USE_HTTPS=true|" "$ENV_FILE"
    else
        echo "USE_HTTPS=true" >> "$ENV_FILE"
    fi
    
    if grep -q "^FLASK_PROTOCOL=" "$ENV_FILE"; then
        sed -i "s|^FLASK_PROTOCOL=.*|FLASK_PROTOCOL=https|" "$ENV_FILE"
    else
        echo "FLASK_PROTOCOL=https" >> "$ENV_FILE"
    fi
    
    echo "✅ Environment file updated with certificate paths"
}

# Function to test certificate configuration
test_certificate_configuration() {
    local hostname="$1"
    
    echo "🧪 Testing certificate configuration..."
    
    # Load environment to get port
    source "$ENV_FILE"
    local port="${FLASK_PORT:-5000}"
    
    echo "🔍 Testing HTTPS configuration on port $port..."
    
    # Test if we can create an SSL context (basic test)
    if command -v python3 >/dev/null 2>&1; then
        local ssl_test_result=$(python3 -c "
import ssl
import os
try:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('$CERT_BASE_DIR/$hostname/cert.pem', '$CERT_BASE_DIR/$hostname/key.pem')
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
        
        if [[ "$ssl_test_result" == "SUCCESS" ]]; then
            echo "✅ SSL context creation successful"
        else
            echo "❌ SSL context creation failed: $ssl_test_result"
            return 1
        fi
    else
        echo "⚠️  Python3 not available for SSL testing"
    fi
    
    echo "✅ Certificate configuration test completed"
}

# Function to list available certificates
list_certificates() {
    echo "📋 Available Certificates:"
    echo "========================="
    
    if [ ! -d "$CERT_BASE_DIR" ]; then
        echo "⚠️  No certificate directory found: $CERT_BASE_DIR"
        return 0
    fi
    
    local found_certs=false
    
    for cert_dir in "$CERT_BASE_DIR"/*; do
        if [ -d "$cert_dir" ]; then
            local hostname=$(basename "$cert_dir")
            local cert_file="$cert_dir/cert.pem"
            local key_file="$cert_dir/key.pem"
            
            echo ""
            echo "🏷️  Hostname: $hostname"
            echo "📁 Directory: $cert_dir"
            
            if [ -f "$cert_file" ] && [ -f "$key_file" ]; then
                echo "📄 Certificate: ✅ Present"
                echo "🔑 Private Key: ✅ Present"
                
                # Show certificate details
                local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2 || echo "Unknown")
                echo "📅 Expires: $expiry_date"
                
                local cert_subject=$(openssl x509 -subject -noout -in "$cert_file" 2>/dev/null | sed 's/subject=//' || echo "Unknown")
                echo "📋 Subject: $cert_subject"
            else
                echo "📄 Certificate: ❌ Missing"
                echo "🔑 Private Key: ❌ Missing"
            fi
            
            found_certs=true
        fi
    done
    
    if [ "$found_certs" = false ]; then
        echo "⚠️  No certificates found"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 COMMAND [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup HOSTNAME              Setup certificates for hostname"
    echo "  extract HOSTNAME            Extract certificates from environment variables"
    echo "  copy HOSTNAME CERT KEY      Copy certificates from files"
    echo "  validate HOSTNAME           Validate existing certificates"
    echo "  update-env HOSTNAME         Update .env file with certificate paths"
    echo "  test HOSTNAME               Test certificate configuration"
    echo "  list                        List all available certificates"
    echo ""
    echo "Examples:"
    echo "  $0 setup jack_robot.crypto-vision.com"
    echo "  $0 extract crypto-robot.local"
    echo "  $0 copy example.com /path/to/cert.pem /path/to/key.pem"
    echo "  $0 validate jack_robot.crypto-vision.com"
    echo "  $0 list"
    echo ""
}

# Main execution
main() {
    local command="${1:-}"
    local hostname="${2:-}"
    local cert_file="${3:-}"
    local key_file="${4:-}"
    
    case "$command" in
        "setup")
            if [ -z "$hostname" ]; then
                echo "❌ Hostname required"
                show_usage
                exit 1
            fi
            
            validate_hostname "$hostname"
            create_cert_directories "$hostname"
            
            # Try to extract from environment first, then prompt for files
            if extract_certificates_from_env "$hostname"; then
                validate_certificates "$hostname"
                update_env_certificate_paths "$hostname"
                test_certificate_configuration "$hostname"
            else
                echo "⚠️  Certificate extraction from environment failed"
                echo "💡 Use 'copy' command to install certificates from files"
            fi
            ;;
        "extract")
            if [ -z "$hostname" ]; then
                echo "❌ Hostname required"
                show_usage
                exit 1
            fi
            
            validate_hostname "$hostname"
            create_cert_directories "$hostname"
            extract_certificates_from_env "$hostname"
            validate_certificates "$hostname"
            ;;
        "copy")
            if [ -z "$hostname" ] || [ -z "$cert_file" ] || [ -z "$key_file" ]; then
                echo "❌ Hostname, certificate file, and key file required"
                show_usage
                exit 1
            fi
            
            validate_hostname "$hostname"
            create_cert_directories "$hostname"
            copy_certificates_from_files "$hostname" "$cert_file" "$key_file"
            validate_certificates "$hostname"
            update_env_certificate_paths "$hostname"
            ;;
        "validate")
            if [ -z "$hostname" ]; then
                echo "❌ Hostname required"
                show_usage
                exit 1
            fi
            
            validate_certificates "$hostname"
            ;;
        "update-env")
            if [ -z "$hostname" ]; then
                echo "❌ Hostname required"
                show_usage
                exit 1
            fi
            
            update_env_certificate_paths "$hostname"
            ;;
        "test")
            if [ -z "$hostname" ]; then
                echo "❌ Hostname required"
                show_usage
                exit 1
            fi
            
            test_certificate_configuration "$hostname"
            ;;
        "list")
            list_certificates
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"