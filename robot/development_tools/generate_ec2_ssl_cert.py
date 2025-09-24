#!/usr/bin/env python3
"""
EC2 SSL Certificate Generator for Crypto Robot
Generates SSL certificates for AWS EC2 deployment with public IP/domain
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timedelta

def get_ec2_public_ip():
    """Get the public IP address of the current EC2 instance"""
    try:
        # AWS metadata service
        response = requests.get(
            'http://169.254.169.254/latest/meta-data/public-ipv4',
            timeout=5
        )
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    # Fallback: try to get external IP
    try:
        response = requests.get('https://ipinfo.io/ip', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    return None

def create_certs_directory():
    """Create certs directory if it doesn't exist"""
    certs_dir = Path('certs')
    certs_dir.mkdir(exist_ok=True)
    return certs_dir

def generate_openssl_config(public_ip, domain_name=None):
    """Generate OpenSSL configuration file for EC2 certificate"""
    
    # Build alternative names
    alt_names = [
        "IP.1 = 127.0.0.1",
        "IP.2 = ::1",
        f"IP.3 = {public_ip}",
        "DNS.1 = localhost",
    ]
    
    if domain_name:
        alt_names.extend([
            f"DNS.2 = {domain_name}",
            f"DNS.3 = *.{domain_name}",
        ])
    
    # Use domain name as CN if provided, otherwise use IP
    common_name = domain_name if domain_name else public_ip
    
    config_content = f"""
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
OU=Production
CN={common_name}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
{chr(10).join(alt_names)}
"""
    
    config_path = Path('certs/openssl_ec2.conf')
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

def generate_certificate_openssl(public_ip, domain_name=None):
    """Generate SSL certificate using OpenSSL for EC2"""
    certs_dir = create_certs_directory()
    config_path = generate_openssl_config(public_ip, domain_name)
    
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
        
        print("🔐 Generating EC2 SSL certificate with OpenSSL...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ EC2 SSL certificate generated successfully!")
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

def generate_certificate_python(public_ip, domain_name=None):
    """Generate SSL certificate using Python cryptography library for EC2"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import ipaddress
        
        print("🔐 Generating EC2 SSL certificate with Python cryptography...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Use domain name as CN if provided, otherwise use IP
        common_name = domain_name if domain_name else public_ip
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Crypto Robot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Production"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        # Build subject alternative names
        san_list = [
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv6Address("::1")),
            x509.IPAddress(ipaddress.IPv4Address(public_ip)),
            x509.DNSName("localhost"),
        ]
        
        if domain_name:
            san_list.extend([
                x509.DNSName(domain_name),
                x509.DNSName(f"*.{domain_name}"),
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
            x509.SubjectAlternativeName(san_list),
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
        
        print(f"✅ EC2 SSL certificate generated successfully!")
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
    """Main function to generate EC2 SSL certificates"""
    print("🔒 Crypto Robot - EC2 SSL Certificate Generator")
    print("=" * 50)
    
    # Get public IP
    print("🌐 Detecting public IP address...")
    public_ip = get_ec2_public_ip()
    
    if not public_ip:
        print("❌ Could not detect public IP address")
        public_ip = input("Please enter your public IP address: ").strip()
        if not public_ip:
            print("❌ Public IP is required for EC2 certificates")
            sys.exit(1)
    
    print(f"✅ Public IP: {public_ip}")
    
    # Ask for domain name (optional)
    domain_name = input("Enter your domain name (optional, press Enter to skip): ").strip()
    if domain_name:
        print(f"✅ Domain: {domain_name}")
    
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
        success = generate_certificate_openssl(public_ip, domain_name)
    
    if not success:
        print("🔄 Falling back to Python cryptography library...")
        success = generate_certificate_python(public_ip, domain_name)
    
    if success:
        # Verify certificates
        if verify_certificates():
            print("\n🎉 EC2 SSL certificates generated successfully!")
            print("\n📋 Next steps:")
            print("1. Configure your security group to allow HTTPS (port 5000)")
            print("2. Start the HTTPS server:")
            print("   python start_https_server.py")
            print(f"\n3. Access the app:")
            if domain_name:
                print(f"   https://{domain_name}:5000")
            print(f"   https://{public_ip}:5000")
            
            if domain_name:
                print(f"\n💡 Make sure your domain points to {public_ip}")
        else:
            print("\n❌ Certificate verification failed")
            sys.exit(1)
    else:
        print("\n❌ Failed to generate SSL certificates")
        print("💡 Please install OpenSSL or the cryptography Python library")
        sys.exit(1)

if __name__ == '__main__':
    main()