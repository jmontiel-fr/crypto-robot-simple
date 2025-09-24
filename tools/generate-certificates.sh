#!/bin/bash

# Certificate Generation Script for Crypto Robot
# Usage: ./tools/generate-certificates.sh <hostname> <type>
# hostname: target hostname (e.g., crypto-robot.local, jack.crypto-robot-itechsource.com)
# type: self-signed or letsencrypt

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display usage
usage() {
    echo "Usage: $0 <hostname> <type>"
    echo ""
    echo "Parameters:"
    echo "  hostname    Target hostname (e.g., crypto-robot.local, jack_robot.crypto-vision.com)"
    echo "  type        Certificate type: 'self-signed' or 'letsencrypt'"
    echo ""
    echo "Examples:"
    echo "  $0 crypto-robot.local self-signed"
    echo "  $0 jack_robot.crypto-vision.com letsencrypt"
    echo "  $0 its_robot.crypto-vision.com letsencrypt"
    echo "  $0 custom_robot.crypto-vision.com letsencrypt"
    exit 1
}

# Check if required parameters are provided
if [ $# -ne 2 ]; then
    print_error "Invalid number of arguments"
    usage
fi

HOSTNAME="$1"
CERT_TYPE="$2"

# Validate certificate type
if [ "$CERT_TYPE" != "self-signed" ] && [ "$CERT_TYPE" != "letsencrypt" ]; then
    print_error "Invalid certificate type. Must be 'self-signed' or 'letsencrypt'"
    usage
fi

# Validate hostname format (basic validation - allow underscores for crypto-vision.com pattern)
if [[ ! "$HOSTNAME" =~ ^[a-zA-Z0-9._-]+$ ]]; then
    print_error "Invalid hostname format: $HOSTNAME"
    exit 1
fi

# Create certificates directory structure
CERT_DIR="certificates/$HOSTNAME"
mkdir -p "$CERT_DIR"

print_info "Generating $CERT_TYPE certificate for hostname: $HOSTNAME"
print_info "Certificate directory: $CERT_DIR"

# Function to generate self-signed certificate
generate_self_signed() {
    local hostname="$1"
    local cert_dir="$2"
    
    print_info "Generating self-signed certificate using OpenSSL..."
    
    # Create OpenSSL configuration file
    cat > "$cert_dir/openssl.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Crypto Robot
OU = Development
CN = $hostname

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $hostname
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

    # Generate private key
    openssl genrsa -out "$cert_dir/key.pem" 2048
    
    # Generate certificate signing request
    openssl req -new -key "$cert_dir/key.pem" -out "$cert_dir/cert.csr" -config "$cert_dir/openssl.conf"
    
    # Generate self-signed certificate (valid for 10 years = 3650 days)
    openssl x509 -req -in "$cert_dir/cert.csr" -signkey "$cert_dir/key.pem" -out "$cert_dir/cert.pem" -days 3650 -extensions v3_req -extfile "$cert_dir/openssl.conf"
    
    # Clean up temporary files
    rm "$cert_dir/cert.csr" "$cert_dir/openssl.conf"
    
    # Set proper permissions
    chmod 600 "$cert_dir/key.pem"
    chmod 644 "$cert_dir/cert.pem"
    
    print_info "Self-signed certificate generated successfully!"
    print_info "Certificate: $cert_dir/cert.pem"
    print_info "Private key: $cert_dir/key.pem"
    print_info "Valid for: 10 years (3650 days)"
}

# Function to generate Let's Encrypt-style certificate (for development)
generate_letsencrypt_style() {
    local hostname="$1"
    local cert_dir="$2"
    
    print_info "Generating Let's Encrypt-style certificate using OpenSSL..."
    
    # Create OpenSSL configuration file for production-like certificate
    cat > "$cert_dir/openssl.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Crypto Vision
OU = Production
CN = $hostname

[v3_req]
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
basicConstraints = CA:FALSE

[alt_names]
DNS.1 = $hostname
EOF

    # Generate private key (2048-bit RSA like Let's Encrypt)
    openssl genrsa -out "$cert_dir/key.pem" 2048
    
    # Generate certificate signing request
    openssl req -new -key "$cert_dir/key.pem" -out "$cert_dir/cert.csr" -config "$cert_dir/openssl.conf"
    
    # Generate certificate (90 days like Let's Encrypt)
    openssl x509 -req -in "$cert_dir/cert.csr" -signkey "$cert_dir/key.pem" -out "$cert_dir/cert.pem" -days 90 -extensions v3_req -extfile "$cert_dir/openssl.conf"
    
    # Create renewal script
    cat > "$cert_dir/renew.sh" << EOF
#!/bin/bash
# Let's Encrypt-style renewal script for $hostname
# For production, replace this with actual certbot renewal

echo "Renewing certificate for $hostname..."
cd "\$(dirname "\$0")"

# Backup existing certificate
cp cert.pem cert.pem.backup.\$(date +%Y%m%d_%H%M%S)

# Generate new certificate (90 days)
openssl x509 -req -in cert.csr -signkey key.pem -out cert.pem -days 90 -extensions v3_req -extfile openssl.conf

echo "Certificate renewed for $hostname"
echo "Valid until: \$(openssl x509 -enddate -noout -in cert.pem | cut -d= -f2)"
EOF
    
    chmod +x "$cert_dir/renew.sh"
    
    # Clean up temporary files
    rm "$cert_dir/cert.csr"
    
    # Set proper permissions
    chmod 600 "$cert_dir/key.pem"
    chmod 644 "$cert_dir/cert.pem"
    
    print_info "Let's Encrypt-style certificate generated successfully!"
    print_info "Certificate: $cert_dir/cert.pem"
    print_info "Private key: $cert_dir/key.pem"
    print_info "Renewal script: $cert_dir/renew.sh"
    print_info "Valid for: 90 days (Let's Encrypt style)"
    print_warning "This is a development certificate - replace with actual Let's Encrypt in production"
}

# Function to generate Let's Encrypt certificate
generate_letsencrypt() {
    local hostname="$1"
    local cert_dir="$2"
    
    print_info "Generating Let's Encrypt-style certificate..."
    print_warning "This creates a development certificate that mimics Let's Encrypt format"
    print_warning "For production, replace with actual Let's Encrypt certificates"
    
    # Check if certbot is installed for actual Let's Encrypt generation
    if command -v certbot &> /dev/null; then
        print_info "Certbot detected - generating actual Let's Encrypt certificate..."
        generate_actual_letsencrypt "$hostname" "$cert_dir"
        return
    fi
    
    print_info "Certbot not found - generating Let's Encrypt-style development certificate..."
    generate_letsencrypt_style "$hostname" "$cert_dir"
}

# Function to generate actual Let's Encrypt certificate using certbot
generate_actual_letsencrypt() {
    local hostname="$1"
    local cert_dir="$2"
    
    # Check if running as root (required for certbot)
    if [ "$EUID" -ne 0 ]; then
        print_warning "Let's Encrypt certificate generation typically requires root privileges"
        print_warning "You may need to run this script with sudo for Let's Encrypt certificates"
    fi
    
    # Create webroot directory for HTTP challenge
    WEBROOT_DIR="/tmp/letsencrypt-webroot"
    mkdir -p "$WEBROOT_DIR"
    
    print_info "Using webroot authentication method"
    print_info "Webroot directory: $WEBROOT_DIR"
    print_warning "Make sure your web server serves files from $WEBROOT_DIR/.well-known/acme-challenge/"
    print_warning "The domain $hostname must be publicly accessible and point to this server"
    
    # Generate Let's Encrypt certificate
    if certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT_DIR" \
        --email "admin@$hostname" \
        --agree-tos \
        --no-eff-email \
        --domains "$hostname" \
        --non-interactive; then
        
        # Copy certificates to our directory structure
        LETSENCRYPT_DIR="/etc/letsencrypt/live/$hostname"
        
        if [ -d "$LETSENCRYPT_DIR" ]; then
            cp "$LETSENCRYPT_DIR/fullchain.pem" "$cert_dir/cert.pem"
            cp "$LETSENCRYPT_DIR/privkey.pem" "$cert_dir/key.pem"
            
            # Set proper permissions
            chmod 600 "$cert_dir/key.pem"
            chmod 644 "$cert_dir/cert.pem"
            
            print_info "Let's Encrypt certificate generated successfully!"
            print_info "Certificate: $cert_dir/cert.pem"
            print_info "Private key: $cert_dir/key.pem"
            print_info "Valid for: 90 days (maximum duration for Let's Encrypt, auto-renewable)"
            
            # Create renewal script
            cat > "$cert_dir/renew.sh" << EOF
#!/bin/bash
# Certificate renewal script for $hostname
certbot renew --webroot --webroot-path="$WEBROOT_DIR"
cp "/etc/letsencrypt/live/$hostname/fullchain.pem" "$cert_dir/cert.pem"
cp "/etc/letsencrypt/live/$hostname/privkey.pem" "$cert_dir/key.pem"
chmod 600 "$cert_dir/key.pem"
chmod 644 "$cert_dir/cert.pem"
echo "Certificate renewed for $hostname"
EOF
            chmod +x "$cert_dir/renew.sh"
            print_info "Renewal script created: $cert_dir/renew.sh"
        else
            print_error "Let's Encrypt certificate directory not found: $LETSENCRYPT_DIR"
            exit 1
        fi
    else
        print_error "Failed to generate Let's Encrypt certificate"
        print_info "Common issues:"
        print_info "1. Domain $hostname is not publicly accessible"
        print_info "2. DNS records are not properly configured"
        print_info "3. Firewall is blocking HTTP (port 80) access"
        print_info "4. Web server is not serving the challenge files"
        exit 1
    fi
    
    # Clean up webroot directory
    rm -rf "$WEBROOT_DIR"
}

# Function to validate generated certificates
validate_certificate() {
    local cert_file="$1"
    local hostname="$2"
    
    print_info "Validating generated certificate..."
    
    if [ ! -f "$cert_file" ]; then
        print_error "Certificate file not found: $cert_file"
        return 1
    fi
    
    # Check certificate validity
    if openssl x509 -in "$cert_file" -text -noout > /dev/null 2>&1; then
        print_info "Certificate is valid"
        
        # Display certificate information
        echo ""
        print_info "Certificate Information:"
        echo "Subject: $(openssl x509 -in "$cert_file" -subject -noout | sed 's/subject=//')"
        echo "Issuer: $(openssl x509 -in "$cert_file" -issuer -noout | sed 's/issuer=//')"
        echo "Valid from: $(openssl x509 -in "$cert_file" -startdate -noout | sed 's/notBefore=//')"
        echo "Valid until: $(openssl x509 -in "$cert_file" -enddate -noout | sed 's/notAfter=//')"
        
        # Check if certificate matches hostname
        if openssl x509 -in "$cert_file" -text -noout | grep -q "$hostname"; then
            print_info "Certificate matches hostname: $hostname"
        else
            print_warning "Certificate may not match hostname: $hostname"
        fi
        
        return 0
    else
        print_error "Certificate is invalid or corrupted"
        return 1
    fi
}

# Main execution
case "$CERT_TYPE" in
    "self-signed")
        generate_self_signed "$HOSTNAME" "$CERT_DIR"
        ;;
    "letsencrypt")
        generate_letsencrypt "$HOSTNAME" "$CERT_DIR"
        ;;
esac

# Validate the generated certificate
if validate_certificate "$CERT_DIR/cert.pem" "$HOSTNAME"; then
    print_info "Certificate generation completed successfully!"
    echo ""
    print_info "Files created:"
    echo "  - Certificate: $CERT_DIR/cert.pem"
    echo "  - Private Key: $CERT_DIR/key.pem"
    if [ "$CERT_TYPE" = "letsencrypt" ] && [ -f "$CERT_DIR/renew.sh" ]; then
        echo "  - Renewal Script: $CERT_DIR/renew.sh"
    fi
    echo ""
    print_info "You can now use these certificates with your Flask HTTPS server"
else
    print_error "Certificate validation failed"
    exit 1
fi