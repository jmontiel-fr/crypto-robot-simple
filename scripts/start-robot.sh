#!/bin/bash
# Crypto Robot Trading Robot Startup Script

set -e

echo "🤖 Starting Crypto Trading Robot..."

# Change to application directory
cd /opt/crypto-robot/app

# Load environment variables
if [ -f "../.env" ]; then
    echo "📝 Loading environment configuration..."
    export $(grep -v '^#' ../.env | xargs)
    echo "✅ Environment loaded"
else
    echo "❌ .env file not found"
    exit 1
fi

# Display robot configuration
echo ""
echo "🤖 Trading Robot Configuration:"
echo "==============================="
echo "💰 Starting Capital: ${STARTING_CAPITAL:-100} ${RESERVE_ASSET:-BNB}"
echo "🎯 Strategy: ${STRATEGY_NAME:-daily_rebalance}"
echo "⏰ Cycle Duration: ${CYCLE_DURATION:-1440} minutes"
echo "🔄 Portfolio Size: ${PORTFOLIO_SIZE:-15} cryptocurrencies"
echo "🛡️  Dry Run Mode: ${ROBOT_DRY_RUN:-true}"
echo "📊 Volatility Mode: ${VOLATILITY_SELECTION_MODE:-average_volatility}"
echo "==============================="
echo ""

# Check if Binance API keys are configured
if [ -z "$BINANCE_API_KEY" ] || [ "$BINANCE_API_KEY" = "your_binance_api_key_here" ]; then
    echo "⚠️  WARNING: Binance API keys not configured"
    echo "   Robot will run in simulation mode only"
    export ROBOT_DRY_RUN=true
fi

# Validate required environment variables
required_vars=("BINANCE_API_KEY" "BINANCE_SECRET_KEY" "STARTING_CAPITAL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable not set: $var"
        exit 1
    fi
done

# Create necessary directories
mkdir -p ../data ../logs

# Initialize database if needed
if [ ! -f "../data/cryptorobot.db" ]; then
    echo "🗄️  Initializing database..."
    python create_database.py
    echo "✅ Database initialized"
fi

# Function to handle different robot modes
start_robot_mode() {
    local robot_mode="${ROBOT_MODE:-single}"
    
    case "$robot_mode" in
        "single")
            echo "🎯 Starting Single Strategy Mode..."
            python main.py --mode single --starting-capital "${STARTING_CAPITAL}"
            ;;
        "auto")
            echo "🔄 Starting Automated Trading Mode..."
            python main.py --mode robot --initial-reserve "${STARTING_CAPITAL}"
            ;;
        "live")
            if [ "${ROBOT_DRY_RUN}" = "false" ]; then
                echo "🚨 Starting LIVE Trading Mode..."
                echo "⚠️  WARNING: This will execute real trades!"
                python main.py --mode live --starting-capital "${STARTING_CAPITAL}"
            else
                echo "🛡️  Live mode requested but DRY_RUN is enabled"
                echo "   Starting in simulation mode instead"
                python main.py --mode single --starting-capital "${STARTING_CAPITAL}"
            fi
            ;;
        "simulation")
            echo "🧪 Starting Simulation Mode..."
            python main.py --mode simulation \
                --simulation-name "Container Simulation" \
                --simulation-days 21 \
                --simulation-reserve "${STARTING_CAPITAL}"
            ;;
        *)
            echo "❌ Unknown robot mode: $robot_mode"
            echo "💡 Valid modes: single, auto, live, simulation"
            exit 1
            ;;
    esac
}

# Function to monitor robot health
monitor_robot() {
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "🚀 Starting robot (attempt $((retry_count + 1))/$max_retries)..."
        
        if start_robot_mode; then
            echo "✅ Robot completed successfully"
            break
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                echo "⚠️  Robot failed, retrying in 30 seconds..."
                sleep 30
            else
                echo "❌ Robot failed after $max_retries attempts"
                exit 1
            fi
        fi
    done
}

# Function to handle shutdown
cleanup_robot() {
    echo ""
    echo "🛑 Shutting down trading robot..."
    
    # Kill any Python processes
    pkill -f "python.*main.py" 2>/dev/null || true
    
    echo "✅ Trading robot shutdown completed"
    exit 0
}

# Set up signal handlers
trap cleanup_robot SIGTERM SIGINT

# Main execution
echo "🚀 Initializing trading robot..."

# Check Python environment
if ! command -v python &> /dev/null; then
    echo "❌ Python not found"
    exit 1
fi

echo "🐍 Python version: $(python --version)"

# Start robot with monitoring
monitor_robot

echo "🏁 Trading robot execution completed"