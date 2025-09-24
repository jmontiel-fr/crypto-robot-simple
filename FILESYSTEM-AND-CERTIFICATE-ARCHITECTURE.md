# Crypto Robot - File System and Certificate Architecture

## 📋 Table of Contents

1. [Overview](#overview)
2. [EC2 File System Structure](#ec2-file-system-structure)
3. [Container File System Structure](#container-file-system-structure)
4. [Certificate Management Architecture](#certificate-management-architecture)
5. [Environment File Flow](#environment-file-flow)
6. [Docker Command File Paths](#docker-command-file-paths)
7. [Security Model](#security-model)
8. [Troubleshooting File Locations](#troubleshooting-file-locations)

---

## Overview

The Crypto Robot dockerization system uses a sophisticated file management architecture that prioritizes security and flexibility. This document details exactly where files are stored, how they flow between systems, and how certificates are managed securely.

### Key Principles

🔐 **Security First**: Certificates never stored as plain files on EC2  
📁 **Clear Separation**: Different file locations for different purposes  
🔄 **Runtime Extraction**: Certificates extracted from environment variables at container startup  
🌍 **Environment Isolation**: Each environment has its own file structure  

---

## EC2 File System Structure

### Base Directory Structure (Multi-Host Support)

```
/opt/crypto-robot/                    # Main application directory (APP_BASE_DIR)
├── hosts/                            # Host-specific directories
│   ├── crypto-robot.local/          # Local development host
│   │   └── app/
│   │       └── .env                  # Environment file for crypto-robot.local
│   ├── jack_robot.crypto-vision.com/  # Jack's production host
│   │   └── app/
│   │       └── .env                  # Environment file for jack_robot.crypto-vision.com
│   ├── its_robot.crypto-vision.com/   # ITS production host
│   │   └── app/
│   │       └── .env                  # Environment file for its_robot.crypto-vision.com
│   └── <custom>_robot.crypto-vision.com/  # Additional custom hosts
│       └── app/
│           └── .env                  # Environment file for custom hostname
├── data/                             # Shared application data (created by Terraform)
├── logs/                             # Shared application logs (created by Terraform)
└── backups/                          # Shared backup files (created by Terraform)
```

### File Locations and Purposes

#### Environment Files (Host-Specific)
```bash
# Local development
Location: /opt/crypto-robot/hosts/crypto-robot.local/app/.env
Source: GitHub Environment Secret (ENV_CONTENT from crypto-robot.local environment)

# Jack's Production
Location: /opt/crypto-robot/hosts/jack_robot.crypto-vision.com/app/.env
Source: GitHub Environment Secret (ENV_CONTENT from jack_robot.crypto-vision.com environment)

# ITS Production
Location: /opt/crypto-robot/hosts/its_robot.crypto-vision.com/app/.env
Source: GitHub Environment Secret (ENV_CONTENT from its_robot.crypto-vision.com environment)

# Custom hosts
Location: /opt/crypto-robot/hosts/<hostname>/app/.env
Source: GitHub Environment Secret (ENV_CONTENT from <hostname> environment)

Purpose: Contains all configuration including embedded certificates for specific host
Permissions: 600 (read/write owner only)
Created by: GitHub Actions workflow (init_env step)
```

#### Application Directory
```bash
Location: /opt/crypto-robot/
Owner: ec2-user
Permissions: 755
Created by: Terraform user-data script
```

### File Creation Timeline

1. **Terraform Deployment**: Creates `/opt/crypto-robot/` directory structure
2. **GitHub Actions (init_env)**: Copies `.env` file from environment secret
3. **Docker Run**: Reads `.env` file and passes to container via ENV_CONTENT

---

## Container File System Structure

### Container Directory Layout

```
/opt/crypto-robot/                    # Container working directory
├── app/                              # Application code (from Docker image)
│   ├── main.py                       # Main application
│   ├── start_https_server.py         # HTTPS server
│   ├── start_fresh_portfolio.py      # Portfolio management
│   ├── src/                          # Source modules
│   ├── templates/                    # Flask templates
│   ├── static/                       # Static assets
│   └── .env                          # Environment file (recreated from ENV_CONTENT)
├── certificates/                     # Certificate storage (created at runtime)
│   └── <hostname>/                   # Hostname-specific certificates
│       ├── cert.pem                  # SSL certificate (extracted from .env)
│       └── key.pem                   # Private key (extracted from .env)
├── data/                             # Application data
├── logs/                             # Application logs
└── scripts/                          # Container scripts
    ├── entrypoint.sh                 # Main entry point
    ├── start-robot.sh                # Robot startup
    └── start-webapp.sh               # WebApp startup
```

### Runtime File Creation Process

1. **Container Startup**: `entrypoint.sh` executes
2. **Environment Recreation**: `.env` file recreated from `ENV_CONTENT` environment variable
3. **Certificate Extraction**: Certificates extracted from `.env` strings to files
4. **Application Launch**: Robot/webapp started with proper certificate paths

---

## Certificate Management Architecture

### Certificate Storage Strategy

#### ❌ **What We DON'T Do**
- Store certificate files on EC2 filesystem
- Embed certificates in Docker images
- Use shared certificate volumes
- Store certificates in plain text files

#### ✅ **What We DO**
- Store certificates as environment variable strings
- Extract certificates at container runtime
- Create certificate files inside secure container
- Use hostname-based certificate organization

### Certificate Flow Diagram

```mermaid
graph TD
    A[Generate Certificates] --> B[tools/generate-certificates.sh]
    B --> C[certificates/hostname/cert.pem]
    B --> D[certificates/hostname/key.pem]
    
    C --> E[tools/create-env-with-certs.sh]
    D --> E
    E --> F[.env file with SSL_CERT_CONTENT]
    
    F --> G[base64 encode]
    G --> H[GitHub Environment Secret]
    
    H --> I[GitHub Actions Workflow]
    I --> J[EC2: /opt/crypto-robot/app/.env]
    
    J --> K[Docker Run: ENV_CONTENT]
    K --> L[Container: entrypoint.sh]
    L --> M[Extract SSL_CERT_CONTENT]
    L --> N[Extract SSL_KEY_CONTENT]
    
    M --> O[Container: /opt/crypto-robot/certificates/hostname/cert.pem]
    N --> P[Container: /opt/crypto-robot/certificates/hostname/key.pem]
```

### Certificate Environment Variables

#### In .env File
```bash
# Certificate content stored as multi-line strings
SSL_CERT_CONTENT="-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKL0UG+jkjkjMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
...certificate content continues...
-----END CERTIFICATE-----"

SSL_KEY_CONTENT="-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
wUw2wJ2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F
...private key content continues...
-----END PRIVATE KEY-----"
```

#### Container Runtime Extraction
```bash
# In entrypoint.sh
setup_certificates() {
    local cert_name="${CERTIFICATE:-$DEFAULT_CERTIFICATE}"
    local cert_dir="$APP_DIR/certificates/$cert_name"
    
    # Create certificate directory
    mkdir -p "$cert_dir"
    
    # Extract certificate content from environment
    echo "$SSL_CERT_CONTENT" > "$cert_dir/cert.pem"
    echo "$SSL_KEY_CONTENT" > "$cert_dir/key.pem"
    
    # Set secure permissions
    chmod 600 "$cert_dir/cert.pem" "$cert_dir/key.pem"
}
```

---

## Environment File Flow

### Complete .env File Journey

#### 1. Local Development
```bash
# Location: robot/.env (local development)
# Purpose: Direct Python execution
# Usage: python main.py --mode web
```

#### 2. Certificate Integration
```bash
# Tool: ./tools/create-env-with-certs.sh
# Input: certificates/hostname/cert.pem, certificates/hostname/key.pem
# Output: .env file with embedded SSL_CERT_CONTENT and SSL_KEY_CONTENT
```

#### 3. GitHub Environment Secret
```bash
# Process: base64 -w 0 .env-with-certs
# Storage: GitHub Environment Secret (ENV_CONTENT)
# Environment: Named by hostname (e.g., "jack.crypto-robot-itechsource.com")
```

#### 4. GitHub Actions Workflow
```bash
# Step: Initialize environment
# Action: echo "${{ secrets.ENV_CONTENT }}" | base64 -d > .env-host
# Transfer: scp .env-host ec2-user@ip:/opt/crypto-robot/app/.env
```

#### 5. Docker Container
```bash
# Command: docker run -e ENV_CONTENT="$(base64 -w 0 app/.env)"
# Process: entrypoint.sh recreates .env from ENV_CONTENT
# Location: /opt/crypto-robot/app/.env (inside container)
```

### Environment File Permissions

| Location | File | Permissions | Owner | Purpose |
|----------|------|-------------|-------|---------|
| Local | `robot/.env` | 600 | developer | Local development |
| EC2 | `/opt/crypto-robot/app/.env` | 600 | ec2-user | Docker input |
| Container | `/opt/crypto-robot/app/.env` | 600 | crypto-robot | Application config |

---

## Docker Command File Paths

### Current Docker Run Commands

#### Robot Container (Host-Specific)
```bash
# Jack's production host
cd /opt/crypto-robot/hosts/jack_robot.crypto-vision.com && \
docker run -d --name crypto-robot-jack_robot.crypto-vision.com-app \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="jack_robot.crypto-vision.com" \
  -e MODE="robot" \
  --restart unless-stopped \
  -p 5443:5443 \
  jmontiel/crypto-robot:latest

# ITS production host
cd /opt/crypto-robot/hosts/its_robot.crypto-vision.com && \
docker run -d --name crypto-robot-its_robot.crypto-vision.com-app \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="its_robot.crypto-vision.com" \
  -e MODE="robot" \
  --restart unless-stopped \
  -p 5444:5444 \
  jmontiel/crypto-robot:latest

# Local development host
cd /opt/crypto-robot/hosts/crypto-robot.local && \
docker run -d --name crypto-robot-crypto-robot.local-app \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -e MODE="robot" \
  --restart unless-stopped \
  -p 5000:5000 \
  jmontiel/crypto-robot:latest
```

#### WebApp Container (Host-Specific)
```bash
# Jack's production host
cd /opt/crypto-robot/hosts/jack_robot.crypto-vision.com && \
docker run -d --name crypto-robot-jack_robot.crypto-vision.com-webapp \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="jack_robot.crypto-vision.com" \
  -e MODE="webapp" \
  --restart unless-stopped \
  -p 5001:5000 \
  jmontiel/crypto-robot:latest

# ITS production host
cd /opt/crypto-robot/hosts/its_robot.crypto-vision.com && \
docker run -d --name crypto-robot-its_robot.crypto-vision.com-webapp \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="its_robot.crypto-vision.com" \
  -e MODE="webapp" \
  --restart unless-stopped \
  -p 5002:5000 \
  jmontiel/crypto-robot:latest

# Local development host  
cd /opt/crypto-robot/hosts/crypto-robot.local && \
docker run -d --name crypto-robot-crypto-robot.local-webapp \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -e MODE="webapp" \
  --restart unless-stopped \
  -p 5002:5000 \
  jmontiel/crypto-robot:latest
```

### File Path Analysis

#### EC2 Host Paths (Multi-Host)
```bash
Base Directory: /opt/crypto-robot
Host-Specific Working Directory: /opt/crypto-robot/hosts/<hostname>
.env File Path: app/.env (relative to host working directory)

# Examples:
# Jack's production host
Full Path: /opt/crypto-robot/hosts/jack_robot.crypto-vision.com/app/.env
Base64 Command: base64 -w 0 app/.env (from host directory)

# ITS production host
Full Path: /opt/crypto-robot/hosts/its_robot.crypto-vision.com/app/.env
Base64 Command: base64 -w 0 app/.env (from host directory)

# Local development host
Full Path: /opt/crypto-robot/hosts/crypto-robot.local/app/.env
Base64 Command: base64 -w 0 app/.env (from host directory)
```

#### Container Paths
```bash
Working Directory: /opt/crypto-robot (WORKDIR in Dockerfile)
.env Recreation: /opt/crypto-robot/app/.env
Certificate Extraction: /opt/crypto-robot/certificates/<hostname>/
Application Code: /opt/crypto-robot/app/
```

### Manual Docker Commands

#### Local Testing
```bash
# From repository root
docker run -e ENV_CONTENT="$(base64 -w 0 robot/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -p 5000:5000 \
  crypto-robot
```

#### EC2 Manual Execution (Multi-Host)
```bash
# SSH to EC2 instance
ssh -i web-crypto-robot-key.pem ec2-user@<instance-ip>

# Navigate to specific host directory (Jack's production)
cd /opt/crypto-robot/hosts/jack_robot.crypto-vision.com

# Run container manually for Jack's production host
docker run -d --name crypto-robot-jack_robot.crypto-vision.com-manual \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="jack_robot.crypto-vision.com" \
  -p 5443:5443 \
  crypto-robot

# Or for ITS production host
cd /opt/crypto-robot/hosts/its_robot.crypto-vision.com
docker run -d --name crypto-robot-its_robot.crypto-vision.com-manual \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="its_robot.crypto-vision.com" \
  -p 5444:5444 \
  crypto-robot

# Or for local development host
cd /opt/crypto-robot/hosts/crypto-robot.local
docker run -d --name crypto-robot-crypto-robot.local-manual \
  -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="crypto-robot.local" \
  -p 5000:5000 \
  crypto-robot
```

---

## Security Model

### Security Layers

#### 1. **No Plain Text Certificates on Disk**
- Certificates stored as environment variable strings
- Never written to EC2 filesystem as files
- Only exist as files inside secure container

#### 2. **Secure File Permissions**
```bash
# EC2 .env file
chmod 600 /opt/crypto-robot/app/.env
chown ec2-user:ec2-user /opt/crypto-robot/app/.env

# Container certificate files (runtime)
chmod 600 /opt/crypto-robot/certificates/*/cert.pem
chmod 600 /opt/crypto-robot/certificates/*/key.pem
chown crypto-robot:crypto-robot /opt/crypto-robot/certificates/
```

#### 3. **Environment Isolation**
- Each hostname has separate GitHub environment
- Environment-specific secrets (ENV_CONTENT)
- No cross-environment certificate access

#### 4. **Container Security**
- Non-root user (crypto-robot)
- Isolated filesystem
- Certificates only exist in container memory/filesystem

### Security Verification Commands

#### Check EC2 File Permissions
```bash
# SSH to EC2
ssh -i web-crypto-robot-key.pem ec2-user@<instance-ip>

# Check .env file
ls -la /opt/crypto-robot/app/.env
# Should show: -rw------- 1 ec2-user ec2-user

# Verify no certificate files on host
find /opt/crypto-robot -name "*.pem" -type f
# Should return empty (no certificate files on host)
```

#### Check Container Certificate Files
```bash
# Check running container
docker exec crypto-robot-app ls -la /opt/crypto-robot/certificates/

# Check certificate content
docker exec crypto-robot-app cat /opt/crypto-robot/certificates/jack.crypto-robot-itechsource.com/cert.pem
```

---

## Multi-Host Deployment on Single EC2

### Architecture Benefits

✅ **Host Isolation**: Each hostname has its own directory and .env file  
✅ **Container Separation**: Containers named by hostname (crypto-robot-<hostname>-app)  
✅ **Port Management**: Different ports for different hosts  
✅ **Independent Deployment**: Deploy/update hosts independently  
✅ **Environment Isolation**: Each host uses its own GitHub environment secrets  

### Directory Structure for Multiple Hosts

```
/opt/crypto-robot/
├── hosts/
│   ├── crypto-robot.local/
│   │   └── app/.env                 # Local development config
│   ├── jack_robot.crypto-vision.com/
│   │   └── app/.env                 # Jack's production config
│   ├── its_robot.crypto-vision.com/
│   │   └── app/.env                 # ITS production config
│   ├── staging_robot.crypto-vision.com/
│   │   └── app/.env                 # Staging config
│   └── custom_robot.crypto-vision.com/
│       └── app/.env                 # Custom host config
└── shared/
    ├── data/                        # Shared application data
    ├── logs/                        # Shared logs
    └── backups/                     # Shared backups
```

### Container Naming Convention

| Host | Robot Container | WebApp Container |
|------|----------------|------------------|
| crypto-robot.local | crypto-robot-crypto-robot.local-app | crypto-robot-crypto-robot.local-webapp |
| jack_robot.crypto-vision.com | crypto-robot-jack_robot.crypto-vision.com-app | crypto-robot-jack_robot.crypto-vision.com-webapp |
| its_robot.crypto-vision.com | crypto-robot-its_robot.crypto-vision.com-app | crypto-robot-its_robot.crypto-vision.com-webapp |
| staging_robot.crypto-vision.com | crypto-robot-staging_robot.crypto-vision.com-app | crypto-robot-staging_robot.crypto-vision.com-webapp |

### Port Allocation Strategy

| Host | Robot Port | WebApp Port | Purpose |
|------|------------|-------------|---------|
| crypto-robot.local | 5000 | 5002 | Local development |
| jack_robot.crypto-vision.com | 5443 | 5001 | Jack's production HTTPS |
| its_robot.crypto-vision.com | 5444 | 5003 | ITS production HTTPS |
| staging_robot.crypto-vision.com | 5445 | 5004 | Staging environment |
| custom_robot.crypto-vision.com | 5446 | 5005 | Custom deployment |

### Deployment Commands for Multiple Hosts

#### Deploy Jack's Production Host
```bash
# GitHub Actions workflow
environment: jack_robot.crypto-vision.com
init_env: true
execute_command: update-robot-image,start-robot,start-webapp
```

#### Deploy ITS Production Host
```bash
# GitHub Actions workflow
environment: its_robot.crypto-vision.com
init_env: true
execute_command: update-robot-image,start-robot,start-webapp
```

#### Deploy Local Development Host
```bash
# GitHub Actions workflow
environment: crypto-robot.local
init_env: true
execute_command: update-robot-image,start-robot,start-webapp
```

#### Deploy Multiple Hosts Simultaneously
```bash
# Run workflow multiple times with different environments
# Workflow 1:
environment: jack_robot.crypto-vision.com
execute_command: update-robot-image,start-robot,start-webapp

# Workflow 2:
environment: its_robot.crypto-vision.com
execute_command: update-robot-image,start-robot,start-webapp

# Workflow 3:
environment: crypto-robot.local
execute_command: update-robot-image,start-robot,start-webapp
```

### Managing Multiple Hosts

#### List All Running Containers
```bash
# SSH to EC2
ssh -i web-crypto-robot-key.pem ec2-user@<instance-ip>

# List all crypto-robot containers
docker ps --filter 'name=crypto-robot' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Expected output:
# NAMES                                           STATUS          PORTS
# crypto-robot-jack_robot.crypto-vision.com-app         Up 2 hours      0.0.0.0:5443->5443/tcp
# crypto-robot-jack_robot.crypto-vision.com-webapp      Up 2 hours      0.0.0.0:5001->5000/tcp
# crypto-robot-its_robot.crypto-vision.com-app          Up 2 hours      0.0.0.0:5444->5444/tcp
# crypto-robot-its_robot.crypto-vision.com-webapp       Up 2 hours      0.0.0.0:5003->5000/tcp
# crypto-robot-crypto-robot.local-app                   Up 1 hour       0.0.0.0:5000->5000/tcp
# crypto-robot-crypto-robot.local-webapp                Up 1 hour       0.0.0.0:5002->5000/tcp
```

#### Stop Specific Host
```bash
# Stop all containers for Jack's production host
docker stop $(docker ps -q --filter 'name=crypto-robot-jack_robot.crypto-vision.com')
docker rm $(docker ps -aq --filter 'name=crypto-robot-jack_robot.crypto-vision.com')

# Stop all containers for ITS production host
docker stop $(docker ps -q --filter 'name=crypto-robot-its_robot.crypto-vision.com')
docker rm $(docker ps -aq --filter 'name=crypto-robot-its_robot.crypto-vision.com')
```

#### Check Host-Specific Logs
```bash
# Jack's production host logs
docker logs crypto-robot-jack_robot.crypto-vision.com-app

# ITS production host logs
docker logs crypto-robot-its_robot.crypto-vision.com-app

# Local development host logs
docker logs crypto-robot-crypto-robot.local-app
```

---

## Troubleshooting File Locations

### Common Issues and Checks

#### 1. **Missing .env File on EC2 (Multi-Host)**
```bash
# Check if host-specific file exists
ls -la /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env
ls -la /opt/crypto-robot/hosts/crypto-robot.local/app/.env

# Check all host directories
find /opt/crypto-robot/hosts -name ".env" -type f

# Check GitHub Actions logs for init_env step
# Verify ENV_CONTENT secret exists in specific GitHub environment

# Manual recreation from secret for specific host
mkdir -p /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app
echo "$ENV_CONTENT_BASE64" | base64 -d > /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env
chmod 600 /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env
```

#### 2. **Docker Command Fails (Multi-Host)**
```bash
# Check working directory for specific host
pwd
# Should be: /opt/crypto-robot/hosts/<hostname>

# Check host-specific .env file exists
ls -la app/.env

# Test base64 encoding for specific host
base64 -w 0 app/.env | head -c 50
# Should show base64 encoded content

# Check Docker command manually for specific host
cd /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com
docker run --rm -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="jack.crypto-robot-itechsource.com" \
  crypto-robot status
```

#### 3. **Certificate Extraction Fails (Multi-Host)**
```bash
# Check container logs for specific host
docker logs crypto-robot-jack.crypto-robot-itechsource.com-app

# Look for certificate extraction messages:
# "[ENTRYPOINT] Setting up certificates from .env configuration..."
# "[ENTRYPOINT] Extracting certificate content from environment variables"
# "[ENTRYPOINT] Certificate file created and validated"

# Check if certificates were created for specific host
docker exec crypto-robot-jack.crypto-robot-itechsource.com-app ls -la /opt/crypto-robot/certificates/

# Check certificates for local development host
docker exec crypto-robot-crypto-robot.local-app ls -la /opt/crypto-robot/certificates/
```

#### 4. **Environment Variable Issues (Multi-Host)**
```bash
# Check .env file content for specific host (without showing secrets)
grep -E "^(FLASK_|HOSTNAME|SSL_)" /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env | grep -v "CONTENT"

# Should show for production:
# FLASK_PORT=5443
# FLASK_PROTOCOL=https
# HOSTNAME=jack.crypto-robot-itechsource.com

# Check for local development host
grep -E "^(FLASK_|HOSTNAME|SSL_)" /opt/crypto-robot/hosts/crypto-robot.local/app/.env | grep -v "CONTENT"

# Should show for local:
# FLASK_PORT=5000
# FLASK_PROTOCOL=http
# HOSTNAME=crypto-robot.local

# Check if SSL content exists for specific host (without showing content)
grep -c "SSL_CERT_CONTENT" /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env
grep -c "SSL_KEY_CONTENT" /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env
# Both should return: 1
```

### File Location Quick Reference

| Component | EC2 Location (Multi-Host) | Container Location | Purpose |
|-----------|---------------------------|-------------------|---------|
| .env file | `/opt/crypto-robot/hosts/<hostname>/app/.env` | `/opt/crypto-robot/app/.env` | Host-specific configuration |
| Certificate | N/A (in .env as string) | `/opt/crypto-robot/certificates/<hostname>/cert.pem` | SSL cert |
| Private Key | N/A (in .env as string) | `/opt/crypto-robot/certificates/<hostname>/key.pem` | SSL key |
| App Code | N/A | `/opt/crypto-robot/app/` | Application |
| Shared Logs | `/opt/crypto-robot/logs/` | `/opt/crypto-robot/logs/` | Shared application logs |

### Emergency Recovery

#### Recreate .env File (Multi-Host)
```bash
# If .env file is lost, recreate from GitHub environment secret
# 1. Get ENV_CONTENT from specific GitHub environment
# 2. SSH to EC2
ssh -i web-crypto-robot-key.pem ec2-user@<instance-ip>

# 3. Recreate file for specific host (replace BASE64_CONTENT with actual content)
mkdir -p /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app
echo "BASE64_CONTENT" | base64 -d > /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env
chmod 600 /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com/app/.env

# 4. Test Docker command for specific host
cd /opt/crypto-robot/hosts/jack.crypto-robot-itechsource.com
docker run --rm -e ENV_CONTENT="$(base64 -w 0 app/.env)" \
  -e CERTIFICATE="jack.crypto-robot-itechsource.com" \
  crypto-robot status

# For multiple hosts, repeat for each:
mkdir -p /opt/crypto-robot/hosts/crypto-robot.local/app
echo "LOCAL_BASE64_CONTENT" | base64 -d > /opt/crypto-robot/hosts/crypto-robot.local/app/.env
chmod 600 /opt/crypto-robot/hosts/crypto-robot.local/app/.env
```

---

*This document provides the complete file system and certificate architecture for the Crypto Robot system. The system has been migrated from Docker-based deployment to direct Python execution.*