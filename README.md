# Crypto Robot - Direct Python Deployment

A sophisticated cryptocurrency trading robot with web interface, now deployed using direct Python execution for simplified infrastructure and improved performance.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- Linux environment (Amazon Linux 2 or Ubuntu 20.04+)

### Installation
```bash
# Clone repository
git clone https://github.com/your-repo/crypto-robot.git
cd crypto-robot

# Setup Python environment
chmod +x scripts/setup-python-env.sh
./scripts/setup-python-env.sh

# Configure environment
cp robot/.env.template .env
# Edit .env with your configuration

# Start applications
./scripts/start-robot-direct.sh
./scripts/start-webapp-direct.sh
```

## 📋 Features

- **Multi-Strategy Trading**: Daily rebalance with volatility optimization
- **Web Interface**: Real-time monitoring and control dashboard
- **Direct Python Deployment**: Simplified infrastructure without Docker
- **Automated Deployment**: GitHub Actions integration
- **Systemd Integration**: Reliable service management
- **SSL/HTTPS Support**: Secure web interface
- **Health Monitoring**: Comprehensive health checks and monitoring
- **API Key Management**: Secure GitHub secrets integration

## 🏗️ Architecture

### Deployment Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub        │    │   EC2 Instance   │    │   Binance API   │
│   Actions       │───▶│   Python Apps    │───▶│   Trading       │
│   Workflows     │    │   Systemd Svcs   │    │   Data          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Application Components
- **Trading Robot** (`main.py`): Core trading logic and strategy execution
- **Web Application** (`app.py`): Flask-based web interface with real-time updates
- **Service Management**: Systemd services for reliability and auto-restart
- **Health Monitoring**: Automated health checks and alerting

## 📖 Documentation

