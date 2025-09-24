# Security Best Practices Guide

## Overview

This guide provides comprehensive security guidelines for the crypto trading robot application, covering certificate management, secrets handling, container security, and operational best practices.

## Certificate Management and Security

### Certificate Generation Security

#### Self-Signed Certificates (Development)

```bash
# Generate secure self-signed certificates
./tools/generate-certificates.sh crypto-robot.local self-signed

# Security considerations:
# - Use strong key lengths (2048-bit RSA minimum, 4096-bit recommended)
# - Set appropriate certificate validity periods (1 year maximum)
# - Use secure random number generation
# - Protect private keys with proper file permissions
```

**Security Best Practices**:
- Never use self-signed certificates in production
- Rotate self-signed certificates regularly (every 6-12 months)
- Store private keys with restricted permissions (600)
- Use different certificates for different environments

#### Let's Encrypt Certificates (Production)

```bash
# Generate production certificates
./tools/generate-certificates.sh jack.crypto-robot-itechsource.com letsencrypt

# Security considerations:
# - Certificates are publicly logged in Certificate Transparency logs
# - Automatic renewal prevents expiration-related outages
# - Rate limits apply (5 certificates per week per domain)
# - Domain validation required
```

**Security Best Practices**:
- Enable automatic certificate renewal
- Monitor certificate expiration dates
- Use DNS validation when possible (more secure than HTTP validation)
- Implement certificate pinning for critical applications
- Monitor Certificate Transparency logs for unauthorized certificates

### Certificate Storage and Access

#### File System Security

```bash
# Secure certificate storage
chmod 600 certificates/*/key.pem    # Private keys: owner read/write only
chmod 644 certificates/*/cert.pem   # Certificates: owner read/write, others read
chown root:root certificates/       # Root ownership
```

#### Docker Container Security

```bash
# Secure certificate handling in containers
# Certificates are copied into image at build time
# Runtime certificate selection via CERTIFICATE environment variable
# No certificate files exposed outside container

# Verify certificate permissions in container
docker exec crypto-robot-container ls -la /opt/crypto-robot/certificates/
```

### Certificate Renewal Procedures

#### Automated Renewal (Recommended)

```bash
# Set up automated Let's Encrypt renewal
# Add to crontab or systemd timer
0 2 * * 0 /path/to/tools/generate-certificates.sh jack.crypto-robot-itechsource.com letsencrypt

# Automated deployment after renewal
# 1. Rebuild Docker image with new certificates
# 2. Deploy updated image via GitHub Actions
# 3. Restart services to load new certificates
```

#### Manual Renewal Process

```bash
# 1. Generate new certificates
./tools/generate-certificates.sh jack.crypto-robot-itechsource.com letsencrypt

# 2. Verify certificate validity
openssl x509 -in certificates/jack.crypto-robot-itechsource.com/cert.pem -text -noout

# 3. Rebuild Docker image
docker build -f docker/Dockerfile -t crypto-robot:new-certs .

# 4. Deploy via GitHub Actions
gh workflow run build-robot-image.yml -f tag=new-certs
gh workflow run control-robot-aws.yml -f execute_command=update-robot-image

# 5. Restart services
gh workflow run control-robot-aws.yml \
  -f execute_command=stop-webapp \
  -f execute_command=start-webapp
```

#### Certificate Monitoring

```bash
# Monitor certificate expiration
# Add to monitoring system or cron job
openssl x509 -in certificates/jack.crypto-robot-itechsource.com/cert.pem -checkend 2592000 -noout
# Returns 0 if certificate expires within 30 days

# Certificate transparency monitoring
# Monitor CT logs for unauthorized certificates
# Use tools like certstream or crt.sh API
```

## Environment File Security and Secrets Management

### .env File Security

#### Local Development

```bash
# Secure .env file permissions
chmod 600 robot/.env              # Owner read/write only
chmod 600 robot/.env-*            # All environment files

# Never commit .env files to version control
# Add to .gitignore
echo "robot/.env*" >> .gitignore
echo "*.env" >> .gitignore

# Use .env.template for documentation
cp robot/.env robot/.env.template
# Remove sensitive values from template
sed -i 's/=.*/=your_value_here/' robot/.env.template
```

#### Production Environment

```bash
# Store production secrets in GitHub Secrets
# Never store in plain text files on servers

# Use base64 encoding for ENV_CONTENT
base64 -w 0 robot/.env-production > env_content.b64
# Copy content to GitHub Secrets → ENV_AWS_CONTENT
rm env_content.b64  # Remove temporary file
```

### GitHub Secrets Management

#### Required Secrets Configuration

