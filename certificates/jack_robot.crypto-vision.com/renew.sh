#!/bin/bash
# Let's Encrypt-style renewal script for jack_robot.crypto-vision.com
# For production, replace this with actual certbot renewal

echo "Renewing certificate for jack_robot.crypto-vision.com..."
cd "$(dirname "$0")"

# Backup existing certificate
cp cert.pem cert.pem.backup.$(date +%Y%m%d_%H%M%S)

# Generate new certificate (90 days)
openssl x509 -req -in cert.csr -signkey key.pem -out cert.pem -days 90 -extensions v3_req -extfile openssl.conf

echo "Certificate renewed for jack_robot.crypto-vision.com"
echo "Valid until: $(openssl x509 -enddate -noout -in cert.pem | cut -d= -f2)"
