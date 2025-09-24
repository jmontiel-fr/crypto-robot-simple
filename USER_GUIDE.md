# Crypto Robot User Guide

## Overview

This comprehensive guide covers how to build, deploy, configure, and access the crypto robot application both locally on your desktop and on AWS infrastructure. The application consists of two main components: a trading robot and a web application interface.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Building Docker Images](#building-docker-images)
4. [Local Container Deployment](#local-container-deployment)
5. [AWS Infrastructure Setup](#aws-infrastructure-setup)
6. [AWS Deployment](#aws-deployment)
7. [Configuration Management](#configuration-management)
8. [Accessing Applications](#accessing-applications)
9. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
10. [Maintenance and Updates](#maintenance-and-updates)

---

## Prerequisites

### Required Software
- **Docker Desktop** (for local development)
- **Git** (for source code management)
- **AWS CLI** (for AWS operations)
- **Terraform** (for infrastructure as code)
- **GitHub CLI** (optional, for GitHub Actions)

### Required Accounts and Access
- **GitHub Account** (with repository access)
- **AWS Account** (with appropriate permissions)
- **Binance API Account** (for trading operations)
- **Docker Hub Account** (for image registry)

### System Requirements
- **Local Development**: 8GB RAM, 20GB free disk space
- **AWS Instance**: t3.medium or larger recommended

---

## Local Development Setup

### 1. Clone Repository
```bash
# Clone the crypto-robot repository
git clone https://github.com/your-username/crypto-robot.git
cd crypto-robot
```

### 2. Environment Configuration
```bash
# Create environment file from template
cp .env.example .env

# Edit environment file with your configuration
nano .env
```

### 3. Required Environment Variables
```bash
# Binance API Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true  # Set to false for production

# Database Configuration
DATABASE_URL=sqlite:///database/crypto_robot.db

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your_secret_key

# Trading Configuration
TRADING_ENABLED=false  # Set to true to enable actual trading
DEFAULT_SYMBOL=BTCUSDT
DEFAULT_QUANTITY=0.001

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/crypto_robot.log
```

---

## Building Docker Images

### 1. Local Image Build
```bash
# Build the crypto-robot image locally
docker build -t crypto-robot:local .

# Build with specific tag
docker build -t crypto-robot:v1.0.0 .

# Build with build arguments
docker build --build-arg ENV=production -t crypto-robot:prod .
```

### 2. Multi-stage Build (Production)
```bash
# Build production image with optimizations
docker build --target production -t crypto-robot:production .

# Build development image with debugging tools
docker build --target development -t crypto-robot:dev .
```

### 3. Automated Build via GitHub Actions
The repository includes GitHub Actions workflows for automated building:

- **Manual Trigger**: Go to GitHub Actions → "Build Robot Image" → Run workflow
- **Automatic Trigger**: Push to main branch triggers build
- **Tagged Release**: Create a git tag to build versioned images

```bash
# Trigger build via git tag
git tag v1.0.0
git push origin v1.0.0
```

---

## Local Container Deployment

### 1. Single Container Deployment

#### Robot Mode (Trading Bot)
```bash
# Run crypto-robot in robot mode
docker run -d --name crypto-robot-local \
  --env-file .env \
  -e MODE=robot \
  -v $(pwd)/database:/opt/crypto-robot/database \
  -v $(pwd)/logs:/opt/crypto-robot/logs \
  -p 5443:5443 \
  crypto-robot:local
```

#### Webapp Mode (Web Interface)
```bash
# Run crypto-robot in webapp mode
docker run -d --name crypto-robot-webapp-local \
  --env-file .env \
  -e MODE=webapp \
  -v $(pwd)/database:/opt/crypto-robot/database \
  -v $(pwd)/logs:/opt/crypto-robot/logs \
  -p 5000:5000 \
  crypto-robot:local
```

### 2. Docker Compose Deployment
Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  crypto-robot:
    image: crypto-robot:local
    container_name: crypto-robot-app
    environment:
      - MODE=robot
      - CERTIFICATE=development
    env_file:
      - .env
    volumes:
      - ./database:/opt/crypto-robot/database
      - ./logs:/opt/crypto-robot/logs
    ports:
      - "5443:5443"
    restart: unless-stopped

  crypto-webapp:
    image: crypto-robot:local
    container_name: crypto-robot-webapp
    environment:
      - MODE=webapp
      - CERTIFICATE=development
    env_file:
      - .env
    volumes:
      - ./database:/opt/crypto-robot/database
      - ./logs:/opt/crypto-robot/logs
    ports:
      - "5000:5000"
    restart: unless-stopped
    depends_on:
      - crypto-robot

networks:
  default:
    name: crypto-robot-network
```

Deploy with Docker Compose:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart crypto-robot
```

### 3. Local Development with Hot Reload
```bash
# Run with source code mounted for development
docker run -d --name crypto-robot-dev \
  --env-file .env \
  -e MODE=webapp \
  -e FLASK_ENV=development \
  -v $(pwd)/app:/opt/crypto-robot/app \
  -v $(pwd)/database:/opt/crypto-robot/database \
  -p 5000:5000 \
  crypto-robot:dev
```

---

## AWS Infrastructure Setup

### 1. Prerequisites for AWS Deployment
```bash
# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Region, and Output format

# Verify AWS access
aws sts get-caller-identity
```

### 2. Terraform Infrastructure Deployment

#### Initialize Terraform
```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure
terraform apply
```

#### Infrastructure Components
The Terraform configuration creates:
- **EC2 Instance** (t3.medium) for running containers
- **Security Groups** with appropriate ports (22, 80, 443, 5000, 5443)
- **Key Pair** for SSH access
- **Elastic IP** for static IP address
- **IAM Roles** for necessary permissions

### 3. Manual AWS Setup (Alternative)

#### Create EC2 Instance
```bash
# Create key pair
aws ec2 create-key-pair --key-name crypto-robot-key --query 'KeyMaterial' --output text > crypto-robot-key.pem
chmod 400 crypto-robot-key.pem

# Create security group
aws ec2 create-security-group --group-name crypto-robot-sg --description "Crypto Robot Security Group"

# Add security group rules
aws ec2 authorize-security-group-ingress --group-name crypto-robot-sg --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name crypto-robot-sg --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name crypto-robot-sg --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name crypto-robot-sg --protocol tcp --port 5000 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name crypto-robot-sg --protocol tcp --port 5443 --cidr 0.0.0.0/0

# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type t3.medium \
  --key-name crypto-robot-key \
  --security-groups crypto-robot-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=crypto-robot-instance}]'
```

---

## AWS Deployment

### 1. Automated Deployment via GitHub Actions

#### Setup GitHub Secrets
Configure the following secrets in your GitHub repository:

```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
```

#### Trigger Deployment
```bash
# Deploy infrastructure
# Go to GitHub Actions → "Build Robot Infrastructure" → Run workflow

# Deploy application
# Go to GitHub Actions → "Control Robot AWS" → Run workflow → Select "deploy"
```

### 2. Manual AWS Deployment

#### Prepare AWS Instance
```bash
# SSH to AWS instance
ssh -i crypto-robot-key.pem ec2-user@<INSTANCE_IP>

# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Create application directory
sudo mkdir -p /opt/crypto-robot
sudo chown ec2-user:ec2-user /opt/crypto-robot
```

#### Deploy Application
```bash
# Create environment file on AWS instance
cat > /opt/crypto-robot/.env << 'EOF'
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=false
DATABASE_URL=sqlite:///database/crypto_robot.db
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your_production_secret_key
TRADING_ENABLED=true
DEFAULT_SYMBOL=BTCUSDT
DEFAULT_QUANTITY=0.001
LOG_LEVEL=INFO
EOF

# Create database directory
mkdir -p /opt/crypto-robot/database

# Pull and run containers
cd /opt/crypto-robot

# Run robot container
docker run -d --name crypto-robot-app \
  -e ENV_CONTENT="$(base64 -w 0 .env)" \
  -e CERTIFICATE="production" \
  -e MODE="robot" \
  -v $(pwd)/database:/opt/crypto-robot/database \
  --restart unless-stopped \
  -p 5443:5443 \
  jmontiel/crypto-robot:latest

# Run webapp container
docker run -d --name crypto-robot-webapp \
  -e ENV_CONTENT="$(base64 -w 0 .env)" \
  -e CERTIFICATE="production" \
  -e MODE="webapp" \
  -v $(pwd)/database:/opt/crypto-robot/database \
  --restart unless-stopped \
  -p 5000:5000 \
  jmontiel/crypto-robot:latest
```

---

## Configuration Management

### 1. Environment Configuration

#### Development Environment
```bash
# .env for development
BINANCE_TESTNET=true
FLASK_ENV=development
FLASK_DEBUG=true
TRADING_ENABLED=false
LOG_LEVEL=DEBUG
```

#### Production Environment
```bash
# .env for production
BINANCE_TESTNET=false
FLASK_ENV=production
FLASK_DEBUG=false
TRADING_ENABLED=true
LOG_LEVEL=INFO
```

### 2. SSL Certificate Configuration

#### Development (Self-signed)
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

#### Production (Let's Encrypt)
```bash
# Install certbot
sudo yum install -y certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to application directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/crypto-robot/certificates/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/crypto-robot/certificates/
```

### 3. Database Configuration

#### SQLite (Default)
```bash
# Database file location
DATABASE_URL=sqlite:///database/crypto_robot.db

# Backup database
sqlite3 database/crypto_robot.db ".backup backup_$(date +%Y%m%d).db"
```

#### PostgreSQL (Advanced)
```bash
# PostgreSQL configuration
DATABASE_URL=postgresql://username:password@localhost:5432/crypto_robot

# Run PostgreSQL container
docker run -d --name postgres \
  -e POSTGRES_DB=crypto_robot \
  -e POSTGRES_USER=crypto_user \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

---

## Accessing Applications

### 1. Local Access

#### Web Application
```bash
# Development (HTTP)
http://localhost:5000

# Production (HTTPS)
https://localhost:5443
```

#### API Endpoints
```bash
# Health check
curl http://localhost:5000/health

# Trading status
curl http://localhost:5000/api/status

# Portfolio information
curl http://localhost:5000/api/portfolio
```

### 2. AWS Access

#### Web Application
```bash
# Get instance IP
aws ec2 describe-instances --filters "Name=tag:Name,Values=crypto-robot-instance" --query 'Reservations[0].Instances[0].PublicIpAddress'

# Access web application
https://<INSTANCE_IP>:5443
http://<INSTANCE_IP>:5000
```

#### SSH Access
```bash
# SSH to instance
ssh -i crypto-robot-key.pem ec2-user@<INSTANCE_IP>

# Port forwarding for local access
ssh -i crypto-robot-key.pem -L 5000:localhost:5000 -L 5443:localhost:5443 ec2-user@<INSTANCE_IP>
```

### 3. API Access Examples

#### Using curl
```bash
# Get trading status
curl -k https://<INSTANCE_IP>:5443/api/status

# Get portfolio
curl -k https://<INSTANCE_IP>:5443/api/portfolio

# Place test order (if enabled)
curl -k -X POST https://<INSTANCE_IP>:5443/api/order \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","side":"BUY","quantity":"0.001","type":"MARKET"}'
```

#### Using Python
```python
import requests

# Configure base URL
base_url = "https://<INSTANCE_IP>:5443"

# Get status
response = requests.get(f"{base_url}/api/status", verify=False)
print(response.json())

# Get portfolio
response = requests.get(f"{base_url}/api/portfolio", verify=False)
print(response.json())
```

---

## Monitoring and Troubleshooting

### 1. Container Monitoring

#### Check Container Status
```bash
# Local monitoring
docker ps
docker logs crypto-robot-app
docker stats

# AWS monitoring (via SSH)
ssh -i crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker ps"
ssh -i crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker logs crypto-robot-app"
```

#### Resource Monitoring
```bash
# Monitor system resources
docker stats --no-stream

# Monitor disk usage
df -h
du -sh /opt/crypto-robot/*

# Monitor network connections
netstat -tulpn | grep -E '(5000|5443)'
```

### 2. Application Monitoring

#### Health Checks
```bash
# Application health
curl -k https://localhost:5443/health

# Database connectivity
curl -k https://localhost:5443/api/db-status

# External API connectivity
curl -k https://localhost:5443/api/binance-status
```

#### Log Analysis
```bash
# View application logs
docker logs crypto-robot-app --tail 100

# Search for errors
docker logs crypto-robot-app 2>&1 | grep -i error

# Monitor live logs
docker logs -f crypto-robot-app | grep --line-buffered -E '(ERROR|WARNING|INFO)'
```

### 3. Troubleshooting Common Issues

#### Container Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check image availability
docker images | grep crypto-robot

# Check environment file
cat .env | head -5

# Check port conflicts
netstat -tulpn | grep -E '(5000|5443)'
```

#### Application Errors
```bash
# Check application logs
docker logs crypto-robot-app --tail 50

# Check database file
ls -la database/crypto_robot.db

# Test database connectivity
docker exec crypto-robot-app sqlite3 database/crypto_robot.db ".tables"

# Check API connectivity
docker exec crypto-robot-app curl -s https://api.binance.com/api/v3/ping
```

#### Network Issues
```bash
# Check security groups (AWS)
aws ec2 describe-security-groups --group-names crypto-robot-sg

# Check firewall (local)
sudo ufw status

# Test port connectivity
telnet <INSTANCE_IP> 5443
nc -zv <INSTANCE_IP> 5443
```

---

## Maintenance and Updates

### 1. Application Updates

#### Local Updates
```bash
# Pull latest code
git pull origin main

# Rebuild image
docker build -t crypto-robot:local .

# Update containers
docker-compose down
docker-compose up -d
```

#### AWS Updates
```bash
# Automated update via GitHub Actions
# Go to GitHub Actions → "Control Robot AWS" → Run workflow → Select "update"

# Manual update
ssh -i crypto-robot-key.pem ec2-user@<INSTANCE_IP> "
docker stop crypto-robot-app crypto-robot-webapp
docker rm crypto-robot-app crypto-robot-webapp
docker pull jmontiel/crypto-robot:latest
# Restart containers with new image
"
```

### 2. Database Maintenance

#### Backup Database
```bash
# Local backup
docker exec crypto-robot-app sqlite3 database/crypto_robot.db ".backup backup_$(date +%Y%m%d).db"

# AWS backup
ssh -i crypto-robot-key.pem ec2-user@<INSTANCE_IP> "
docker exec crypto-robot-app sqlite3 /opt/crypto-robot/database/crypto_robot.db '.backup /tmp/backup.db'
docker cp crypto-robot-app:/tmp/backup.db /opt/crypto-robot/database/backup_$(date +%Y%m%d).db
"
```

#### Database Cleanup
```bash
# Clean old log entries
docker exec crypto-robot-app sqlite3 database/crypto_robot.db "DELETE FROM logs WHERE timestamp < datetime('now', '-30 days');"

# Vacuum database
docker exec crypto-robot-app sqlite3 database/crypto_robot.db "VACUUM;"

# Analyze database
docker exec crypto-robot-app sqlite3 database/crypto_robot.db "ANALYZE;"
```

### 3. System Maintenance

#### Clean Docker Resources
```bash
# Remove unused containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Complete system cleanup
docker system prune -a -f
```

#### Update System Packages
```bash
# Local (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# AWS (Amazon Linux)
ssh -i crypto-robot-key.pem ec2-user@<INSTANCE_IP> "sudo yum update -y"
```

### 4. Security Updates

#### Update SSL Certificates
```bash
# Renew Let's Encrypt certificates
sudo certbot renew

# Update self-signed certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

#### Rotate API Keys
```bash
# Update environment file with new keys
nano .env

# Restart containers to apply changes
docker-compose restart
```

---

## Best Practices

### 1. Security
- Use strong, unique passwords and API keys
- Enable 2FA on all accounts (GitHub, AWS, Binance)
- Regularly rotate API keys and certificates
- Use HTTPS in production
- Restrict security group access to necessary IPs
- Keep system and Docker updated

### 2. Monitoring
- Set up log rotation to prevent disk space issues
- Monitor container resource usage
- Set up alerts for application errors
- Regular health checks
- Monitor trading performance and errors

### 3. Backup and Recovery
- Regular database backups
- Store backups in multiple locations
- Test backup restoration procedures
- Document recovery procedures
- Version control all configuration files

### 4. Development
- Use version tags for Docker images
- Test changes in development environment first
- Use feature branches for development
- Document configuration changes
- Maintain changelog for releases

---

## Support and Resources

### Documentation
- [Docker Documentation](https://docs.docker.com/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Terraform Documentation](https://www.terraform.io/docs/)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)

### Troubleshooting
- Check application logs first
- Verify environment configuration
- Test network connectivity
- Check resource availability
- Review security group settings

### Getting Help
- Create GitHub issues for bugs
- Check existing documentation
- Review container logs for errors
- Test with minimal configuration
- Provide detailed error information when seeking help

This user guide provides comprehensive instructions for building, deploying, configuring, and accessing the crypto robot application in both local and AWS environments. Follow the sections relevant to your deployment scenario and refer to the troubleshooting section when issues arise.