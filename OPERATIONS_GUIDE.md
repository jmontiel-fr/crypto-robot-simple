# Operations Guide - Crypto Robot Management

## Overview

This guide provides practical SSH commands and Docker operations for managing the crypto robot application on AWS EC2 instances. Use these commands for direct server management, troubleshooting, and manual operations.

## SSH Access to Robot Instance

### Basic SSH Connection
```bash
# SSH to the robot instance (web-crypto-robot-instance)
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP>

# Example with actual IP
ssh -i web-crypto-robot-key.pem ec2-user@54.123.45.67
```

### SSH with Command Execution (Piping)
```bash
# Execute single command
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "command"

# Execute multiple commands
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "command1 && command2 && command3"

# Pipe commands to SSH for execution
echo "docker ps" | ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "bash"

# Pipe multiple commands
cat << 'EOF' | ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "bash"
docker ps
docker images
df -h
EOF

# Execute script remotely
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "bash -s" < local_script.sh
```

## Basic System Commands

### System Status
```bash
# Check system status
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "uptime && free -h && df -h"

# Check running processes
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "ps aux | grep -E 'docker|python|crypto'"

# Check system logs
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "sudo journalctl -n 50"

# Monitor system resources
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "top -bn1 | head -20"
```

### File Operations
```bash
# List crypto-robot directory
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "ls -la /opt/crypto-robot/"

# Check environment file (be careful with sensitive data)
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "head -5 /opt/crypto-robot/.env"

# Check database files
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "ls -la /opt/crypto-robot/database/"

# Check disk usage
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "du -sh /opt/crypto-robot/*"
```

## Docker Commands

### Docker Status and Information
```bash
# Check Docker status
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker --version && docker info"

# List all containers
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker ps -a"

# List running containers only
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker ps"

# List crypto-robot containers specifically
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker ps --filter 'name=crypto-robot'"

# List Docker images
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker images"

# Check Docker system usage
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker system df"
```### C
ontainer Management
```bash
# Start crypto-robot containers
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "
cd /opt/crypto-robot && \
docker run -d --name crypto-robot-app \
  -e ENV_CONTENT=\"\$(base64 -w 0 .env)\" \
  -e CERTIFICATE=\"production\" \
  -e MODE=\"robot\" \
  -v \$(pwd)/database:/opt/crypto-robot/database \
  --restart unless-stopped \
  -p 5443:5443 \
  jmontiel/crypto-robot:latest
"

# Start webapp container
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "
cd /opt/crypto-robot && \
docker run -d --name crypto-robot-webapp \
  -e ENV_CONTENT=\"\$(base64 -w 0 .env)\" \
  -e CERTIFICATE=\"production\" \
  -e MODE=\"webapp\" \
  -v \$(pwd)/database:/opt/crypto-robot/database \
  --restart unless-stopped \
  -p 5000:5000 \
  jmontiel/crypto-robot:latest
"

# Stop containers
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker stop crypto-robot-app crypto-robot-webapp"

# Remove containers
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker rm crypto-robot-app crypto-robot-webapp"

# Restart containers
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker restart crypto-robot-app crypto-robot-webapp"
```

### Container Logs and Monitoring
```bash
# View robot container logs
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker logs crypto-robot-app"

# Follow robot container logs (live)
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker logs -f crypto-robot-app"

# View webapp container logs
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker logs crypto-robot-webapp"

# View last 50 lines of logs
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker logs --tail 50 crypto-robot-app"

# Monitor container resource usage
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker stats --no-stream"

# Search for errors in logs
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker logs crypto-robot-app 2>&1 | grep -i error"
```

## Execute Commands in Containers

### Access Container Shell
```bash
# Execute bash in robot container
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec -it crypto-robot-app bash"

# Execute bash in webapp container
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec -it crypto-robot-webapp bash"

# Execute command without interactive shell
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app ls -la /opt/crypto-robot"
```

