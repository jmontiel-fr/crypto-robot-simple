# Crypto Robot - Python Direct Deployment Guide

## Overview

This guide covers the deployment of the Crypto Robot using direct Python execution instead of Docker containers. This approach simplifies the deployment process while maintaining security and reliability through systemd service management and GitHub Actions automation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Configuration](#environment-configuration)
4. [API Key Management](#api-key-management)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Deployment Process](#deployment-process)
7. [Service Management](#service-management)
8. [Monitoring and Logs](#monitoring-and-logs)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Operating System**: Amazon Linux 2 or Ubuntu 20.04+
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM
- **Storage**: Minimum 10GB available space
- **Network**: Internet connectivity for API access

### Required Packages
```bash
# Amazon Linux 2
sudo yum update -y
sudo yum install -y python3 python3-pip python3-venv git openssl

# Ubuntu
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git openssl
```

### User Setup
The application runs as the `ec2-user` (Amazon Linux) or `ubuntu` (Ubuntu) user with appropriate permissions.

## Initial Setup

### 1. Clone Repository
```bash
# Clone to the standard application directory
cd /opt
sudo git clone https://github.com/your-repo/crypto-robot.git
sudo chown -R ec2-user:ec2-user crypto-robot
cd crypto-robot
```

### 2. Setup Python Environment
```bash
# Run the automated setup script
chmod +x scripts/setup-python-env.sh
./scripts/setup-python-env.sh
```

This script will:
- Create a Python virtual environment at `/opt/crypto-robot/venv`
- Install all required dependencies from `requirements.txt`
- Validate the installation
- Create helper scripts for environment management

### 3. Verify Installation
```bash
# Check environment setup
./scripts/health-check.sh --quick
```

## Environment Configuration

### 1. Create Environment File
```bash
# Create .env from template
cp robot/.env.template .env
chmod 600 .env
```

### 2. Configure Basic Settings
Edit the `.env` file with your specific configuration:

```bash
# Basic Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_PROTOCOL=http
USE_HTTPS=false

# Domain Configuration
DOMAIN_NAME=your-hostname.com
HOSTNAME=your-hostname.com

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_PATH=/opt/crypto-robot/database
DATABASE_FILE=cryptorobot.db

# Trading Configuration
STARTING_CAPITAL=100
ROBOT_DRY_RUN=true
STRATEGY_NAME=daily_rebalance
```

### 3. Validate Configuration
```bash
# Validate environment file
./scripts/manage-env.sh validate
```

## API Key Management

### GitHub Secrets Configuration

API keys are managed through GitHub secrets using the pattern `<HOST>_KEYS`:

1. **Create GitHub Secret**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Create a new secret with the name pattern: `HOSTNAME_KEYS`
   - Example names:
     - `CRYPTO_ROBOT_LOCAL_KEYS`
     - `JACK_ROBOT_CRYPTO_VISION_COM_KEYS`
     - `ITS_ROBOT_CRYPTO_VISION_COM_KEYS`

2. **Secret Format** (JSON):
```json
{
  "BINANCE_API_KEY": "your_actual_api_key_here",
  "BINANCE_SECRET_KEY": "your_actual_secret_key_here"
}
```

### Manual API Key Injection
For local testing or manual deployment:

```bash
# Set hostname and inject keys
export HOSTNAME="your-hostname.com"
export YOUR_HOSTNAME_COM_KEYS='{"BINANCE_API_KEY":"your_key","BINANCE_SECRET_KEY":"your_secret"}'
./scripts/inject-api-keys.sh
```

## SSL Certificate Setup

### 1. Certificate Management
The system supports hostname-based certificate management:

```bash
# Setup certificates for a hostname
./scripts/configure-certificates.sh setup your-hostname.com

# List available certificates
./scripts/configure-certificates.sh list

# Validate certificates
./scripts/configure-certificates.sh validate your-hostname.com
```

### 2. Certificate Sources

#### From Environment Variables
Certificates can be embedded in the `.env` file:
```bash
SSL_CERT_CONTENT="-----BEGIN CERTIFICATE-----
...certificate content...
-----END CERTIFICATE-----"

SSL_KEY_CONTENT="-----BEGIN PRIVATE KEY-----
...private key content...
-----END PRIVATE KEY-----"
```

#### From Files
```bash
# Copy certificates from files
./scripts/configure-certificates.sh copy your-hostname.com /path/to/cert.pem /path/to/key.pem
```

### 3. HTTPS Configuration
Update `.env` for HTTPS:
```bash
USE_HTTPS=true
FLASK_PROTOCOL=https
SSL_CERT_PATH=/opt/crypto-robot/certificates/your-hostname.com/cert.pem
SSL_KEY_PATH=/opt/crypto-robot/certificates/your-hostname.com/key.pem
```

## Deployment Process

### Automated Deployment (GitHub Actions)

1. **Trigger Deployment**:
   - Go to Actions → control-robot-aws
   - Select your environment
   - Choose commands to execute

2. **Common Deployment Workflows**:

   **Initial Setup**:
   ```
   Commands: update-code,setup-environment,start-robot,start-webapp
   Initialize environment: ✓
   ```

   **Update Deployment**:
   ```
   Commands: stop-robot,stop-webapp,update-code,start-robot,start-webapp
   Initialize environment: ✗
   ```

   **Status Check**:
   ```
   Commands: application-status
   ```

### Manual Deployment

1. **Update Code**:
```bash
cd /opt/crypto-robot
git pull origin main
```

2. **Update Dependencies**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

3. **Start Services**:
```bash
# Start robot
./scripts/start-robot-direct.sh

# Start webapp
./scripts/start-webapp-direct.sh
```

## Service Management

### Systemd Services

Install systemd services for automatic startup and management:

```bash
# Install services
sudo ./scripts/install-systemd-services.sh

# Service management
sudo systemctl start crypto-robot
sudo systemctl start crypto-webapp
sudo systemctl enable crypto-robot
sudo systemctl enable crypto-webapp
```

### Service Control Script

Use the unified service control script:

```bash
# Start services
sudo ./scripts/service-control.sh start robot
sudo ./scripts/service-control.sh start webapp

# Check status
./scripts/service-control.sh status

# View logs
./scripts/service-control.sh logs robot 100
./scripts/service-control.sh follow webapp

# Stop services
sudo ./scripts/service-control.sh stop robot
sudo ./scripts/service-control.sh stop webapp
```

### Direct Script Management

For development or troubleshooting:

```bash
# Start applications directly
./scripts/start-robot-direct.sh --mode single --capital 100
./scripts/start-webapp-direct.sh --port 5000 --host 0.0.0.0

# Stop applications
./scripts/stop-robot-direct.sh --status
./scripts/stop-webapp-direct.sh --logs
```

## Monitoring and Logs

### Log Files
- **Robot Logs**: `/opt/crypto-robot/logs/robot-*.log`
- **WebApp Logs**: `/opt/crypto-robot/logs/webapp-*.log`
- **Systemd Logs**: `journalctl -u crypto-robot -f`

### Health Monitoring
```bash
# Full health check
./scripts/health-check.sh

# Quick check
./scripts/health-check.sh --quick

# API connectivity test
./scripts/health-check.sh --api-only
```

### Process Monitoring
```bash
# Check running processes
ps aux | grep -E 'python.*(main|app)\.py'

# Check PID files
ls -la /opt/crypto-robot/*.pid

# Check service status
./scripts/service-control.sh status
```

## Troubleshooting

### Common Issues

#### 1. Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
./scripts/setup-python-env.sh
```

#### 2. Permission Issues
```bash
# Fix ownership
sudo chown -R ec2-user:ec2-user /opt/crypto-robot

# Fix permissions
chmod 600 .env
chmod +x scripts/*.sh
```

#### 3. API Key Issues
```bash
# Validate API keys
./scripts/manage-env.sh show | grep -E "(API_KEY|SECRET_KEY)"

# Re-inject API keys
./scripts/inject-api-keys.sh --validate-only
```

#### 4. Certificate Issues
```bash
# Validate certificates
./scripts/configure-certificates.sh validate your-hostname.com

# Test SSL configuration
./scripts/configure-certificates.sh test your-hostname.com
```

#### 5. Service Issues
```bash
# Check service status
sudo systemctl status crypto-robot
sudo systemctl status crypto-webapp

# View service logs
journalctl -u crypto-robot -n 50
journalctl -u crypto-webapp -n 50

# Restart services
sudo systemctl restart crypto-robot
sudo systemctl restart crypto-webapp
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Update .env
FLASK_DEBUG=true
ROBOT_DRY_RUN=true

# Restart services
sudo ./scripts/service-control.sh restart-all
```

### Log Analysis

```bash
# Check recent errors
grep -i error /opt/crypto-robot/logs/*.log | tail -20

# Monitor real-time logs
tail -f /opt/crypto-robot/logs/robot-*.log

# Check application startup
journalctl -u crypto-robot --since "10 minutes ago"
```

## Security Considerations

### File Permissions
- `.env` file: 600 (owner read/write only)
- Certificate files: 600 for keys, 644 for certificates
- Application directory: 755 with ec2-user ownership
- Log files: 644 with proper rotation

### Network Security
- Configure firewall rules for required ports
- Use HTTPS for web interface in production
- Restrict SSH access to authorized users
- Monitor for unusual network activity

### API Key Security
- Store API keys only in GitHub secrets
- Never commit API keys to repository
- Rotate API keys regularly
- Monitor API usage for anomalies

## Performance Optimization

### Resource Monitoring
```bash
# Monitor resource usage
htop
df -h
free -h

# Check application resource usage
ps aux | grep python | awk '{print $2, $3, $4, $11}'
```

### Log Rotation
Configure log rotation to prevent disk space issues:

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/crypto-robot << EOF
/opt/crypto-robot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ec2-user ec2-user
}
EOF
```

## Backup and Recovery

### Database Backup
```bash
# Backup SQLite database
cp /opt/crypto-robot/database/cryptorobot.db /opt/crypto-robot/backups/cryptorobot-$(date +%Y%m%d).db
```

### Configuration Backup
```bash
# Backup configuration
./scripts/manage-env.sh backup
```

### Full System Backup
```bash
# Create full backup
tar -czf crypto-robot-backup-$(date +%Y%m%d).tar.gz \
  --exclude=venv \
  --exclude=logs \
  /opt/crypto-robot
```

## Migration from Docker

If migrating from a Docker-based deployment:

1. **Stop Docker containers**:
```bash
docker stop crypto-robot-app crypto-robot-webapp
docker rm crypto-robot-app crypto-robot-webapp
```

2. **Backup Docker data**:
```bash
docker cp crypto-robot-app:/opt/crypto-robot/database ./database-backup
```

3. **Follow this deployment guide** for Python setup

4. **Restore data**:
```bash
cp -r database-backup/* /opt/crypto-robot/database/
```

## Support and Maintenance

### Regular Maintenance Tasks
- Update dependencies monthly
- Rotate logs weekly
- Monitor disk space daily
- Check certificate expiration monthly
- Review API key usage weekly

### Getting Help
- Check application logs first
- Run health checks
- Review this documentation
- Check GitHub Issues for known problems

---

*This guide covers the complete deployment process for the Python-based Crypto Robot. For additional support, refer to the troubleshooting section or create an issue in the repository.*