```yaml
# DockerHub Authentication
DOCKERHUB_USERNAME: your_dockerhub_username
DOCKERHUB_TOKEN: personal_access_token_not_password

# AWS Authentication
AWS_ACCESS_KEY_ID: AKIA...
AWS_SECRET_ACCESS_KEY: secret_key
AWS_REGION: eu-west-1

# EC2 SSH Access
EC2_SSH_PRIVATE_KEY: |
  -----BEGIN OPENSSH PRIVATE KEY-----
  private_key_content_here
  -----END OPENSSH PRIVATE KEY-----
EC2_HOST: ec2-public-ip-or-hostname

# Application Configuration
ENV_AWS_CONTENT: base64_encoded_env_file_content
```

#### Secrets Security Best Practices

1. **Use Personal Access Tokens**: Never use passwords for DockerHub authentication
2. **Rotate Secrets Regularly**: Update secrets every 90 days minimum
3. **Least Privilege Access**: Use minimal required permissions for AWS IAM
4. **Separate Environments**: Use different secrets for staging/production
5. **Audit Access**: Monitor who accesses secrets and when

#### AWS IAM Security

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
      "Resource": "arn:aws:ec2:eu-west-1:account-id:instance/i-specific-instance-id"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeImages",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeKeyPairs"
      ],
      "Resource": "*"
    }
  ]
}
```

### Environment Variable Security

#### Sensitive Data Handling

```bash
# Never log sensitive environment variables
# Use secure logging practices

# In application code:
import os
import logging

# Configure logging to exclude sensitive data
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safe logging
api_key = os.getenv('BINANCE_API_KEY')
logger.info(f"Using API key: {api_key[:8]}...")  # Only log first 8 characters

# Unsafe logging (NEVER DO THIS)
# logger.info(f"API key: {api_key}")  # Exposes full API key
```

#### Container Environment Security

```bash
# Secure environment variable passing
# Use ENV_CONTENT instead of individual environment variables
docker run -e ENV_CONTENT="$(base64 -w 0 robot/.env)" crypto-robot

# Avoid exposing secrets in docker ps output
# Never use: docker run -e BINANCE_API_KEY=secret crypto-robot
```

## Container Security and Vulnerability Management

### Docker Image Security

#### Base Image Security

```dockerfile
# Use official, minimal base images
FROM python:3.11-slim

# Keep base image updated
# Regularly rebuild images to get security updates

# Avoid using 'latest' tag in production
FROM python:3.11.7-slim  # Use specific version
```

#### Container Hardening

```dockerfile
# Create non-root user
RUN groupadd -r cryptorobot && useradd -r -g cryptorobot cryptorobot

