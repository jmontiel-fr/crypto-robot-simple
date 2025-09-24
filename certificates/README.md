# Certificate Management for Crypto Robot

This directory contains SSL/TLS certificates for the Crypto Robot application, organized by hostname for easy management and deployment flexibility.

## Directory Structure

```
certificates/
├── crypto-robot.local/           # Local development certificates
│   ├── cert.pem                  # SSL certificate (self-signed)
│   └── key.pem                   # Private key
├── jack_robot.crypto-vision.com/ # Jack's production certificates
│   ├── cert.pem                  # SSL certificate (Let's Encrypt style)
│   ├── key.pem                   # Private key
│   ├── renew.sh                  # Renewal script
│   └── openssl.conf              # OpenSSL configuration
├── its_robot.crypto-vision.com/  # ITS production certificates
│   ├── cert.pem                  # SSL certificate (Let's Encrypt style)
│   ├── key.pem                   # Private key
│   ├── renew.sh                  # Renewal script
│   └── openssl.conf              # OpenSSL configuration
└── <custom>_robot.crypto-vision.com/  # Additional custom certificates
    ├── cert.pem
    ├── key.pem
    ├── renew.sh                  # Renewal script
    └── openssl.conf              # OpenSSL configuration
```

## Certificate Generation

Use the `tools/generate-certificates.sh` script to generate certificates for any hostname:

### Self-Signed Certificates (Development)

```bash
# Generate self-signed certificate for local development
./tools/generate-certificates.sh crypto-robot.local self-signed

# Generate self-signed certificate for testing
./tools/generate-certificates.sh my-test.crypto-robot.com self-signed
```

### Let's Encrypt Certificates (Production)

```bash
# Generate Let's Encrypt certificate for Jack's production
./tools/generate-certificates.sh jack_robot.crypto-vision.com letsencrypt

# Generate Let's Encrypt certificate for ITS production
./tools/generate-certificates.sh its_robot.crypto-vision.com letsencrypt

# Generate Let's Encrypt certificate for custom domain
./tools/generate-certificates.sh custom_robot.crypto-vision.com letsencrypt
```

**Note:** Let's Encrypt certificates require:
- The domain to be publicly accessible
- Proper DNS configuration pointing to your server
- HTTP (port 80) access for domain validation
- Root privileges (run with `sudo`)

## Certificate Usage

### Flask Application Integration

The certificates are designed to work seamlessly with the Flask HTTPS server. The application will automatically select certificates based on the hostname configuration:

```python
# Example Flask HTTPS server configuration
import ssl
from flask import Flask

app = Flask(__name__)

# Certificate selection based on hostname
hostname = "crypto-robot.local"  # or from environment variable
cert_file = f"certificates/{hostname}/cert.pem"
key_file = f"certificates/{hostname}/key.pem"

# Create SSL context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(cert_file, key_file)

# Run Flask with HTTPS
app.run(host='0.0.0.0', port=5443, ssl_context=context)
```

### Docker Container Usage

In Docker containers, certificates are selected using the `CERTIFICATE` environment variable:

```bash
# Local development
docker run -e CERTIFICATE="crypto-robot.local" crypto-robot

# Jack's production deployment
docker run -e CERTIFICATE="jack_robot.crypto-vision.com" crypto-robot

# ITS production deployment
docker run -e CERTIFICATE="its_robot.crypto-vision.com" crypto-robot

# Custom deployment
docker run -e CERTIFICATE="custom_robot.crypto-vision.com" crypto-robot
```

## Certificate Validation

All generated certificates include:
- **Subject Alternative Names (SAN)** for the target hostname, localhost, and 127.0.0.1
- **Extended Key Usage** for server authentication
- **Key Usage** for key encipherment and data encipherment
- **2048-bit RSA keys** for security

### Self-Signed Certificates
- Valid for 10 years (3650 days)
- Suitable for development and testing
- Will show browser warnings (expected behavior)
- Long duration eliminates renewal concerns for development

