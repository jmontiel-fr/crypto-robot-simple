#!/bin/bash
# Crypto Robot Web Application Stop Script for Direct Python Deployment

set -e

echo "🛑 Stopping Crypto Robot Web Application"
echo "========================================"

# Configuration
APP_PATH="/opt/crypto-robot"
PID_FILE="/opt/crypto-robot/webapp.pid"
LOG_PATH="/opt/crypto-robot/logs"

# Function to stop webapp process
stop_webapp() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🔄 Stopping web application process (PID: $pid)..."
            
            # Send SIGTERM for graceful shutdown
            kill "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 15 ]; do
                echo "⏳ Waiting for graceful shutdown... ($count/15)"
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "⚡ Force stopping web application process..."
                kill -9 "$pid"
                sleep 1
            fi
            
            if ! ps -p "$pid" > /dev/null 2>&1; then
                echo "✅ Web application stopped successfully"
            else
                echo "❌ Failed to stop web application process"
                exit 1
            fi
        else
            echo "⚠️  Web application process not running (PID: $pid)"
        fi
        
        # Remove PID file
        rm -f "$PID_FILE"
    else
        echo "⚠️  No PID file found - web application may not be running"
    fi
}

# Function to cleanup any remaining processes
cleanup_processes() {
    echo "🧹 Cleaning up any remaining web application processes..."
    
    # Find and kill any remaining python processes running app.py
    local pids=$(pgrep -f "python.*app.py" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "🔍 Found remaining processes: $pids"
        for pid in $pids; do
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "🔄 Stopping process $pid..."
                kill "$pid" 2>/dev/null || true
            fi
        done
        
        # Wait a moment
        sleep 2
        
        # Force kill if still running
        pids=$(pgrep -f "python.*app.py" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "⚡ Force killing remaining processes..."
            pkill -9 -f "python.*app.py" 2>/dev/null || true
        fi
    fi
    
    # Also check for Flask processes
    local flask_pids=$(pgrep -f "flask" 2>/dev/null || true)
    if [ -n "$flask_pids" ]; then
        echo "🔍 Found Flask processes: $flask_pids"
        for pid in $flask_pids; do
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "🔄 Stopping Flask process $pid..."
                kill "$pid" 2>/dev/null || true
            fi
        done
    fi
    
    echo "✅ Process cleanup completed"
}

# Function to check port status
check_port_status() {
    local port="${FLASK_PORT:-5000}"
    
    echo "🔍 Checking port $port status..."
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo "⚠️  Port $port is still in use"
        echo "🔍 Processes using port $port:"
        lsof -i ":$port" 2>/dev/null || netstat -tulnp 2>/dev/null | grep ":$port"
    else
        echo "✅ Port $port is now available"
    fi
}

# Function to display status
show_status() {
    echo ""
    echo "📊 Web Application Status After Stop:"
    echo "===================================="
    
    if [ -f "$PID_FILE" ]; then
        echo "❌ PID file still exists: $PID_FILE"
    else
        echo "✅ PID file removed"
    fi
    
    local running_processes=$(pgrep -f "python.*app.py" 2>/dev/null | wc -l)
    echo "🔍 Running webapp processes: $running_processes"
    
    if [ "$running_processes" -eq 0 ]; then
        echo "✅ No webapp processes running"
    else
        echo "⚠️  Some webapp processes may still be running"
        pgrep -f "python.*app.py" 2>/dev/null || true
    fi
    
    check_port_status
    echo ""
}

# Function to show recent logs
show_recent_logs() {
    echo "📝 Recent Web Application Logs:"
    echo "==============================="
    
    local latest_log=$(ls -t "$LOG_PATH"/webapp-*.log 2>/dev/null | head -n1)
    
    if [ -n "$latest_log" ] && [ -f "$latest_log" ]; then
        echo "📄 Latest log file: $latest_log"
        echo "📋 Last 10 lines:"
        tail -n 10 "$latest_log"
    else
        echo "⚠️  No webapp log files found"
    fi
    
    echo ""
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --force         Force kill all webapp processes"
    echo "  --status        Show status after stopping"
    echo "  --logs          Show recent logs"
    echo "  --help          Show this help message"
    echo ""
}

# Parse command line arguments
FORCE_KILL=false
SHOW_STATUS=false
SHOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_KILL=true
            shift
            ;;
        --status)
            SHOW_STATUS=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
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
    echo "🚀 Initiating web application shutdown..."
    
    if [ "$FORCE_KILL" = true ]; then
        echo "⚡ Force kill mode enabled"
        cleanup_processes
    else
        stop_webapp
        cleanup_processes
    fi
    
    if [ "$SHOW_STATUS" = true ]; then
        show_status
    fi
    
    if [ "$SHOW_LOGS" = true ]; then
        show_recent_logs
    fi
    
    echo "🎉 Web application shutdown completed!"
}

# Execute main function
main "$@"