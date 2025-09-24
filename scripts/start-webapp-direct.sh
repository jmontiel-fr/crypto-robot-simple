#!/bin/bash
# Crypto Robot Web Application Direct Python Startup Script
# Replaces Docker container startup for webapp mode

set -e

echo "🌐 Starting Crypto Robot Web Application (Direct Python)"
echo "========================================================"

# Configuration
APP_PATH="/opt/crypto-robot"
VENV_PATH="/opt/crypto-robot/venv"
LOG_PATH="/opt/crypto-robot/logs"
PID_FILE="/opt/crypto-robot/webapp.pid"

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
    
    # Check Flask availability
    if ! python -c "import flask" 2>/dev/null; then
        echo "❌ Flask not available in virtual environment"
        exit 1
    fi
    
    # Set defaults for web application
    export FLASK_PORT="${FLASK_PORT:-5000}"
    export FLASK_HOST="${FLASK_HOST:-0.0.0.0}"
    export FLASK_DEBUG="${FLASK_DEBUG:-false}"
    export FLASK_PROTOCOL="${FLASK_PROTOCOL:-http}"
    export USE_HTTPS="${USE_HTTPS:-false}"
    
    echo "✅ Environment validation completed"
}

# Function to setup directories
setup_directories() {
    echo "📁 Setting up directories..."
    
    # Create necessary directories
    mkdir -p "$LOG_PATH"
    mkdir -p "$APP_PATH/data"
    mkdir -p "$APP_PATH/database"
    mkdir -p "$APP_PATH/static"
    mkdir -p "$APP_PATH/templates"
    
    # Set permissions
    chmod 755 "$LOG_PATH" "$APP_PATH/data" "$APP_PATH/database"
    
    echo "✅ Directories configured"
}

# Function to configure SSL certificates
configure_ssl() {
    local hostname="${HOSTNAME:-${DOMAIN_NAME:-crypto-robot.local}}"
    local cert_dir="$APP_PATH/certificates/$hostname"
    
    if [ "${USE_HTTPS}" = "true" ] || [ "${FLASK_PROTOCOL}" = "https" ]; then
        echo "🔒 Configuring SSL certificates for: $hostname"
        
        if [ -d "$cert_dir" ] && [ -f "$cert_dir/cert.pem" ] && [ -f "$cert_dir/key.pem" ]; then
            export SSL_CERT_PATH="$cert_dir/cert.pem"
            export SSL_KEY_PATH="$cert_dir/key.pem"
            echo "✅ SSL certificates found and configured"
        else
            echo "⚠️  SSL certificates not found for $hostname"
            echo "   Falling back to HTTP mode"
            export USE_HTTPS="false"
            export FLASK_PROTOCOL="http"
        fi
    else
        echo "🔓 Running in HTTP mode"
    fi
}

# Function to display configuration
display_configuration() {
    echo ""
    echo "🌐 Web Application Configuration:"
    echo "================================="
    echo "🏠 Host: ${FLASK_HOST}"
    echo "🔌 Port: ${FLASK_PORT}"
    echo "🔒 Protocol: ${FLASK_PROTOCOL}"
    echo "🛡️  HTTPS: ${USE_HTTPS}"
    echo "🏷️  Domain: ${HOSTNAME:-${DOMAIN_NAME:-crypto-robot.local}}"
    echo "🐛 Debug: ${FLASK_DEBUG}"
    echo "🐍 Python: $(which python)"
    echo "📁 Working Directory: $(pwd)"
    
    if [ "${USE_HTTPS}" = "true" ]; then
        echo "📄 SSL Cert: ${SSL_CERT_PATH}"
        echo "🔑 SSL Key: ${SSL_KEY_PATH}"
        echo "🌍 Access URL: https://${HOSTNAME:-${DOMAIN_NAME:-crypto-robot.local}}:${FLASK_PORT}"
    else
        echo "🌍 Access URL: http://${FLASK_HOST}:${FLASK_PORT}"
    fi
    
    echo "================================="
    echo ""
}

# Function to check if webapp is already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "⚠️  Web application is already running with PID: $pid"
            echo "💡 Use stop-webapp-direct.sh to stop it first"
            exit 1
        else
            echo "🧹 Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
}

# Function to check port availability
check_port() {
    local port="${FLASK_PORT}"
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo "⚠️  Port $port is already in use"
        echo "💡 Change FLASK_PORT in .env or stop the service using that port"
        exit 1
    fi
    
    echo "✅ Port $port is available"
}

# Function to start webapp
start_webapp() {
    local log_file="$LOG_PATH/webapp-$(date +%Y%m%d-%H%M%S).log"
    
    echo "🚀 Starting web application..."
    echo "📝 Log file: $log_file"
    
    # Change to application directory
    cd "$APP_PATH"
    
    # Start the web application
    if [ "${USE_HTTPS}" = "true" ] && [ "${FLASK_PROTOCOL}" = "https" ]; then
        echo "🔒 Starting with HTTPS..."
        nohup python app.py \
            > "$log_file" 2>&1 &
    else
        echo "🔓 Starting with HTTP..."
        nohup python app.py \
            > "$log_file" 2>&1 &
    fi
    
    # Save PID
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to check if process started successfully
    sleep 3
    
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "✅ Web application started successfully with PID: $pid"
        echo "📝 Log file: $log_file"
        echo "🔍 Monitor with: tail -f $log_file"
        
        # Test if the application is responding
        local url
        if [ "${USE_HTTPS}" = "true" ]; then
            url="https://localhost:${FLASK_PORT}"
        else
            url="http://localhost:${FLASK_PORT}"
        fi
        
        echo "🔍 Testing application response..."
        sleep 2
        
        if curl -s -k "$url" > /dev/null 2>&1; then
            echo "✅ Web application is responding"
        else
            echo "⚠️  Web application may still be starting up"
            echo "💡 Check the log file if issues persist"
        fi
    else
        echo "❌ Web application failed to start"
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
    echo "  --port PORT     Flask port (default: 5000)"
    echo "  --host HOST     Flask host (default: 0.0.0.0)"
    echo "  --https         Enable HTTPS mode"
    echo "  --debug         Enable debug mode"
    echo "  --help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  FLASK_PORT              Web server port"
    echo "  FLASK_HOST              Web server host"
    echo "  FLASK_DEBUG             Enable debug mode"
    echo "  USE_HTTPS               Enable HTTPS"
    echo "  FLASK_PROTOCOL          Protocol (http/https)"
    echo ""
}

# Function to handle shutdown
cleanup() {
    echo ""
    echo "🛑 Received shutdown signal..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🔄 Stopping web application process (PID: $pid)..."
            kill "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "⚡ Force stopping web application process..."
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
        --port)
            export FLASK_PORT="$2"
            shift 2
            ;;
        --host)
            export FLASK_HOST="$2"
            shift 2
            ;;
        --https)
            export USE_HTTPS="true"
            export FLASK_PROTOCOL="https"
            shift
            ;;
        --debug)
            export FLASK_DEBUG="true"
            shift
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
    echo "🚀 Initializing web application startup..."
    
    load_environment
    activate_environment
    validate_environment
    setup_directories
    configure_ssl
    display_configuration
    check_running
    check_port
    start_webapp
    
    echo "🎉 Web application startup completed successfully!"
    echo "💡 Use stop-webapp-direct.sh to stop the web application"
}

# Execute main function
main "$@"