### Python Commands in Containers
```bash
# Execute Python command in robot container
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app python -c 'print(\"Hello from robot\")'"

# Check Python version
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app python --version"

# Run Python script
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app python /opt/crypto-robot/app/main.py --help"

# Check application status
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app python -c '
import sys
sys.path.append(\"/opt/crypto-robot/app\")
try:
    from robot.status import get_status
    print(get_status())
except Exception as e:
    print(f\"Error: {e}\")
'"
```

### Database Operations
```bash
# Access SQLite database
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec -it crypto-robot-app sqlite3 /opt/crypto-robot/database/crypto_robot.db"

# List database tables
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app sqlite3 /opt/crypto-robot/database/crypto_robot.db '.tables'"

# Query recent trades
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app sqlite3 /opt/crypto-robot/database/crypto_robot.db 'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;'"

# Backup database
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker exec crypto-robot-app sqlite3 /opt/crypto-robot/database/crypto_robot.db '.backup /tmp/backup.db'"
```

## Application Health Checks

### Test Application Endpoints
```bash
# Test webapp health
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "curl -k https://localhost:5443/health"

# Test webapp accessibility
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "curl -k -I https://localhost:5443/"

# Check if ports are listening
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "netstat -tulpn | grep -E '(5000|5443)'"

# Test external API connectivity
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "curl -s https://api.binance.com/api/v3/ping"
```

## Maintenance Operations

### Update Application
```bash
# Pull latest image and restart containers
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "
docker stop crypto-robot-app crypto-robot-webapp
docker rm crypto-robot-app crypto-robot-webapp
docker pull jmontiel/crypto-robot:latest
cd /opt/crypto-robot
# Restart containers with new image
docker run -d --name crypto-robot-app \
  -e ENV_CONTENT=\"\$(base64 -w 0 .env)\" \
  -e CERTIFICATE=\"production\" \
  -e MODE=\"robot\" \
  -v \$(pwd)/database:/opt/crypto-robot/database \
  --restart unless-stopped \
  -p 5443:5443 \
  jmontiel/crypto-robot:latest
"
```

### Clean Up Docker Resources
```bash
# Clean up unused Docker resources
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker system prune -f"

# Remove unused images
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker image prune -a -f"

# Remove unused volumes
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker volume prune -f"
```

## Quick Reference Commands

### One-liner Status Check
```bash
# Complete system status
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "
echo '=== System Status ==='
uptime
echo '=== Docker Containers ==='
docker ps --filter 'name=crypto-robot'
echo '=== Application Health ==='
curl -k -s https://localhost:5443/health || echo 'Health check failed'
echo '=== Database Status ==='
ls -lh /opt/crypto-robot/database/crypto_robot.db
"
```

### Emergency Operations
```bash
# Emergency stop all crypto-robot containers
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker stop \$(docker ps -q --filter 'name=crypto-robot')"

# Emergency restart
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "docker restart \$(docker ps -aq --filter 'name=crypto-robot')"
```

## Piping Examples for Automation

### Execute Multiple Commands via Pipe
```bash
# Pipe system check commands
cat << 'EOF' | ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "bash"
echo "=== System Check Started ==="
uptime
docker ps --filter 'name=crypto-robot'
df -h /opt/crypto-robot
echo "=== System Check Completed ==="
EOF

# Pipe maintenance commands
cat << 'EOF' | ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "bash"
echo "Starting maintenance..."
docker logs crypto-robot-app --tail 20
docker system df
docker system prune -f
echo "Maintenance completed"
EOF
```

### Create and Execute Remote Scripts
```bash
# Create maintenance script locally and execute remotely
cat > maintenance.sh << 'EOF'
#!/bin/bash
echo "Crypto Robot Maintenance - $(date)"
docker ps --filter 'name=crypto-robot'
docker logs crypto-robot-app --tail 10
docker system df
echo "Maintenance completed"
EOF

# Execute the script remotely
ssh -i web-crypto-robot-key.pem ec2-user@<INSTANCE_IP> "bash -s" < maintenance.sh
```

## Notes

- Replace `<INSTANCE_IP>` with the actual IP address of your EC2 instance
- Ensure the SSH key file `web-crypto-robot-key.pem` has correct permissions (400)
- Always verify container names match your actual deployment
- Use caution when viewing environment files as they contain sensitive information
- Monitor resource usage regularly to prevent system overload