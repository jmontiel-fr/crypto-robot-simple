# Security and Best Practices Guide

## Overview

This document outlines security best practices, certificate management procedures, and operational guidelines for the crypto robot dockerization project. Following these practices ensures secure deployment, operation, and maintenance of the containerized trading robot application.

## Table of Contents

1. [Certificate Management](#certificate-management)
2. [Secrets Management](#secrets-management)
3. [Container Security](#container-security)
4. [Network Security](#network-security)
5. [AWS Security](#aws-security)
6. [CI/CD Security](#cicd-security)
7. [Database Security](#database-security)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Incident Response](#incident-response)
10. [Compliance and Auditing](#compliance-and-auditing)

---

## Certificate Management

### Certificate Generation and Renewal

#### Self-Signed Certificates (Development)
```bash
# Generate self-signed certificate for local development
./tools/generate-certificates.sh crypto-robot.local self-signed

# Certificate validity: 365 days
# Location: certificates/crypto-robot.local/
# Files: cert.pem, key.pem
```

**Security Considerations:**
- Self-signed certificates should ONLY be used in development environments
- Never use self-signed certificates in production
- Regularly regenerate development certificates (recommended: every 90 days)
- Store private keys securely with proper file permissions (600)

#### Let's Encrypt Certificates (Production)
```bash
# Generate Let's Encrypt certificate for production
./tools/generate-certificates.sh jack.crypto-robot-itechsource.com letsencrypt

# Certificate validity: 90 days
# Auto-renewal: Recommended every 60 days
# Location: certificates/jack.crypto-robot-itechsource.com/
```

**Security Best Practices:**
- Implement automated certificate renewal
- Monitor certificate expiration dates
- Use DNS validation for certificate generation when possible
- Store Let's Encrypt account keys securely
- Implement certificate transparency monitoring

#### Certificate Renewal Procedures

**Automated Renewal (Recommended):**
```bash
# Set up cron job for certificate renewal
0 2 * * 0 /path/to/tools/generate-certificates.sh jack.crypto-robot-itechsource.com letsencrypt

# Verify renewal success
0 3 * * 0 /path/to/scripts/verify-certificate.sh jack.crypto-robot-itechsource.com
```

**Manual Renewal Process:**
1. Generate new certificate using the certificate generation script
2. Test certificate validity and configuration
3. Update Docker image with new certificates
4. Deploy updated image to production
5. Verify HTTPS functionality
6. Update monitoring systems with new certificate details

**Certificate Validation:**
```bash
# Verify certificate validity
openssl x509 -in certificates/hostname/cert.pem -text -noout

# Check certificate expiration
openssl x509 -in certificates/hostname/cert.pem -enddate -noout

# Verify certificate chain
openssl verify -CAfile ca-bundle.pem certificates/hostname/cert.pem
```

### Certificate Storage and Access

**File Permissions:**
```bash
# Certificate files
chmod 644 certificates/*/cert.pem
chmod 600 certificates/*/key.pem

# Directory permissions
chmod 755 certificates/
chmod 700 certificates/*/
```

**Docker Image Security:**
- Certificates are embedded in Docker images during build
- Private keys are protected within container filesystem
- Certificate selection is controlled via environment variables
- No certificate files are exposed outside the container

---

## Secrets Management

### GitHub Repository Secrets

#### Required Secrets Configuration
```yaml
# AWS Access (Production)
AWS_ACCESS_KEY_ID: "AKIA..."
AWS_SECRET_ACCESS_KEY: "..."

# DockerHub Registry Access
DOCKERHUB_USERNAME: "jmontiel"
DOCKERHUB_TOKEN: "dckr_pat_..."  # Use Personal Access Token, not password

# SSH Access to EC2 Instances
EC2_SSH_PRIVATE_KEY: |
  -----BEGIN OPENSSH PRIVATE KEY-----
  ...
  -----END OPENSSH PRIVATE KEY-----

# Application Environment Configuration
ENV_AWS: |
  FLASK_PORT=5443
  FLASK_PROTOCOL=https
  BINANCE_API_KEY=...
  BINANCE_SECRET_KEY=...
  DATABASE_PATH=/opt/crypto-robot/database
```

#### Secret Security Best Practices

**Access Control:**
- Limit repository access to essential team members only
- Use principle of least privilege for secret access
- Regularly audit secret access logs
- Implement approval workflows for secret changes

**Secret Rotation:**
- Rotate AWS access keys every 90 days
- Rotate DockerHub tokens every 180 days
- Regenerate SSH keys every 6 months
- Update Binance API keys as required by security policy

**Secret Validation:**
```bash
# Validate AWS credentials
aws sts get-caller-identity

# Test DockerHub access
docker login docker.io -u $DOCKERHUB_USERNAME -p $DOCKERHUB_TOKEN

# Verify SSH key format
ssh-keygen -l -f ~/.ssh/crypto-robot-key.pem
```

### Environment Variable Security

#### .env File Management
```bash
# Production .env file structure
FLASK_PORT=5443
FLASK_PROTOCOL=https
FLASK_HOST=0.0.0.0

# Binance API Configuration (Production)
BINANCE_API_KEY=your_production_api_key
BINANCE_SECRET_KEY=your_production_secret_key
BINANCE_TESTNET=false

# Database Configuration
DATABASE_PATH=/opt/crypto-robot/database
DATABASE_FILE=crypto_robot.db

# Security Configuration
DEBUG=false
SSL_VERIFY=true
```

**Security Requirements:**
- Never commit .env files to version control
- Use different API keys for development and production
- Implement API key rotation procedures
- Monitor API key usage and access patterns
- Use read-only API keys where possible

#### Environment Variable Injection
```bash
# Secure environment variable passing
docker run -d --name crypto-robot \
  -e ENV_CONTENT="$(base64 -w 0 /opt/crypto-robot/.env)" \
  -e CERTIFICATE="jack.crypto-robot-itechsource.com" \
  --restart unless-stopped \
  jmontiel/crypto-robot:latest
```

**Security Considerations:**
- Base64 encoding provides obfuscation, not encryption
- Environment variables are visible in process lists
- Use Docker secrets for highly sensitive data in production
- Implement environment variable validation in application startup

---

## Container Security

### Docker Image Security

#### Base Image Security
```dockerfile
# Use official, minimal base images
FROM python:3.11-slim

# Update packages and remove package manager cache
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r cryptorobot && useradd -r -g cryptorobot cryptorobot
```

#### Container Hardening
```bash
# Run container with security options
docker run -d \
  --name crypto-robot \
  --user cryptorobot \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  --no-new-privileges \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges:true \
  jmontiel/crypto-robot:latest
```

#### Image Scanning
```bash
# Scan Docker image for vulnerabilities
docker scout cves jmontiel/crypto-robot:latest

# Use Trivy for comprehensive scanning
trivy image jmontiel/crypto-robot:latest

# Implement automated scanning in CI/CD
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image jmontiel/crypto-robot:latest
```

### Runtime Security

#### Container Isolation
- Use separate containers for robot and webapp components
- Implement network segmentation between containers
- Use Docker networks for inter-container communication
- Avoid privileged container execution

#### Resource Limits
```bash
# Set resource limits
docker run -d \
  --name crypto-robot \
  --memory=512m \
  --cpus=1.0 \
  --pids-limit=100 \
  jmontiel/crypto-robot:latest
```

#### File System Security
```bash
# Mount database with proper permissions
docker run -d \
  --name crypto-robot \
  -v /opt/crypto-robot/database:/opt/crypto-robot/database:rw \
  --tmpfs /tmp:noexec,nosuid,size=100m \
  jmontiel/crypto-robot:latest
```

---

## Network Security

### AWS Security Groups

#### Inbound Rules Configuration
```yaml
# Security Group: crypto-robot-sg
Inbound Rules:
  - Type: SSH
    Protocol: TCP
    Port: 22
    Source: Your IP ranges only
    Description: SSH access for management
    
  - Type: HTTPS
    Protocol: TCP
    Port: 5443
    Source: 0.0.0.0/0
    Description: HTTPS access for webapp
    
  - Type: Custom TCP
    Protocol: TCP
    Port: 5000
    Source: Your IP ranges only
    Description: HTTP access for development (if needed)
```

#### Outbound Rules Configuration
```yaml
Outbound Rules:
  - Type: HTTPS
    Protocol: TCP
    Port: 443
    Destination: 0.0.0.0/0
    Description: HTTPS for API calls and updates
    
  - Type: HTTP
    Protocol: TCP
    Port: 80
    Destination: 0.0.0.0/0
    Description: HTTP for package updates
    
  - Type: DNS
    Protocol: UDP
    Port: 53
    Destination: 0.0.0.0/0
    Description: DNS resolution
```

### Network Monitoring

#### Traffic Analysis
```bash
# Monitor network connections
netstat -tulpn | grep :5443
ss -tulpn | grep :5000

# Check active connections
lsof -i :5443
lsof -i :5000

# Monitor network traffic
tcpdump -i eth0 port 5443
```

#### Firewall Configuration
```bash
# Configure UFW firewall (if used)
ufw default deny incoming
ufw default allow outgoing
ufw allow from YOUR_IP_RANGE to any port 22
ufw allow 5443/tcp
ufw enable

# Verify firewall status
ufw status verbose
```

### SSL/TLS Security

#### TLS Configuration
```python
# Flask HTTPS configuration
app.run(
    host='0.0.0.0',
    port=5443,
    ssl_context=(cert_file, key_file),
    ssl_version=ssl.PROTOCOL_TLSv1_2,
    ciphers='ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'
)
```

#### Certificate Validation
```bash
# Test SSL configuration
openssl s_client -connect hostname:5443 -servername hostname

# Check SSL certificate details
curl -vI https://hostname:5443/

# Validate certificate chain
openssl verify -CAfile ca-bundle.pem cert.pem
```

---

## AWS Security

### IAM Security

#### Principle of Least Privilege
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:DescribeInstanceStatus"
      ],
      "Resource": "arn:aws:ec2:eu-west-1:*:instance/i-*",
      "Condition": {
        "StringEquals": {
          "ec2:ResourceTag/Project": "crypto-robot"
        }
      }
    }
  ]
}
```

#### Access Key Management
- Use IAM roles instead of access keys when possible
- Implement access key rotation every 90 days
- Monitor access key usage through CloudTrail
- Use temporary credentials for CI/CD workflows

#### Multi-Factor Authentication
- Enable MFA for all IAM users
- Use hardware tokens for production access
- Implement conditional access policies
- Regular MFA device audits

### EC2 Security

#### Instance Hardening
```bash
# Update system packages
sudo yum update -y

# Configure automatic security updates
sudo yum install -y yum-cron
sudo systemctl enable yum-cron
sudo systemctl start yum-cron

# Disable unnecessary services
sudo systemctl disable telnet
sudo systemctl disable rsh
sudo systemctl disable rlogin
```

#### SSH Security
```bash
# SSH configuration (/etc/ssh/sshd_config)
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

#### System Monitoring
```bash
# Install and configure fail2ban
sudo yum install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure log monitoring
sudo yum install -y rsyslog
sudo systemctl enable rsyslog
```

### Data Protection

#### Encryption at Rest
- Use encrypted EBS volumes for EC2 instances
- Enable S3 bucket encryption for Terraform state
- Implement database encryption for sensitive data
- Use AWS KMS for key management

#### Encryption in Transit
- Use HTTPS for all web communications
- Implement TLS for database connections
- Use SSH for secure remote access
- Enable VPC flow logs for network monitoring

---

## CI/CD Security

### GitHub Actions Security

#### Workflow Security
```yaml
# Secure workflow configuration
name: secure-workflow
on:
  workflow_dispatch:
    # Limit manual triggers to specific users
  push:
    branches: [main]
    # Only trigger on main branch

permissions:
  contents: read
  id-token: write  # For OIDC authentication

jobs:
  secure-job:
    runs-on: ubuntu-latest
    environment: production  # Require environment approval
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          # Use minimal permissions token
```

#### Secret Security in Workflows
- Use environment-specific secrets
- Implement secret scanning in repositories
- Avoid logging sensitive information
- Use OIDC for AWS authentication when possible

#### Artifact Security
```yaml
# Secure artifact handling
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: secure-artifacts
    path: artifacts/
    retention-days: 7  # Minimize retention period
    if-no-files-found: error
```

### Supply Chain Security

#### Dependency Management
```bash
# Scan dependencies for vulnerabilities
pip audit
safety check

# Use dependency pinning
pip freeze > requirements.txt

# Implement automated dependency updates
dependabot.yml configuration
```

#### Container Registry Security
- Use private registries for sensitive images
- Implement image signing and verification
- Scan images before deployment
- Use minimal base images

---

## Database Security

### SQLite3 Security

#### File Permissions
```bash
# Set proper database file permissions
chmod 600 /opt/crypto-robot/database/crypto_robot.db
chown cryptorobot:cryptorobot /opt/crypto-robot/database/

# Verify permissions
ls -la /opt/crypto-robot/database/
```

#### Database Encryption
```python
# Implement database encryption (if required)
import sqlite3
from cryptography.fernet import Fernet

# Generate encryption key
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Encrypt sensitive data before storage
encrypted_data = cipher_suite.encrypt(sensitive_data.encode())
```

#### Backup Security
```bash
# Secure database backup
sqlite3 /opt/crypto-robot/database/crypto_robot.db ".backup backup.db"
gpg --symmetric --cipher-algo AES256 backup.db
rm backup.db

# Automated backup with encryption
#!/bin/bash
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).db"
sqlite3 /opt/crypto-robot/database/crypto_robot.db ".backup $BACKUP_FILE"
gpg --batch --yes --passphrase-file /secure/passphrase.txt \
    --symmetric --cipher-algo AES256 "$BACKUP_FILE"
rm "$BACKUP_FILE"
```

### Data Access Control

#### Application-Level Security
```python
# Implement parameterized queries
cursor.execute("SELECT * FROM trades WHERE user_id = ?", (user_id,))

# Input validation
def validate_trade_data(data):
    if not isinstance(data.get('amount'), (int, float)):
        raise ValueError("Invalid amount")
    if data.get('amount') <= 0:
        raise ValueError("Amount must be positive")
```

#### Audit Logging
```python
# Implement database audit logging
def log_database_operation(operation, table, user_id, timestamp):
    audit_cursor.execute(
        "INSERT INTO audit_log (operation, table_name, user_id, timestamp) VALUES (?, ?, ?, ?)",
        (operation, table, user_id, timestamp)
    )
```

---

## Monitoring and Logging

### Application Monitoring

#### Health Check Endpoints
```python
# Implement health check endpoint
@app.route('/health')
def health_check():
    try:
        # Check database connectivity
        db_status = check_database_connection()
        
        # Check external API connectivity
        api_status = check_binance_api()
        
        if db_status and api_status:
            return jsonify({"status": "healthy"}), 200
        else:
            return jsonify({"status": "unhealthy"}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

#### Performance Monitoring
```python
# Implement performance metrics
import time
import logging

def monitor_trade_execution(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logging.info(f"Trade executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"Trade failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper
```

### Security Monitoring

#### Log Analysis
```bash
# Monitor authentication attempts
grep "Failed password" /var/log/auth.log

# Monitor Docker container logs
docker logs crypto-robot | grep -i error
docker logs crypto-robot | grep -i security

# Monitor application logs
tail -f /opt/crypto-robot/logs/application.log | grep -i "unauthorized\|failed\|error"
```

#### Intrusion Detection
```bash
# Install and configure AIDE
sudo yum install -y aide
sudo aide --init
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Run integrity check
sudo aide --check
```

#### Automated Alerting
```bash
# Configure log monitoring with alerts
# /etc/rsyslog.d/crypto-robot.conf
if $programname == 'crypto-robot' and $msg contains 'SECURITY' then {
    action(type="ommail"
           server="smtp.example.com"
           port="587"
           mailfrom="alerts@example.com"
           mailto="security@example.com"
           subject="Security Alert: Crypto Robot")
}
```

### Compliance Monitoring

#### Audit Trail
```python
# Implement comprehensive audit logging
class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('audit')
        
    def log_trade(self, user_id, action, symbol, amount, price):
        self.logger.info({
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'ip_address': request.remote_addr
        })
```

#### Compliance Reporting
```bash
# Generate compliance reports
#!/bin/bash
# compliance-report.sh

echo "Crypto Robot Security Compliance Report"
echo "Generated: $(date)"
echo "=================================="

echo "1. Certificate Status:"
openssl x509 -in /opt/crypto-robot/certificates/*/cert.pem -enddate -noout

echo "2. System Updates:"
yum list updates

echo "3. Failed Login Attempts:"
grep "Failed password" /var/log/auth.log | tail -10

echo "4. Container Security:"
docker scout cves jmontiel/crypto-robot:latest
```

---

## Incident Response

### Security Incident Response Plan

#### Incident Classification
1. **Critical**: Unauthorized access, data breach, system compromise
2. **High**: Failed authentication attempts, suspicious network activity
3. **Medium**: Configuration drift, certificate expiration warnings
4. **Low**: Performance degradation, non-security related errors

#### Response Procedures

**Immediate Response (0-15 minutes):**
1. Identify and isolate affected systems
2. Preserve evidence and logs
3. Notify security team
4. Document incident timeline

**Short-term Response (15 minutes - 4 hours):**
1. Contain the incident
2. Assess impact and scope
3. Implement temporary mitigations
4. Communicate with stakeholders

**Long-term Response (4+ hours):**
1. Implement permanent fixes
2. Conduct root cause analysis
3. Update security procedures
4. Provide incident report

#### Emergency Procedures

**System Compromise Response:**
```bash
# Immediate isolation
sudo iptables -A INPUT -j DROP
sudo iptables -A OUTPUT -j DROP

# Stop all services
docker stop $(docker ps -q)
sudo systemctl stop sshd

# Preserve evidence
sudo dd if=/dev/sda of=/backup/forensic-image.dd bs=4096
sudo tar -czf /backup/logs-$(date +%Y%m%d).tar.gz /var/log/
```

**Data Breach Response:**
1. Immediately revoke all API keys
2. Change all passwords and SSH keys
3. Notify relevant authorities within 72 hours
4. Implement additional monitoring
5. Conduct security audit

### Recovery Procedures

#### System Recovery
```bash
# Restore from clean backup
docker pull jmontiel/crypto-robot:latest
docker run --name crypto-robot-recovery \
  -e ENV_CONTENT="$(base64 /backup/clean.env)" \
  jmontiel/crypto-robot:latest

# Restore database from backup
gpg --decrypt backup_encrypted.db.gpg > restored.db
sqlite3 restored.db ".backup /opt/crypto-robot/database/crypto_robot.db"
```

#### Post-Incident Actions
1. Update security procedures based on lessons learned
2. Implement additional monitoring and alerting
3. Conduct security training for team members
4. Review and update incident response plan
5. Perform security audit and penetration testing

---

## Compliance and Auditing

### Security Auditing

#### Regular Security Assessments
- Monthly vulnerability scans
- Quarterly penetration testing
- Annual security architecture review
- Continuous compliance monitoring

#### Audit Checklist
```markdown
## Monthly Security Audit Checklist

### Infrastructure Security
- [ ] EC2 instances have latest security patches
- [ ] Security groups follow least privilege principle
- [ ] SSH keys are rotated and secure
- [ ] SSL certificates are valid and not expiring soon

### Application Security
- [ ] Docker images scanned for vulnerabilities
- [ ] Dependencies updated and scanned
- [ ] Application logs reviewed for security events
- [ ] Database backups tested and encrypted

### Access Control
- [ ] User access reviewed and updated
- [ ] API keys rotated according to schedule
- [ ] GitHub repository access audited
- [ ] AWS IAM permissions reviewed

### Monitoring and Alerting
- [ ] Security monitoring systems operational
- [ ] Alert thresholds appropriate and tested
- [ ] Incident response procedures updated
- [ ] Compliance reports generated and reviewed
```

### Documentation Requirements

#### Security Documentation
- Security architecture diagrams
- Risk assessment and mitigation strategies
- Incident response procedures
- Security training materials
- Compliance certification documents

#### Change Management
- All security-related changes must be documented
- Security impact assessments for major changes
- Approval process for security configuration changes
- Rollback procedures for security updates

### Regulatory Compliance

#### Data Protection
- Implement data classification scheme
- Ensure data retention policies are followed
- Maintain data processing records
- Implement data subject rights procedures

#### Financial Regulations
- Maintain audit trails for all trading activities
- Implement transaction monitoring
- Ensure proper record keeping
- Comply with anti-money laundering requirements

---

## Conclusion

This security and best practices guide provides comprehensive coverage of security considerations for the crypto robot dockerization project. Regular review and updates of these practices are essential to maintain a strong security posture.

### Key Takeaways

1. **Defense in Depth**: Implement multiple layers of security controls
2. **Principle of Least Privilege**: Grant minimal necessary permissions
3. **Regular Updates**: Keep all systems and dependencies updated
4. **Monitoring**: Implement comprehensive logging and monitoring
5. **Incident Response**: Maintain and test incident response procedures
6. **Compliance**: Ensure ongoing compliance with relevant regulations

### Next Steps

1. Implement automated security scanning in CI/CD pipelines
2. Set up comprehensive monitoring and alerting
3. Conduct regular security training for team members
4. Perform periodic security assessments and penetration testing
5. Review and update security procedures quarterly

For questions or clarifications regarding these security practices, consult with the security team or refer to the detailed implementation guides in the project documentation.