### Let's Encrypt Certificates
- Valid for 90 days (maximum duration allowed by Let's Encrypt)
- Automatically renewable using the generated renewal script
- Trusted by all major browsers
- Require public domain validation

## Certificate Renewal

### Let's Encrypt Renewal

For Let's Encrypt certificates, use the generated renewal script:

```bash
# Manual renewal for Jack's environment
./certificates/jack_robot.crypto-vision.com/renew.sh

# Manual renewal for ITS environment
./certificates/its_robot.crypto-vision.com/renew.sh

# Automated renewal (add to crontab)
0 2 * * 0 /path/to/certificates/jack_robot.crypto-vision.com/renew.sh
0 2 * * 0 /path/to/certificates/its_robot.crypto-vision.com/renew.sh
```

### Self-Signed Renewal

For self-signed certificates, regenerate using the same command:

```bash
./tools/generate-certificates.sh crypto-robot.local self-signed
```

## Security Considerations

1. **Private Key Protection**: Private keys (key.pem) have restricted permissions (600)
2. **Certificate Storage**: Store certificates securely and avoid committing private keys to version control
3. **Regular Renewal**: Monitor certificate expiration and renew before expiry
4. **Backup**: Keep secure backups of production certificates and private keys

## Troubleshooting

### Common Issues

1. **Let's Encrypt Rate Limiting**
   - Let's Encrypt has rate limits (5 certificates per domain per week)
   - Use staging environment for testing: `--staging` flag with certbot

2. **Domain Validation Failures**
   - Ensure domain points to your server's public IP
   - Check firewall allows HTTP (port 80) access
   - Verify web server serves challenge files from webroot

3. **Permission Errors**
   - Let's Encrypt requires root privileges
   - Ensure proper file permissions on certificate files

4. **Certificate Validation Errors**
   - Check certificate validity: `openssl x509 -in cert.pem -text -noout`
   - Verify hostname matches: `openssl x509 -in cert.pem -noout -subject`

### Testing Certificates

```bash
# Test certificate validity
openssl x509 -in certificates/crypto-robot.local/cert.pem -text -noout

# Test certificate and key match
openssl x509 -noout -modulus -in certificates/crypto-robot.local/cert.pem | openssl md5
openssl rsa -noout -modulus -in certificates/crypto-robot.local/key.pem | openssl md5

# Test HTTPS connection
openssl s_client -connect crypto-robot.local:5443 -servername crypto-robot.local
```

## Generated Certificates

The following certificates have been pre-generated for immediate use:

- **crypto-robot.local**: Self-signed certificate for local development (10 years validity)
- **jack_robot.crypto-vision.com**: Let's Encrypt-style certificate for Jack's production (90 days validity)
- **its_robot.crypto-vision.com**: Let's Encrypt-style certificate for ITS production (90 days validity)

### Production Certificate Notes

The production certificates (jack_robot.crypto-vision.com and its_robot.crypto-vision.com) are currently Let's Encrypt-style development certificates. For actual production deployment:

1. **Replace with real Let's Encrypt certificates** using certbot on your production server
2. **Use the renewal scripts** to maintain certificate validity
3. **Monitor expiration dates** - Let's Encrypt certificates expire every 90 days

### Generating Real Let's Encrypt Certificates

On your production server with certbot installed:

```bash
# Install certbot (Ubuntu/Debian)
sudo apt-get install certbot

# Generate real Let's Encrypt certificate
sudo certbot certonly --standalone -d jack_robot.crypto-vision.com
sudo certbot certonly --standalone -d its_robot.crypto-vision.com

# Copy certificates to your application
sudo cp /etc/letsencrypt/live/jack_robot.crypto-vision.com/fullchain.pem certificates/jack_robot.crypto-vision.com/cert.pem
sudo cp /etc/letsencrypt/live/jack_robot.crypto-vision.com/privkey.pem certificates/jack_robot.crypto-vision.com/key.pem
```

Additional certificates can be generated as needed using the certificate generation script.