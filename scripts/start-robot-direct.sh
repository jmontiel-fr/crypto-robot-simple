#!/bin/bash
# Crypto Robot Direct Python Startup Script
# Replaces Docker container startup for robot mode

set -e

echo "🤖 Starting Crypto Trading Robot (Direct Python)"
echo "================================================="

# Configuration
APP_PATH="/opt/crypto-robot"
VENV_PATH="/opt/crypto-robot/venv"
LOG_PATH="/opt/crypto-robot/logs"
PID_FILE="/opt/crypto-robot/robot.pid"

# Function to load environment variables
load_environment() {
    echo "📝 Loading environment configuration..."
    
    if [ -f "$APP_PATH/.env" ]; then
        # Export environment variables from .env file
        set -a
        source "$APP_PATH/.env"
        set +a
        echo "✅ Environment loaded from $APP_PATH/.env"
    else
        echo "❌ .env file not found at $APP_PATH/.env"
        exit 1
    fi
}

# Function to activate virtual environment
activate_environment() {
    echo "🐍 Activating Python virtual environment..."
    
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        echo "✅ Virtual environment activated: $VIRTUAL_ENV"
    else
        echo "❌ Virtual environment not found at $VENV_PATH"
        echo "💡 Run setup-python-env.sh first"
        exit 1
    fi
}

# Function to validate environment
validate_environment() {
    echo "🔍 Validating environment..."
    
    # Check Python
    if ! command -v python &> /dev/null; then
        echo "❌ Python not found in virtual environment"
        exit 1
    fi
    
    # Check required environment variables
    required_vars=("BINANCE_API_KEY" "BINANCE_SECRET_KEY" "STARTING_CAPITAL")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Required environment variable not set: $var"
            exit 1
        fi
    done
    
    # Validate API keys (basic check)
    if [ "$BINANCE_API_KEY" = "your_binance_api_key_here" ]; then
        echo "⚠️  WARNING: Default API key detected - robot will run in simulation mode"
        export ROBOT_DRY_RUN=true
    fi
    
    echo "✅ Environment validation completed"
}

# Function to setup directories
setup_directories() {
    echo "📁 Setting up directories..."
    
    # Create necessary directories
    mkdir -p "$LOG_PATH"
    mkdir -p "$APP_PATH/data"
    mkdir -p "$APP_PATH/database"
    
    # Set permissions
    chmod 755 "$LOG_PATH" "$APP_PATH/data" "$APP_PATH/database"
    
    echo "✅ Directories configured"
}

# Function to display configuration
display_configuration() {
    echo ""
    echo "🤖 Trading Robot Configuration:"
    echo "==============================="
    echo "💰 Starting Capital: ${STARTING_CAPITAL:-100} ${RESERVE_ASSET:-USDT}"
    echo "🎯 Strategy: ${STRATEGY_NAME:-daily_rebalance}"
    echo "⏰ Cycle Duration: ${CYCLE_DURATION:-1440} minutes"
    echo "🔄 Portfolio Size: ${PORTFOLIO_SIZE:-15} cryptocurrencies"
    echo "🛡️  Dry Run Mode: ${ROBOT_DRY_RUN:-true}"
    echo "📊 Volatility Mode: ${VOLATILITY_SELECTION_MODE:-average_volatility}"
    echo "🐍 Python: $(which python)"
    echo "📁 Working Directory: $(pwd)"
    echo "==============================="
    echo ""
}

# Function to check if robot is already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "⚠️  Robot is already running with PID: $pid"
            echo "💡 Use stop-robot-direct.sh to stop it first"
            exit 1
        else
            echo "🧹 Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
}

# Function to start robot
start_robot() {
    local robot_mode="${ROBOT_MODE:-single}"
    local log_file="$LOG_PATH/robot-$(date +%Y%m%d-%H%M%S).log"
    
    echo "🚀 Starting robot in mode: $robot_mode"
    echo "📝 Log file: $log_file"
    
    # Change to application directory
    cd "$APP_PATH"
    
    case "$robot_mode" in
        "single")
            echo "🎯 Starting Single Strategy Mode..."
            nohup python main.py --mode single --starting-capital "${STARTING_CAPITAL}" \
                > "$log_file" 2>&1 &
            ;;
        "auto")
            echo "🔄 Starting Automated Trading Mode..."
            nohup python main.py --mode robot --initial-reserve "${STARTING_CAPITAL}" \
                > "$log_file" 2>&1 &
            ;;
        "live")
            if [ "${ROBOT_DRY_RUN}" = "false" ]; then
                echo "🚨 Starting LIVE Trading Mode..."
                echo "⚠️  WARNING: This will execute real trades!"
                nohup python main.py --mode live --starting-capital "${STARTING_CAPITAL}" \
                    > "$log_file" 2>&1 &
            else
                echo "🛡️  Live mode requested but DRY_RUN is enabled"
                echo "   Starting in simulation mode instead"
                nohup python main.py --mode single --starting-capital "${STARTING_CAPITAL}" \
                    > "$log_file" 2>&1 &
            fi
            ;;
        "simulation")
            echo "🧪 Starting Simulation Mode..."
            nohup python main.py --mode simulation \
                --simulation-name "Direct Python Simulation" \
                --simulation-days 21 \
                --simulation-reserve "${STARTING_CAPITAL}" \
                > "$log_file" 2>&1 &
            ;;
        *)
            echo "❌ Unknown robot mode: $robot_mode"
            echo "💡 Valid modes: single, auto, live, simulation"
            exit 1
            ;;
    esac
    
    # Save PID
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to check if process started successfully
    sleep 2
    
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "✅ Robot started successfully with PID: $pid"
        echo "📝 Log file: $log_file"
        echo "🔍 Monitor with: tail -f $log_file"
    else
        echo "❌ Robot failed to start"
        echo "📝 Check log file: $log_file"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --mode MODE     Robot mode (single|auto|live|simulation)"
    echo "  --capital NUM   Starting capital amount"
    echo "  --help         Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ROBOT_MODE              Robot execution mode"
    echo "  STARTING_CAPITAL        Initial capital amount"
    echo "  ROBOT_DRY_RUN          Enable dry run mode (true/false)"
    echo ""
}

# Function to handle shutdown
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🔄 Stopping robot process (PID: $pid)..."
            kill "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "⚡ Force stopping robot process..."
                kill -9 "$pid"
            fi
        fi
        
        rm -f "$PID_FILE"
    fi
    
    echo "✅ Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            export ROBOT_MODE="$2"
            shift 2
            ;;
        --capital)
            export STARTING_CAPITAL="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution flow
main() {
    echo "🚀 Initializing robot startup..."
    
    load_environment
    activate_environment
    validate_environment
    setup_directories
    display_configuration
    check_running
    start_robot
    
    echo "🎉 Robot startup completed successfully!"
    echo "💡 Use stop-robot-direct.sh to stop the robot"
}

# Execute main function
main "$@"