# Set secure file permissions
COPY --chown=cryptorobot:cryptorobot . /opt/crypto-robot/
RUN chmod -R 755 /opt/crypto-robot/
RUN chmod 600 /opt/crypto-robot/certificates/*/key.pem

# Use non-root user
USER cryptorobot

# Remove unnecessary packages
RUN apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*
```

#### Security Scanning

```bash
# Scan Docker images for vulnerabilities
# Use tools like Trivy, Clair, or Snyk

# Trivy scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image crypto-robot:latest

# Snyk scanning
snyk container test crypto-robot:latest

# Docker Scout (if available)
docker scout cves crypto-robot:latest
```

### Container Runtime Security

#### Resource Limits

```bash
# Set resource limits to prevent DoS
docker run --memory=1g --cpus=1.0 \
  -e ENV_CONTENT="$(base64 -w 0 robot/.env)" \
  crypto-robot

# Use read-only root filesystem when possible
docker run --read-only \
  -v /tmp:/tmp:rw \
  -v /opt/crypto-robot/data:/opt/crypto-robot/data:rw \
  crypto-robot
```

#### Network Security

```bash
# Use custom networks instead of default bridge
docker network create --driver bridge crypto-robot-net

# Run container on custom network
docker run --network crypto-robot-net crypto-robot

# Limit exposed ports
docker run -p 127.0.0.1:5443:5443 crypto-robot  # Bind to localhost only
```

#### Security Monitoring

```bash
# Monitor container behavior
docker stats crypto-robot-container

# Check for suspicious processes
docker exec crypto-robot-container ps aux

# Monitor file system changes
docker diff crypto-robot-container

# Check network connections
docker exec crypto-robot-container netstat -tulpn
```

### Vulnerability Management

#### Automated Scanning Pipeline

```yaml
# GitHub Actions security scanning
name: Security Scan
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly scan

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build image
        run: docker build -f docker/Dockerfile -t crypto-robot:scan .
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'crypto-robot:scan'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

#### Vulnerability Response Process

1. **Detection**: Automated scanning identifies vulnerabilities
2. **Assessment**: Evaluate severity and exploitability
3. **Prioritization**: Address critical and high-severity issues first
4. **Remediation**: Update dependencies, rebuild images, redeploy
5. **Verification**: Confirm vulnerabilities are resolved
6. **Documentation**: Record remediation actions

## Operational Security Best Practices

### Access Control

#### SSH Security

```bash
# Use SSH key authentication only
# Disable password authentication in /etc/ssh/sshd_config
PasswordAuthentication no
PubkeyAuthentication yes

# Use strong SSH keys
ssh-keygen -t ed25519 -b 4096 -f ~/.ssh/crypto-robot-key

# Restrict SSH access by IP
# In AWS Security Group, limit SSH (port 22) to specific IP ranges
```

#### Application Access

```bash
# Use HTTPS only in production
# Redirect HTTP to HTTPS

# Implement proper authentication
# Use strong session management
# Implement rate limiting
# Use CSRF protection
```

### Monitoring and Logging

#### Security Logging

```python
# Implement comprehensive security logging
import logging
from datetime import datetime

# Security event logging
def log_security_event(event_type, user_id, details):
    security_logger = logging.getLogger('security')
    security_logger.info({
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details,
        'source_ip': request.remote_addr
    })

# Examples:
log_security_event('login_attempt', user_id, {'success': True})
log_security_event('api_access', user_id, {'endpoint': '/api/trade'})
log_security_event('config_change', user_id, {'setting': 'trading_enabled'})
```

#### Monitoring Checklist

- [ ] Failed authentication attempts
- [ ] Unusual API usage patterns
- [ ] Certificate expiration warnings
- [ ] Container resource usage
- [ ] Network connection anomalies
- [ ] File system changes
- [ ] Trading activity patterns
- [ ] Error rates and types

### Incident Response

#### Security Incident Response Plan

1. **Detection**: Identify security incident
2. **Containment**: Isolate affected systems
3. **Investigation**: Determine scope and impact
4. **Eradication**: Remove threat and vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Document and improve

#### Emergency Procedures

```bash
# Emergency shutdown
gh workflow run control-robot-aws.yml \
  -f execute_command=stop-robot \
  -f execute_command=stop-webapp

# Emergency infrastructure shutdown
gh workflow run control-robot-infra.yml -f action=stop

# Revoke compromised credentials
# 1. Rotate GitHub secrets immediately
# 2. Revoke AWS access keys
# 3. Change DockerHub tokens
# 4. Update Binance API keys
```

### Compliance and Auditing

#### Security Audit Checklist

- [ ] All secrets stored securely (GitHub Secrets, not in code)
- [ ] Certificates are valid and properly configured
- [ ] Docker images scanned for vulnerabilities
- [ ] Access controls properly implemented
- [ ] Logging and monitoring configured
- [ ] Incident response procedures documented
- [ ] Regular security updates applied
- [ ] Backup and recovery procedures tested

#### Regular Security Tasks

**Daily**:
- Monitor application logs for anomalies
- Check certificate expiration warnings
- Review trading activity for unusual patterns

**Weekly**:
- Scan Docker images for new vulnerabilities
- Review access logs and authentication attempts
- Check for security updates to dependencies

**Monthly**:
- Rotate non-critical secrets and tokens
- Review and update security configurations
- Test incident response procedures
- Update security documentation

**Quarterly**:
- Comprehensive security audit
- Penetration testing (if applicable)
- Review and update security policies
- Security training and awareness updates

## Security Tools and Resources

### Recommended Security Tools

#### Vulnerability Scanning
- **Trivy**: Container vulnerability scanner
- **Snyk**: Dependency vulnerability scanning
- **OWASP Dependency Check**: Open source dependency scanner

#### Security Monitoring
- **Falco**: Runtime security monitoring
- **Sysdig**: Container security platform
- **Datadog**: Application performance monitoring with security features

#### Certificate Management
- **Certbot**: Let's Encrypt certificate automation
- **cert-manager**: Kubernetes certificate management
- **SSL Labs**: SSL configuration testing

### Security Resources

#### Documentation
- [OWASP Container Security Guide](https://owasp.org/www-project-container-security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)

#### Security Standards
- CIS Docker Benchmark
- NIST Cybersecurity Framework
- ISO 27001 Security Controls

#### Threat Intelligence
- CVE Database
- Docker Security Advisories
- AWS Security Bulletins
- Python Security Advisories

## Emergency Contacts and Procedures

### Security Incident Contacts

- **Primary Security Contact**: [Your security team email]
- **AWS Support**: [Your AWS support case URL]
- **DockerHub Support**: [DockerHub support contact]
- **Certificate Authority**: Let's Encrypt community support

### Emergency Response Procedures

1. **Immediate Response**: Stop all services and isolate systems
2. **Assessment**: Determine scope and severity of incident
3. **Communication**: Notify stakeholders and users if necessary
4. **Recovery**: Implement recovery procedures and restore services
5. **Post-Incident**: Conduct post-mortem and improve security measures

Remember: Security is an ongoing process, not a one-time setup. Regular reviews, updates, and improvements are essential for maintaining a secure crypto trading robot deployment.