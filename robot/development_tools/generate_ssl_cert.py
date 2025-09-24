#!/usr/bin/env python3
"""
SSL Certificate Generator for Crypto Robot HTTPS Server
Generates self-signed SSL certificates for local development
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def create_certs_directory():
    """Create certs directory if it doesn't exist"""
    certs_dir = Path('certs')
    certs_dir.mkdir(exist_ok=True)
    return certs_dir

def generate_openssl_config():
    """Generate OpenSSL configuration file for certificate"""
    config_content = """
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=CA
L=San Francisco
O=Crypto Robot
OU=Development
CN=crypto-robot.local

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = crypto-robot.local
DNS.2 = localhost
DNS.3 = *.crypto-robot.local
IP.1 = 127.0.0.1
IP.2 = ::1
"""
    
    config_path = Path('certs/openssl.conf')
    with open(config_path, 'w') as f:
        f.write(config_content.strip())
    
    return config_path

def check_openssl():
    """Check if OpenSSL is available"""
    try:
        result = subprocess.run(['openssl', 'version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ OpenSSL found: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def generate_certificate_openssl():
    """Generate SSL certificate using OpenSSL"""
    certs_dir = create_certs_directory()
    config_path = generate_openssl_config()
    
    cert_path = certs_dir / 'cert.pem'
    key_path = certs_dir / 'key.pem'
    
    try:
        # Generate private key and certificate in one command
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', str(key_path),
            '-out', str(cert_path),
            '-days', '365',
            '-nodes',  # No password
            '-config', str(config_path)
        ]
        
        print("🔐 Generating SSL certificate with OpenSSL...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SSL certificate generated successfully!")
            print(f"📄 Certificate: {cert_path}")
            print(f"🔑 Private key: {key_path}")
            
            # Clean up config file
            config_path.unlink()
            
            return True
        else:
            print(f"❌ OpenSSL error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating certificate: {e}")
        return False

def generate_certificate_python():
    """Generate SSL certificate using Python cryptography library"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import ipaddress
        
        print("🔐 Generating SSL certificate with Python cryptography...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Crypto Robot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "crypto-robot.local"),
        ])
        
        # Certificate valid for 1 year
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("crypto-robot.local"),
                x509.DNSName("localhost"),
                x509.DNSName("*.crypto-robot.local"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Create certs directory
        certs_dir = create_certs_directory()
        
        # Write certificate
        cert_path = certs_dir / 'cert.pem'
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        key_path = certs_dir / 'key.pem'
        with open(key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✅ SSL certificate generated successfully!")
        print(f"📄 Certificate: {cert_path}")
        print(f"🔑 Private key: {key_path}")
        
        return True
        
    except ImportError:
        print("❌ Python cryptography library not found")
        print("💡 Install with: pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ Error generating certificate: {e}")
        return False

def verify_certificates():
    """Verify that certificates were created and are valid"""
    cert_path = Path('certs/cert.pem')
    key_path = Path('certs/key.pem')
    
    if not cert_path.exists() or not key_path.exists():
        return False
    
    try:
        # Try to read the certificate
        with open(cert_path, 'r') as f:
            cert_content = f.read()
            if 'BEGIN CERTIFICATE' in cert_content and 'END CERTIFICATE' in cert_content:
                print("✅ Certificate file is valid")
            else:
                print("❌ Certificate file appears corrupted")
                return False
        
        # Try to read the private key
        with open(key_path, 'r') as f:
            key_content = f.read()
            if 'BEGIN PRIVATE KEY' in key_content and 'END PRIVATE KEY' in key_content:
                print("✅ Private key file is valid")
            else:
                print("❌ Private key file appears corrupted")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying certificates: {e}")
        return False

def main():
    """Main function to generate SSL certificates"""
    print("🔒 Crypto Robot - SSL Certificate Generator")
    print("=" * 45)
    
    # Check if certificates already exist
    cert_path = Path('certs/cert.pem')
    key_path = Path('certs/key.pem')
    
    if cert_path.exists() and key_path.exists():
        print("⚠️  SSL certificates already exist!")
        response = input("Do you want to regenerate them? (y/N): ").lower()
        if response != 'y':
            print("🔄 Keeping existing certificates")
            return
    
    # Try OpenSSL first, then fall back to Python
    success = False
    
    if check_openssl():
        success = generate_certificate_openssl()
    
    if not success:
        print("🔄 Falling back to Python cryptography library...")
        success = generate_certificate_python()
    
    if success:
        # Verify certificates
        if verify_certificates():
            print("\n🎉 SSL certificates generated successfully!")
            print("\n📋 Next steps:")
            print("1. Add to your hosts file:")
            print("   127.0.0.1 crypto-robot.local")
            print("\n2. Start the HTTPS server:")
            print("   python start_https_server.py")
            print("\n3. Access the app:")
            print("   https://crypto-robot.local:5000")
        else:
            print("\n❌ Certificate verification failed")
            sys.exit(1)
    else:
        print("\n❌ Failed to generate SSL certificates")
        print("💡 Please install OpenSSL or the cryptography Python library")
        sys.exit(1)

if __name__ == '__main__':
    main()