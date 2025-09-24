#!/bin/bash
# Crypto Robot Flask Web Application Startup Script

set -e

echo "🌐 Starting Crypto Robot Web Application..."

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

# Extract Flask configuration with fallback defaults
FLASK_PORT="${FLASK_PORT:-5000}"
FLASK_HOST="${FLASK_HOST:-0.0.0.0}"
FLASK_PROTOCOL="${FLASK_PROTOCOL:-http}"
USE_HTTPS="${USE_HTTPS:-false}"
DOMAIN_NAME="${DOMAIN_NAME:-crypto-robot.local}"

# Determine if HTTPS should be used
if [ "$USE_HTTPS" = "true" ] || [ "$FLASK_PROTOCOL" = "https" ]; then
    USE_HTTPS_MODE=true
    DEFAULT_PORT=5443
else
    USE_HTTPS_MODE=false
    DEFAULT_PORT=5000
fi

# Use configured port or default based on protocol
if [ "$FLASK_PORT" = "5000" ] && [ "$USE_HTTPS_MODE" = "true" ]; then
    FLASK_PORT=$DEFAULT_PORT
fi

# Display webapp configuration
echo ""
echo "🌐 Web Application Configuration:"
echo "================================="
echo "🏷️  Domain: $DOMAIN_NAME"
echo "🔌 Host: $FLASK_HOST"
echo "🔌 Port: $FLASK_PORT"
echo "🔒 HTTPS: $USE_HTTPS_MODE"
echo "🎯 Protocol: $FLASK_PROTOCOL"
echo "🐛 Debug: ${FLASK_DEBUG:-False}"
echo "🌍 Environment: ${FLASK_ENV:-production}"
echo "================================="
echo ""

# Validate SSL certificates if HTTPS is enabled
if [ "$USE_HTTPS_MODE" = "true" ]; then
    SSL_CERT_PATH="${SSL_CERT_PATH:-../certificates/$DOMAIN_NAME/cert.pem}"
    SSL_KEY_PATH="${SSL_KEY_PATH:-../certificates/$DOMAIN_NAME/key.pem}"
    
    echo "🔒 Validating SSL certificates..."
    echo "   📄 Certificate: $SSL_CERT_PATH"
    echo "   🔑 Private Key: $SSL_KEY_PATH"
    
    if [ ! -f "$SSL_CERT_PATH" ]; then
        echo "❌ SSL certificate not found: $SSL_CERT_PATH"
        exit 1
    fi
    
    if [ ! -f "$SSL_KEY_PATH" ]; then
        echo "❌ SSL private key not found: $SSL_KEY_PATH"
        exit 1
    fi
    
    echo "✅ SSL certificates validated"
fi

# Create necessary directories
mkdir -p ../data ../logs

# Initialize database if needed
if [ ! -f "../data/cryptorobot.db" ]; then
    echo "🗄️  Initializing database..."
    python create_database.py
    echo "✅ Database initialized"
fi

# Function to start Flask application
start_flask_app() {
    echo "🚀 Starting Flask application..."
    
    # Set Flask environment variables
    export FLASK_APP=app.py
    export FLASK_RUN_HOST="$FLASK_HOST"
    export FLASK_RUN_PORT="$FLASK_PORT"
    
    if [ "$USE_HTTPS_MODE" = "true" ]; then
        echo "🔒 Starting HTTPS server..."
        
        # Use the HTTPS startup script if available
        if [ -f "start_https_server.py" ]; then
            python start_https_server.py
        else
            # Fallback to Flask with SSL context
            python -c "
import os
import sys
sys.path.append('src')

from src.web_app import app, socketio

if __name__ == '__main__':
    ssl_context = ('$SSL_CERT_PATH', '$SSL_KEY_PATH')
    print(f'🔒 Starting HTTPS server on https://$FLASK_HOST:$FLASK_PORT')
    socketio.run(app, 
                host='$FLASK_HOST', 
                port=$FLASK_PORT, 
                debug=${FLASK_DEBUG:-False}, 
                ssl_context=ssl_context,
                allow_unsafe_werkzeug=True)
"
        fi
    else
        echo "🌐 Starting HTTP server..."
        
        # Use the regular app startup
        if [ -f "app.py" ]; then
            python app.py
        else
            # Fallback to direct Flask run
            python -c "
import os
import sys
sys.path.append('src')

from src.web_app import app, socketio

if __name__ == '__main__':
    print(f'🌐 Starting HTTP server on http://$FLASK_HOST:$FLASK_PORT')
    socketio.run(app, 
                host='$FLASK_HOST', 
                port=$FLASK_PORT, 
                debug=${FLASK_DEBUG:-False},
                allow_unsafe_werkzeug=True)
"
        fi
    fi
}

# Function to check if port is available
check_port_availability() {
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$FLASK_PORT "; then
            echo "⚠️  Port $FLASK_PORT is already in use"
            echo "💡 Consider changing FLASK_PORT in .env file"
            return 1
        fi
    fi
    return 0
}

# Function to handle webapp health check
webapp_health_check() {
    local max_attempts=30
    local attempt=1
    local protocol="http"
    
    if [ "$USE_HTTPS_MODE" = "true" ]; then
        protocol="https"
    fi
    
    local health_url="${protocol}://${FLASK_HOST}:${FLASK_PORT}/health"
    
    echo "🔍 Waiting for webapp to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s -k "$health_url" > /dev/null 2>&1; then
            echo "✅ Web application is healthy and responding"
            echo "🌍 Access URL: ${protocol}://${DOMAIN_NAME}:${FLASK_PORT}"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts - waiting for webapp..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Web application failed to start within expected time"
    return 1
}

# Function to handle shutdown
cleanup_webapp() {
    echo ""
    echo "🛑 Shutting down web application..."
    
    # Kill any Python/Flask processes
    pkill -f "python.*app.py" 2>/dev/null || true
    pkill -f "flask run" 2>/dev/null || true
    
    echo "✅ Web application shutdown completed"
    exit 0
}

# Set up signal handlers
trap cleanup_webapp SIGTERM SIGINT

# Main execution
echo "🚀 Initializing web application..."

# Check Python environment
if ! command -v python &> /dev/null; then
    echo "❌ Python not found"
    exit 1
fi

echo "🐍 Python version: $(python --version)"

# Check port availability
if ! check_port_availability; then
    echo "❌ Cannot start webapp - port conflict"
    exit 1
fi

# Start Flask application in background for health check
start_flask_app &
FLASK_PID=$!

# Wait a moment and then check health
sleep 5

# Perform health check
if webapp_health_check; then
    echo "🎉 Web application started successfully!"
    echo "📊 Process ID: $FLASK_PID"
    
    # Wait for the Flask process to complete
    wait $FLASK_PID
else
    echo "❌ Web application health check failed"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi

echo "🏁 Web application execution completed"