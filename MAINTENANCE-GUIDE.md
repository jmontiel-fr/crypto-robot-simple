# Crypto Robot - Maintenance and Version Update Guide

## Overview

This guide provides comprehensive procedures for maintaining and updating the Crypto Robot system deployed with direct Python execution. It covers routine maintenance tasks, version updates, troubleshooting, and system monitoring.

## Table of Contents

1. [Routine Maintenance](#routine-maintenance)
2. [Version Updates](#version-updates)
3. [Rollback Procedures](#rollback-procedures)
4. [Health Monitoring](#health-monitoring)
5. [Backup and Recovery](#backup-and-recovery)
6. [Performance Optimization](#performance-optimization)
7. [Security Maintenance](#security-maintenance)
8. [Troubleshooting Guide](#troubleshooting-guide)

## Routine Maintenance

### Daily Tasks

#### 1. System Health Check
```bash
# Run comprehensive health check
cd /opt/crypto-robot
./scripts/health-check.sh --quick

# Check service status
./scripts/service-control.sh status

# Monitor resource usage
df -h
free -h
```

#### 2. Log Review
```bash
# Check for errors in recent logs
grep -i error /opt/crypto-robot/logs/*.log | tail -20

# Check application logs
./scripts/service-control.sh logs robot 50
./scripts/service-control.sh logs webapp 50

# Check system logs
journalctl -u crypto-robot --since "24 hours ago" | grep -i error
journalctl -u crypto-webapp --since "24 hours ago" | grep -i error
```

#### 3. Process Monitoring
```bash
# Verify processes are running
ps aux | grep -E 'python.*(main|app)\.py'

# Check PID files are valid
for pid_file in /opt/crypto-robot/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null; then
            echo "✅ $(basename "$pid_file"): PID $pid is running"
        else
            echo "❌ $(basename "$pid_file"): PID $pid is not running"
        fi
    fi
done
```

### Weekly Tasks

#### 1. Log Rotation and Cleanup
```bash
# Manual log rotation if needed
sudo logrotate -f /etc/logrotate.d/crypto-robot

# Clean old log files (older than 30 days)
find /opt/crypto-robot/logs -name "*.log" -mtime +30 -delete

# Clean old backup files
find /opt/crypto-robot/backups -name "*.backup.*" -mtime +7 -delete
```

#### 2. Database Maintenance
```bash
# Backup database
cp /opt/crypto-robot/database/cryptorobot.db \
   /opt/crypto-robot/backups/cryptorobot-$(date +%Y%m%d).db

# Check database integrity (SQLite)
sqlite3 /opt/crypto-robot/database/cryptorobot.db "PRAGMA integrity_check;"

# Optimize database
sqlite3 /opt/crypto-robot/database/cryptorobot.db "VACUUM;"
```

#### 3. Security Review
```bash
# Check file permissions
./scripts/health-check.sh --quick | grep -i permission

# Review API key configuration
./scripts/manage-env.sh show | grep -E "(API_KEY|SECRET_KEY)"

# Check certificate expiration
./scripts/configure-certificates.sh list
```

### Monthly Tasks

#### 1. Dependency Updates
```bash
# Check for outdated packages
source /opt/crypto-robot/venv/bin/activate
pip list --outdated

# Update packages (test in staging first)
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

#### 2. System Updates
```bash
# Update system packages (Amazon Linux)
sudo yum update -y

# Update system packages (Ubuntu)
sudo apt update && sudo apt upgrade -y
```

#### 3. Certificate Renewal
```bash
# Check certificate expiration
./scripts/configure-certificates.sh validate your-hostname.com

# Renew certificates if needed (process depends on your CA)
# Update certificates
./scripts/configure-certificates.sh setup your-hostname.com
```

## Version Updates

### Preparation

#### 1. Pre-Update Checklist
```bash
# Create full backup
./scripts/manage-env.sh backup
cp -r /opt/crypto-robot/database /opt/crypto-robot/backups/database-$(date +%Y%m%d)

# Document current version
cd /opt/crypto-robot
git log --oneline -1 > /opt/crypto-robot/backups/version-$(date +%Y%m%d).txt

# Check system health
./scripts/health-check.sh --full
```

#### 2. Maintenance Window Planning
- Schedule during low trading activity periods
- Notify users of planned downtime
- Prepare rollback plan
- Test update in staging environment first

### Update Process

#### 1. Automated Update (GitHub Actions)
```bash
# Use GitHub Actions workflow:
# 1. Go to Actions → control-robot-aws
# 2. Select environment
# 3. Commands: stop-robot,stop-webapp,update-code,setup-environment,start-robot,start-webapp
# 4. Initialize environment: false (unless config changes needed)
```

#### 2. Manual Update Process
```bash
# Step 1: Stop services
sudo ./scripts/service-control.sh stop-all

# Step 2: Backup current state
cp -r /opt/crypto-robot /opt/crypto-robot-backup-$(date +%Y%m%d)

# Step 3: Update code
cd /opt/crypto-robot
git fetch origin
git checkout main
git pull origin main

# Step 4: Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Step 5: Run health check
./scripts/health-check.sh --no-api

# Step 6: Start services
sudo ./scripts/service-control.sh start-all

# Step 7: Verify deployment
sleep 30
./scripts/health-check.sh --full
```

### Post-Update Verification

#### 1. Functional Testing
```bash
# Check service status
./scripts/service-control.sh status

# Test web interface (if applicable)
curl -k https://your-hostname.com:5000/health || curl http://your-hostname.com:5000/health

# Check API connectivity
./scripts/health-check.sh --api-only

# Monitor logs for errors
./scripts/service-control.sh logs robot 20
./scripts/service-control.sh logs webapp 20
```

#### 2. Performance Verification
```bash
# Check resource usage
htop
df -h
free -h

# Monitor for memory leaks
ps aux | grep python | awk '{print $2, $3, $4, $11}'

# Check response times
time curl -k https://your-hostname.com:5000/health
```

## Rollback Procedures

### Immediate Rollback (Critical Issues)

#### 1. Service-Level Rollback
```bash
# Stop current services
sudo ./scripts/service-control.sh stop-all

# Restore from backup
sudo rm -rf /opt/crypto-robot
sudo mv /opt/crypto-robot-backup-$(date +%Y%m%d) /opt/crypto-robot
sudo chown -R ec2-user:ec2-user /opt/crypto-robot

# Start services
sudo ./scripts/service-control.sh start-all
```

#### 2. Git-Based Rollback
```bash
# Stop services
sudo ./scripts/service-control.sh stop-all

# Rollback to previous commit
cd /opt/crypto-robot
git log --oneline -10  # Find the commit to rollback to
git checkout <previous-commit-hash>

# Restore dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Start services
sudo ./scripts/service-control.sh start-all
```

### Database Rollback

#### 1. Restore Database Backup
```bash
# Stop services
sudo ./scripts/service-control.sh stop-all

# Restore database
cp /opt/crypto-robot/backups/cryptorobot-$(date +%Y%m%d).db \
   /opt/crypto-robot/database/cryptorobot.db

# Verify database integrity
sqlite3 /opt/crypto-robot/database/cryptorobot.db "PRAGMA integrity_check;"

# Start services
sudo ./scripts/service-control.sh start-all
```

### Configuration Rollback

#### 1. Restore Environment Configuration
```bash
# List available backups
ls -la /opt/crypto-robot/backups/env/

# Restore configuration
./scripts/manage-env.sh restore /opt/crypto-robot/backups/env/.env.YYYYMMDD-HHMMSS

# Restart services
sudo ./scripts/service-control.sh restart-all
```

## Health Monitoring

### Automated Monitoring Setup

#### 1. Cron Jobs for Health Checks
```bash
# Add to crontab (crontab -e)
# Health check every 15 minutes
*/15 * * * * /opt/crypto-robot/scripts/health-check.sh --quick >> /opt/crypto-robot/logs/health-check.log 2>&1

# Daily full health check
0 6 * * * /opt/crypto-robot/scripts/health-check.sh --full >> /opt/crypto-robot/logs/daily-health.log 2>&1

# Weekly maintenance
0 2 * * 0 /opt/crypto-robot/scripts/weekly-maintenance.sh >> /opt/crypto-robot/logs/maintenance.log 2>&1
```

#### 2. Create Weekly Maintenance Script
```bash
cat > /opt/crypto-robot/scripts/weekly-maintenance.sh << 'EOF'
#!/bin/bash
# Weekly maintenance script

echo "$(date): Starting weekly maintenance"

# Backup database
cp /opt/crypto-robot/database/cryptorobot.db \
   /opt/crypto-robot/backups/cryptorobot-$(date +%Y%m%d).db

# Clean old logs
find /opt/crypto-robot/logs -name "*.log" -mtime +30 -delete

# Clean old backups
find /opt/crypto-robot/backups -name "*.backup.*" -mtime +7 -delete

# Database optimization
sqlite3 /opt/crypto-robot/database/cryptorobot.db "VACUUM;"

# Health check
/opt/crypto-robot/scripts/health-check.sh --full

echo "$(date): Weekly maintenance completed"
EOF

chmod +x /opt/crypto-robot/scripts/weekly-maintenance.sh
```

### Monitoring Metrics

#### 1. Key Performance Indicators
- **Service Uptime**: Services should be running 99.9% of the time
- **Response Time**: Web interface should respond within 2 seconds
- **Memory Usage**: Should not exceed 80% of available memory
- **Disk Usage**: Should not exceed 85% of available space
- **API Success Rate**: Binance API calls should succeed >95% of the time

#### 2. Alert Thresholds
```bash
# Create monitoring script
cat > /opt/crypto-robot/scripts/monitor-alerts.sh << 'EOF'
#!/bin/bash
# Monitoring and alerting script

# Check disk usage
DISK_USAGE=$(df /opt/crypto-robot | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "ALERT: Disk usage is ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEM_USAGE" -gt 80 ]; then
    echo "ALERT: Memory usage is ${MEM_USAGE}%"
fi

# Check service status
if ! systemctl is-active --quiet crypto-robot; then
    echo "ALERT: Robot service is not running"
fi

if ! systemctl is-active --quiet crypto-webapp; then
    echo "ALERT: WebApp service is not running"
fi
EOF

chmod +x /opt/crypto-robot/scripts/monitor-alerts.sh
```

## Backup and Recovery

### Backup Strategy

#### 1. Automated Backups
```bash
# Create backup script
cat > /opt/crypto-robot/scripts/backup.sh << 'EOF'
#!/bin/bash
# Automated backup script

BACKUP_DIR="/opt/crypto-robot/backups"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
cp /opt/crypto-robot/database/cryptorobot.db "$BACKUP_DIR/database-$DATE.db"

# Backup configuration
cp /opt/crypto-robot/.env "$BACKUP_DIR/env-$DATE.backup"

# Backup certificates
tar -czf "$BACKUP_DIR/certificates-$DATE.tar.gz" /opt/crypto-robot/certificates/

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.backup" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/crypto-robot/scripts/backup.sh

# Add to crontab for daily backups
# 0 3 * * * /opt/crypto-robot/scripts/backup.sh >> /opt/crypto-robot/logs/backup.log 2>&1
```

#### 2. Recovery Procedures
```bash
# List available backups
ls -la /opt/crypto-robot/backups/

# Restore database
cp /opt/crypto-robot/backups/database-YYYYMMDD-HHMMSS.db \
   /opt/crypto-robot/database/cryptorobot.db

# Restore configuration
cp /opt/crypto-robot/backups/env-YYYYMMDD-HHMMSS.backup \
   /opt/crypto-robot/.env

# Restore certificates
tar -xzf /opt/crypto-robot/backups/certificates-YYYYMMDD-HHMMSS.tar.gz -C /
```

## Performance Optimization

### Resource Monitoring

#### 1. System Resources
```bash
# Monitor CPU usage
top -p $(pgrep -f "python.*(main|app)\.py" | tr '\n' ',' | sed 's/,$//')

# Monitor memory usage
ps aux | grep python | awk '{print $2, $3, $4, $11}' | sort -k3 -nr

# Monitor disk I/O
iotop -p $(pgrep -f "python.*(main|app)\.py" | tr '\n' ',' | sed 's/,$//')
```

#### 2. Application Performance
```bash
# Check response times
time curl -k https://your-hostname.com:5000/health

# Monitor database performance
sqlite3 /opt/crypto-robot/database/cryptorobot.db ".timer on" "SELECT COUNT(*) FROM trades;"

# Check log file sizes
du -sh /opt/crypto-robot/logs/*.log
```

### Optimization Techniques

#### 1. Database Optimization
```bash
# Regular VACUUM operations
sqlite3 /opt/crypto-robot/database/cryptorobot.db "VACUUM;"

# Analyze database statistics
sqlite3 /opt/crypto-robot/database/cryptorobot.db "ANALYZE;"

# Check database size
du -sh /opt/crypto-robot/database/cryptorobot.db
```

#### 2. Log Management
```bash
# Implement log rotation
sudo tee /etc/logrotate.d/crypto-robot << EOF
/opt/crypto-robot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ec2-user ec2-user
    postrotate
        systemctl reload crypto-robot crypto-webapp
    endscript
}
EOF
```

## Security Maintenance

### Regular Security Tasks

#### 1. API Key Rotation
```bash
# Generate new API keys in Binance
# Update GitHub secrets
# Deploy new keys
export HOSTNAME="your-hostname.com"
export YOUR_HOSTNAME_COM_KEYS='{"BINANCE_API_KEY":"new_key","BINANCE_SECRET_KEY":"new_secret"}'
./scripts/inject-api-keys.sh

# Restart services
sudo ./scripts/service-control.sh restart-all
```

#### 2. Certificate Renewal
```bash
# Check certificate expiration
./scripts/configure-certificates.sh validate your-hostname.com

# Renew certificates (process varies by CA)
# Update certificates
./scripts/configure-certificates.sh setup your-hostname.com

# Restart services
sudo ./scripts/service-control.sh restart webapp
```

#### 3. Security Audits
```bash
# Check file permissions
find /opt/crypto-robot -type f -name "*.py" ! -perm 644 -ls
find /opt/crypto-robot -type f -name ".env*" ! -perm 600 -ls

# Check for sensitive data in logs
grep -r "api.*key\|secret\|password" /opt/crypto-robot/logs/ || echo "No sensitive data found"

# Review network connections
netstat -tulnp | grep python
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status crypto-robot
sudo systemctl status crypto-webapp

# Check logs
journalctl -u crypto-robot -n 50
journalctl -u crypto-webapp -n 50

# Check configuration
./scripts/manage-env.sh validate

# Check permissions
ls -la /opt/crypto-robot/.env
ls -la /opt/crypto-robot/scripts/
```

#### 2. High Memory Usage
```bash
# Identify memory-consuming processes
ps aux | grep python | sort -k4 -nr

# Check for memory leaks
# Monitor memory usage over time
while true; do
    ps aux | grep python | awk '{print $4}' | head -1
    sleep 60
done

# Restart services if needed
sudo ./scripts/service-control.sh restart-all
```

#### 3. Database Issues
```bash
# Check database integrity
sqlite3 /opt/crypto-robot/database/cryptorobot.db "PRAGMA integrity_check;"

# Check database locks
lsof /opt/crypto-robot/database/cryptorobot.db

# Backup and recreate if corrupted
cp /opt/crypto-robot/database/cryptorobot.db /opt/crypto-robot/database/cryptorobot.db.corrupt
cp /opt/crypto-robot/backups/database-latest.db /opt/crypto-robot/database/cryptorobot.db
```

#### 4. API Connection Issues
```bash
# Test API connectivity
./scripts/health-check.sh --api-only

# Check network connectivity
ping api.binance.com
curl -s https://api.binance.com/api/v3/ping

# Verify API keys
./scripts/manage-env.sh show | grep -E "(API_KEY|SECRET_KEY)"
```

#### 5. Certificate Issues
```bash
# Validate certificates
./scripts/configure-certificates.sh validate your-hostname.com

# Test SSL configuration
openssl s_client -connect your-hostname.com:5000 -servername your-hostname.com

# Check certificate expiration
openssl x509 -enddate -noout -in /opt/crypto-robot/certificates/your-hostname.com/cert.pem
```

### Emergency Procedures

#### 1. Complete System Recovery
```bash
# Stop all services
sudo ./scripts/service-control.sh stop-all

# Restore from backup
sudo rm -rf /opt/crypto-robot
sudo tar -xzf /path/to/crypto-robot-backup.tar.gz -C /opt/

# Fix permissions
sudo chown -R ec2-user:ec2-user /opt/crypto-robot

# Start services
sudo ./scripts/service-control.sh start-all
```

#### 2. Emergency Shutdown
```bash
# Immediate shutdown of all services
sudo pkill -f "python.*(main|app)\.py"
sudo systemctl stop crypto-robot crypto-webapp

# Verify shutdown
ps aux | grep python
```

### Support Escalation

#### 1. Information to Collect
- System logs: `journalctl -u crypto-robot -u crypto-webapp --since "1 hour ago"`
- Application logs: Recent entries from `/opt/crypto-robot/logs/`
- System status: Output of `./scripts/health-check.sh --full`
- Configuration: Sanitized version of `.env` file (remove sensitive data)
- Resource usage: `top`, `df -h`, `free -h` output

#### 2. Contact Information
- Create GitHub issue with collected information
- Include steps to reproduce the problem
- Specify environment and version information

---

*This maintenance guide ensures the reliable operation of your Crypto Robot deployment. Regular adherence to these procedures will minimize downtime and maintain optimal performance.*