### Deployment Guides
- **[Python Deployment Guide](PYTHON-DEPLOYMENT-GUIDE.md)**: Complete deployment instructions
- **[Maintenance Guide](MAINTENANCE-GUIDE.md)**: Maintenance and update procedures
- **[Configuration Reference](#configuration)**: Environment variable reference

### Quick Links
- [Installation](#installation)
- [Configuration](#configuration)
- [GitHub Secrets Setup](#github-secrets-setup)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Service Management](#service-management)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## ⚙️ Configuration

### Environment Variables

#### Core Configuration
```bash
# Application Mode
FLASK_HOST=0.0.0.0                    # Web server host
FLASK_PORT=5000                       # Web server port
FLASK_PROTOCOL=http                   # Protocol (http/https)
USE_HTTPS=false                       # Enable HTTPS

# Domain Configuration
DOMAIN_NAME=crypto-robot.local        # Domain name
HOSTNAME=crypto-robot.local           # Hostname for certificates

# Database Configuration
DATABASE_TYPE=sqlite                  # Database type
DATABASE_PATH=/opt/crypto-robot/database  # Database directory
DATABASE_FILE=cryptorobot.db          # Database filename
```

#### Trading Configuration
```bash
# API Configuration (managed via GitHub secrets)
BINANCE_API_KEY=your_api_key          # Binance API key
BINANCE_SECRET_KEY=your_secret_key    # Binance secret key

# Trading Parameters
STARTING_CAPITAL=100                  # Starting capital amount
ROBOT_DRY_RUN=true                   # Dry run mode (true/false)
STRATEGY_NAME=daily_rebalance        # Trading strategy
PORTFOLIO_SIZE=15                    # Number of cryptocurrencies
```

#### SSL Configuration
```bash
# Certificate Paths (auto-configured)
SSL_CERT_PATH=/opt/crypto-robot/certificates/hostname/cert.pem
SSL_KEY_PATH=/opt/crypto-robot/certificates/hostname/key.pem

# Certificate Content (for injection)
SSL_CERT_CONTENT=""                  # Certificate content
SSL_KEY_CONTENT=""                   # Private key content
```

### Configuration Management
```bash
# Validate configuration
./scripts/manage-env.sh validate

# Update configuration
./scripts/manage-env.sh update FLASK_PORT 5000

# Show configuration (sensitive values masked)
./scripts/manage-env.sh show

# Backup configuration
./scripts/manage-env.sh backup
```

## 🔐 GitHub Secrets Setup

### Required Secrets

API keys are managed through GitHub secrets using hostname-based naming:

| Environment | Secret Name | Format |
|-------------|-------------|---------|
| crypto-robot.local | `CRYPTO_ROBOT_LOCAL_KEYS` | JSON |
| jack_robot.crypto-vision.com | `JACK_ROBOT_CRYPTO_VISION_COM_KEYS` | JSON |
| its_robot.crypto-vision.com | `ITS_ROBOT_CRYPTO_VISION_COM_KEYS` | JSON |

### Secret Format
```json
{
  "BINANCE_API_KEY": "your_actual_api_key_here",
  "BINANCE_SECRET_KEY": "your_actual_secret_key_here"
}
```

### Setup Process
1. Go to repository → Settings → Secrets and variables → Actions
2. Create new secret with hostname-based name
3. Add JSON content with your API keys
4. Deploy using GitHub Actions workflow

## 🔒 SSL Certificate Setup

### Certificate Management
```bash
# Setup certificates for hostname
./scripts/configure-certificates.sh setup your-hostname.com

# List available certificates
./scripts/configure-certificates.sh list

# Validate certificates
./scripts/configure-certificates.sh validate your-hostname.com

# Test SSL configuration
./scripts/configure-certificates.sh test your-hostname.com
```

### Certificate Sources

#### From Environment Variables
Certificates can be embedded in `.env` file:
```bash
SSL_CERT_CONTENT="-----BEGIN CERTIFICATE-----
...certificate content...
-----END CERTIFICATE-----"
```

#### From Files
```bash
# Copy from files
./scripts/configure-certificates.sh copy hostname /path/to/cert.pem /path/to/key.pem
```

## 🎛️ Service Management

### Direct Script Management
```bash
# Start services
./scripts/start-robot-direct.sh
./scripts/start-webapp-direct.sh

# Stop services
./scripts/stop-robot-direct.sh
./scripts/stop-webapp-direct.sh
```

### Systemd Service Management
```bash
# Install systemd services
sudo ./scripts/install-systemd-services.sh

# Service control
sudo ./scripts/service-control.sh start robot
sudo ./scripts/service-control.sh start webapp
sudo ./scripts/service-control.sh status
sudo ./scripts/service-control.sh logs robot 100
```

### GitHub Actions Deployment
```bash
# Available commands:
# - update-code: Update from repository
# - setup-environment: Setup Python environment
# - start-robot: Start trading robot
# - start-webapp: Start web application
# - stop-robot: Stop trading robot
# - stop-webapp: Stop web application
# - application-status: Check status
```

## 📊 Monitoring

### Health Checks
```bash
# Full health check
./scripts/health-check.sh

# Quick health check
./scripts/health-check.sh --quick

# API connectivity test
./scripts/health-check.sh --api-only
```

### Log Monitoring
```bash
# View recent logs
./scripts/service-control.sh logs robot 50
./scripts/service-control.sh logs webapp 50

# Follow logs in real-time
./scripts/service-control.sh follow robot

# Check system logs
journalctl -u crypto-robot -f
```

### Performance Monitoring
```bash
# Check resource usage
htop
df -h
free -h

# Monitor processes
ps aux | grep -E 'python.*(main|app)\.py'

# Check PID files
ls -la /opt/crypto-robot/*.pid
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status crypto-robot
sudo systemctl status crypto-webapp

# Check logs
journalctl -u crypto-robot -n 50

# Validate configuration
./scripts/manage-env.sh validate
```

#### Permission Issues
```bash
# Fix ownership
sudo chown -R ec2-user:ec2-user /opt/crypto-robot

# Fix permissions
chmod 600 .env
chmod +x scripts/*.sh
```

#### API Connection Issues
```bash
# Test API connectivity
./scripts/health-check.sh --api-only

# Check network
ping api.binance.com
curl -s https://api.binance.com/api/v3/ping
```

#### Certificate Issues
```bash
# Validate certificates
./scripts/configure-certificates.sh validate hostname

# Test SSL
openssl s_client -connect hostname:5000
```

### Debug Mode
```bash
# Enable debug mode
echo "FLASK_DEBUG=true" >> .env
echo "ROBOT_DRY_RUN=true" >> .env

# Restart services
sudo ./scripts/service-control.sh restart-all
```

## 🚀 Deployment

### Automated Deployment (Recommended)
1. Configure GitHub secrets for your environment
2. Go to Actions → control-robot-aws
3. Select environment and commands
4. Run workflow

### Manual Deployment
```bash
# Initial setup
git clone https://github.com/your-repo/crypto-robot.git
cd crypto-robot
./scripts/setup-python-env.sh

# Configure environment
cp robot/.env.template .env
# Edit .env with your settings

# Inject API keys (if configured)
export HOSTNAME="your-hostname.com"
./scripts/inject-api-keys.sh

# Start services
./scripts/start-robot-direct.sh
./scripts/start-webapp-direct.sh
```

## 📈 Performance

### Optimization Tips
- Use SSD storage for database
- Monitor memory usage regularly
- Implement log rotation
- Regular database maintenance
- Keep dependencies updated

### Resource Requirements
- **Minimum**: 2GB RAM, 10GB storage
- **Recommended**: 4GB RAM, 20GB storage
- **Network**: Stable internet connection
- **CPU**: 2+ cores recommended

## 🔄 Migration from Docker

If migrating from Docker deployment:

1. **Backup Docker data**:
```bash
docker cp crypto-robot-app:/opt/crypto-robot/database ./database-backup
```

2. **Stop Docker containers**:
```bash
docker stop crypto-robot-app crypto-robot-webapp
docker rm crypto-robot-app crypto-robot-webapp
```

3. **Follow installation guide** for Python setup

4. **Restore data**:
```bash
cp -r database-backup/* /opt/crypto-robot/database/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-repo/crypto-robot.git
cd crypto-robot

# Setup development environment
./scripts/setup-python-env.sh

# Run in development mode
export FLASK_DEBUG=true
export ROBOT_DRY_RUN=true
./scripts/start-webapp-direct.sh --debug
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
1. Check the [troubleshooting section](#troubleshooting)
2. Review the [maintenance guide](MAINTENANCE-GUIDE.md)
3. Search existing GitHub issues
4. Create a new issue with:
   - System information
   - Error logs
   - Steps to reproduce

### Documentation
- **[Python Deployment Guide](PYTHON-DEPLOYMENT-GUIDE.md)**: Complete deployment instructions
- **[Maintenance Guide](MAINTENANCE-GUIDE.md)**: Maintenance and updates
- **[Configuration Reference](#configuration)**: Environment variables

---

## 📊 System Status

### Health Check
Run `./scripts/health-check.sh` to verify system health.

### Version Information
- **Architecture**: Direct Python Deployment
- **Python**: 3.8+
- **Framework**: Flask with SocketIO
- **Database**: SQLite (default) or PostgreSQL
- **Process Management**: Systemd services
- **Deployment**: GitHub Actions

---

*For detailed deployment instructions, see the [Python Deployment Guide](PYTHON-DEPLOYMENT-GUIDE.md).*