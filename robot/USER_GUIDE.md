# 🤖 Crypto Trading Robot - User Guide

Complete guide for configuring, starting, and managing your crypto trading robot with web interface.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Trading Strategies](#trading-strategies)
4. [Dry-Run vs Live Trading](#dry-run-vs-live-trading)
5. [Starting the Robot](#starting-the-robot)
6. [Starting the Web App](#starting-the-web-app)
7. [Robot Management](#robot-management)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
9. [Safety & Best Practices](#safety--best-practices)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ installed
- Binance account (for live trading)
- All dependencies installed: `pip install -r requirements.txt`

### 1. Configure Environment
```bash
# Copy and edit configuration
cp .env-dev .env
# Edit .env with your settings (see Configuration section)
```

### 2. Start in Safe Mode (Dry-Run)
```bash
# Start web interface
python src/web_app.py

# In another terminal, start robot
python enhanced_crypto_robot.py
```

### 3. Access Web Interface
- **HTTP**: `http://localhost:5000`
- **HTTPS**: `https://crypto-robot.local:5000`

---

## 💾 Database Options

### SQLite (Default - Easy Setup)
**Best for**: Development, testing, single-user setups

**Pros:**
- ✅ No additional setup required
- ✅ File-based (easy backup)
- ✅ Built into Python
- ✅ Perfect for getting started

**Cons:**
- ⚠️ Limited concurrent access
- ⚠️ Single writer at a time
- ⚠️ Not suitable for high-frequency trading

**Configuration:**
```bash
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=data/cryptorobot.db
ENABLE_WAL_MODE=true  # Improves concurrency
```

### PostgreSQL (Production - High Performance)
**Best for**: Production, live trading, multiple users

**Pros:**
- ✅ Excellent concurrency
- ✅ ACID compliance
- ✅ High performance
- ✅ Network access
- ✅ Advanced features

**Cons:**
- ⚠️ Requires separate server setup
- ⚠️ More complex configuration
- ⚠️ Higher resource usage

**Setup Steps:**
1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # macOS (with Homebrew)
   brew install postgresql
   brew services start postgresql
   
   # Windows: Download from postgresql.org
   ```

2. **Create Database and User**
   ```bash
   sudo -u postgres psql
   
   CREATE DATABASE cryptorobot;
   CREATE USER cryptorobot_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE cryptorobot TO cryptorobot_user;
   \q
   ```

3. **Configure .env**
   ```bash
   DATABASE_TYPE=postgresql
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=cryptorobot
   POSTGRES_USER=cryptorobot_user
   POSTGRES_PASSWORD=your_secure_password
   ```

4. **Install Python Dependencies**
   ```bash
   pip install psycopg2-binary
   ```

### Database Migration (SQLite → PostgreSQL)
```bash
# 1. Export SQLite data
python scripts/export_sqlite_data.py

# 2. Setup PostgreSQL (see above)

# 3. Import data to PostgreSQL
python scripts/import_to_postgresql.py

# 4. Update .env configuration

# 5. Restart robot and web app
```

---

## ⚙️ Configuration

### Essential .env Settings

```bash
# =============================================================================
# TRADING CONFIGURATION
# =============================================================================

# Trading Strategy (choose one)
TRADING_STRATEGY=balanced
# Options: conservative, balanced, aggressive, ml_enhanced, bear_market, bull_market

# Dry-Run Mode (IMPORTANT!)
ROBOT_DRY_RUN=true
# Set to 'false' for live trading with real money

# Initial Capital
INITIAL_RESERVE=100
RESERVE_ASSET=BNB

# =============================================================================
# BINANCE API CONFIGURATION (for live trading only)
# =============================================================================

# Get these from Binance API Management
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here

# Trading Parameters
PORTFOLIO_SIZE=6
TRADING_FEE=0.001
STOP_LOSS_THRESHOLD=0.90
ALLOCATION_PERCENTAGE=0.8

# =============================================================================
# WEB INTERFACE CONFIGURATION
# =============================================================================

# Web Server Settings
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
FLASK_DEBUG=True
DOMAIN_NAME=crypto-robot.local
USE_HTTPS=true

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Database Type (sqlite or postgresql)
DATABASE_TYPE=sqlite

# SQLite Configuration (default - simple setup)
SQLITE_DB_PATH=data/cryptorobot.db
ENABLE_WAL_MODE=true
ENABLE_TRANSACTIONS=true

# PostgreSQL Configuration (production - better performance)
# Uncomment and configure for PostgreSQL:
# DATABASE_TYPE=postgresql
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=cryptorobot
# POSTGRES_USER=cryptorobot_user
# POSTGRES_PASSWORD=your_secure_password

# =============================================================================
# ROBOT BEHAVIOR
# =============================================================================

# Cycle Settings
CYCLE_LENGTH_MINUTES=1440
LOOKBACK_CYCLES=4
TOP_COINS_COUNT=50

# Risk Management
UNDERPERFORMER_THRESHOLD=-0.05
MAX_POSITION_SIZE=0.15
MIN_DAILY_VOLUME=50000000
```

### Strategy Configurations

| Strategy | Portfolio Size | Stop-Loss | Risk Level | Best For |
|----------|----------------|-----------|------------|----------|
| **conservative** | 4 coins | -8% | Low | Capital preservation |
| **balanced** | 6 coins | -10% | Medium | Steady growth |
| **aggressive** | 8 coins | -15% | High | Maximum returns |
| **ml_enhanced** | 6 coins | -10% | Medium | AI-powered trading |
| **bear_market** | 3 coins | -6% | Low | Market downturns |
| **bull_market** | 10 coins | -20% | High | Bull runs |

---

## 🎯 Trading Strategies

### Changing Strategy
1. Edit `.env` file:
   ```bash
   TRADING_STRATEGY=aggressive
   ```
2. Restart robot and web app
3. Strategy automatically configures all parameters

### Strategy Details

#### Conservative Strategy
- **Portfolio**: 4 coins (BTC, ETH, BNB focus)
- **Stop-Loss**: -8% (tight protection)
- **Cash Reserve**: 20%
- **Rebalancing**: Daily
- **Best For**: Safe, steady returns

#### Balanced Strategy (Default)
- **Portfolio**: 6 coins (diversified)
- **Stop-Loss**: -10% (moderate protection)
- **Cash Reserve**: 10%
- **Rebalancing**: Every 2 days
- **Best For**: Steady growth with moderate risk

#### Aggressive Strategy
- **Portfolio**: 8 coins (including volatile altcoins)
- **Stop-Loss**: -15% (wider tolerance)
- **Cash Reserve**: 5%
- **Rebalancing**: Every 3 days
- **Best For**: Maximum returns, higher risk

---

## 🧪 Dry-Run vs Live Trading

### Dry-Run Mode (Default - SAFE)

```bash
# In .env file
ROBOT_DRY_RUN=true
```

**Features:**
- ✅ Simulates all trades without real money
- ✅ Realistic fee calculations
- ✅ Virtual portfolio tracking
- ✅ All robot functions work (freeze/unfreeze, close positions)
- ✅ Resume capability after restart
- ✅ Transaction rollback on interruption

**Files Created:**
- `data/dry_run_portfolio.json` - Virtual portfolio
- `data/dry_run_transactions.json` - Trade history

### Live Trading Mode (REAL MONEY)

```bash
# In .env file
ROBOT_DRY_RUN=false

# Required: Binance API credentials
BINANCE_API_KEY=your_real_api_key
BINANCE_SECRET_KEY=your_real_secret_key
```

**⚠️ WARNING: Live mode uses real money! Test thoroughly in dry-run first.**

---

## 🤖 Starting the Robot

### Method 1: Direct Start
```bash
# Start robot directly
python enhanced_crypto_robot.py
```

### Method 2: Background Process (Linux/Mac)
```bash
# Start in background
nohup python enhanced_crypto_robot.py > robot.log 2>&1 &

# Check if running
ps aux | grep enhanced_crypto_robot

# Stop background process
pkill -f enhanced_crypto_robot.py
```

### Method 3: Windows Service
```bash
# Start in background (Windows)
start /B python enhanced_crypto_robot.py

# Stop (find process ID first)
tasklist | findstr python
taskkill /PID <process_id>
```

### Robot Startup Sequence
1. **Configuration Loading** - Reads .env settings
2. **Strategy Selection** - Applies chosen trading strategy
3. **Mode Detection** - Initializes dry-run or live mode
4. **Database Setup** - Enables WAL mode and transactions
5. **Portfolio Loading** - Resumes from last state
6. **Cycle Scheduling** - Starts trading cycles

---

## 🌐 Starting the Web App

### Method 1: Standard HTTP
```bash
python src/web_app.py
```
Access: `http://localhost:5000`

### Method 2: Secure HTTPS
```bash
python start_https_server.py
```
Access: `https://crypto-robot.local:5000`

**Note**: For HTTPS, add to your hosts file:
- **Windows**: `C:\Windows\System32\drivers\etc\hosts`
- **Linux/Mac**: `/etc/hosts`
```
127.0.0.1 crypto-robot.local
```

### Web App Features
- 📊 **Real-time Dashboard** - Portfolio performance, current positions
- 📈 **Trading History** - All trades and performance metrics
- 🎮 **Robot Controls** - Freeze/unfreeze, close positions, restart
- 🧪 **Simulation Tools** - Run backtests and strategy analysis
- ⚙️ **Configuration** - View and modify settings
- 📱 **Mobile Friendly** - Responsive design for all devices

---

## 🎮 Robot Management

### Freeze Robot (Pause Trading)
```bash
# Via web interface: Click "Freeze Robot" button
# Via API: POST /api/robot/freeze
# Via command line: Not directly available
```

### Unfreeze Robot (Resume Trading)
```bash
# Via web interface: Click "Unfreeze Robot" button
# Via API: POST /api/robot/unfreeze
```

### Close All Positions (Emergency Stop)
```bash
# Via web interface: Click "Close All Positions" button
# Via API: POST /api/robot/close-positions
```

### Restart Robot
```bash
# Stop current process (Ctrl+C or kill process)
# Start again: python enhanced_crypto_robot.py
# Robot automatically resumes from last state
```

### Check Robot Status
```bash
# Via web interface: Dashboard shows current status
# Via API: GET /api/robot/status
# Via logs: Check robot.log file
```

---

## 📊 Monitoring & Troubleshooting

### Log Files
- **Robot Logs**: `robot.log` (if using nohup)
- **Web App Logs**: Console output
- **Database**: `data/cryptorobot.db`
- **Dry-Run Data**: `data/dry_run_*.json`

### Key Metrics to Monitor
- **Success Rate**: Target 60-85% depending on strategy
- **Portfolio Value**: Should trend upward over time
- **Drawdown**: Should stay within strategy limits
- **Trading Frequency**: Based on strategy rebalancing schedule

### Common Issues & Solutions

#### Robot Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check .env file exists
ls -la .env

# Check configuration
python -c "import os; print(os.getenv('TRADING_STRATEGY'))"
```

#### Web App Connection Issues
```bash
# Check if port is available
netstat -an | grep 5000

# Try different port
FLASK_PORT=5001 python src/web_app.py

# Check firewall settings
```

#### Database Issues

**SQLite Issues:**
```bash
# Check database file
ls -la data/cryptorobot.db

# Check WAL mode
sqlite3 data/cryptorobot.db "PRAGMA journal_mode;"

# Backup database
cp data/cryptorobot.db data/cryptorobot.db.backup

# Fix corruption
sqlite3 data/cryptorobot.db ".recover" | sqlite3 data/cryptorobot_recovered.db
```

**PostgreSQL Issues:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Connect to database
psql -h localhost -U cryptorobot_user -d cryptorobot

# Check connections
SELECT * FROM pg_stat_activity WHERE datname = 'cryptorobot';

# Backup database
pg_dump -h localhost -U cryptorobot_user cryptorobot > backup.sql

# Restore database
psql -h localhost -U cryptorobot_user cryptorobot < backup.sql
```

#### API Connection Issues (Live Mode)
```bash
# Test API credentials
python -c "
import os
from binance.client import Client
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'))
print(client.get_account())
"
```

### Performance Optimization

**SQLite Optimization:**
- **WAL Mode**: Enabled automatically for better concurrency
- **Cache Size**: Optimized for trading workload
- **Synchronous**: Set to NORMAL for better performance
- **Memory Mapping**: Enabled for faster access

**PostgreSQL Optimization:**
- **Connection Pooling**: Configured automatically
- **Shared Buffers**: Increase for better performance
- **Work Memory**: Optimize for query performance
- **Checkpoint Settings**: Tuned for write-heavy workload

**General:**
- **Memory**: Monitor with `htop` or Task Manager
- **Network**: Ensure stable internet connection
- **Storage**: Keep at least 1GB free space

---

## 🛡️ Safety & Best Practices

### Before Live Trading
1. **✅ Test in Dry-Run Mode** - Run for at least 1 week
2. **✅ Verify Strategy Performance** - Check success rate and drawdown
3. **✅ Test All Functions** - Freeze, unfreeze, close positions
4. **✅ Backup Configuration** - Save .env and database files
5. **✅ Start Small** - Use minimal capital initially

### Security Best Practices
- **🔐 API Keys**: Use Binance API with trading permissions only (no withdrawal)
- **🔒 Environment**: Keep .env file secure, never commit to git
- **🌐 Network**: Use HTTPS for web interface
- **💾 Backups**: Regular database backups
- **📱 Monitoring**: Set up alerts for unusual activity

### Risk Management
- **💰 Capital**: Never invest more than you can afford to lose
- **📊 Diversification**: Use balanced or conservative strategies initially
- **⏰ Monitoring**: Check robot status daily
- **🚨 Stop-Loss**: Ensure stop-loss levels are appropriate
- **📈 Performance**: Review and adjust strategy based on results

### Emergency Procedures
1. **Immediate Stop**: Click "Close All Positions" in web interface
2. **Freeze Robot**: Use freeze function to pause trading
3. **Manual Override**: Access Binance directly if needed
4. **Rollback**: Restore from database backup if necessary

---

## 📞 Support & Resources

### Configuration Files
- **Main Config**: `.env`
- **Strategy Examples**: `.env.conservative`, `.env.aggressive`, etc.
- **Database**: `data/cryptorobot.db`
- **Logs**: `robot.log`, web app console

### Useful Commands
```bash
# Check robot status
curl http://localhost:5000/api/robot/status

# View recent trades
curl http://localhost:5000/api/trading-cycles/recent

# Get portfolio summary
curl http://localhost:5000/api/portfolio/summary

# Test dry-run system
python test_dry_run_system.py

# Test strategy system
python test_strategy_system.py
```

### File Structure
```
crypto-robot/
├── .env                          # Main configuration
├── enhanced_crypto_robot.py      # Main robot script
├── src/
│   ├── web_app.py               # Web interface
│   ├── strategy_manager.py      # Trading strategies
│   ├── dry_run_manager.py       # Dry-run simulation
│   └── ...                      # Other modules
├── data/
│   ├── cryptorobot.db          # Main database
│   ├── dry_run_portfolio.json  # Dry-run portfolio
│   └── dry_run_transactions.json # Dry-run trades
└── templates/                   # Web interface templates
```

---

## 🗄️ Database Selection Guide

### When to Use SQLite
**✅ Use SQLite if:**
- Getting started with the robot
- Running simulations and backtests
- Single user setup
- Development and testing
- Simple deployment requirements

**Configuration:**
```bash
DATABASE_TYPE=sqlite
ENABLE_WAL_MODE=true
```

### When to Use PostgreSQL
**✅ Use PostgreSQL if:**
- Running live trading with real money
- High-frequency trading (multiple trades per day)
- Multiple users accessing web interface
- Production deployment
- Need maximum reliability and performance

**Configuration:**
```bash
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_DB=cryptorobot
POSTGRES_USER=cryptorobot_user
POSTGRES_PASSWORD=your_secure_password
```

### Migration Path
1. **Start with SQLite** (easy setup)
2. **Test strategies** in dry-run mode
3. **Migrate to PostgreSQL** before live trading
4. **Monitor performance** and optimize

### Database Performance Comparison

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Setup Complexity** | Easy | Medium |
| **Concurrent Access** | Limited | Excellent |
| **Performance** | Good | Excellent |
| **Reliability** | Good | Excellent |
| **Backup Options** | Basic | Advanced |
| **Scalability** | Limited | High |
| **Live Trading Suitability** | ⚠️ Acceptable | ✅ Recommended |

---

## 🎯 Quick Reference

### Start Everything
```bash
# 1. Start web app
python src/web_app.py

# 2. In new terminal, start robot
python enhanced_crypto_robot.py

# 3. Access web interface
# HTTP: http://localhost:5000
# HTTPS: https://crypto-robot.local:5000
```

### Change Strategy
```bash
# Edit .env file
TRADING_STRATEGY=aggressive

# Restart robot
# Strategy auto-applies on restart
```

### Switch to Live Trading
```bash
# Edit .env file
ROBOT_DRY_RUN=false
BINANCE_API_KEY=your_real_key
BINANCE_SECRET_KEY=your_real_secret

# Restart robot
# WARNING: Uses real money!
```

### Emergency Stop
```bash
# Via web interface: "Close All Positions" button
# Via terminal: Ctrl+C to stop robot
# Via API: POST /api/robot/close-positions
```

---

**🚀 Your crypto trading robot is ready! Start with dry-run mode to test safely, then switch to live trading when confident.**

**Remember: Always test thoroughly in dry-run mode before risking real money!** 💰