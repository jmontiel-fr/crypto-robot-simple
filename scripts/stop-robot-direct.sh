#!/bin/bash
# Crypto Robot Stop Script for Direct Python Deployment

set -e

echo "🛑 Stopping Crypto Trading Robot"
echo "================================="

# Configuration
APP_PATH="/opt/crypto-robot"
PID_FILE="/opt/crypto-robot/robot.pid"
LOG_PATH="/opt/crypto-robot/logs"

# Function to stop robot process
stop_robot() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "🔄 Stopping robot process (PID: $pid)..."
            
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
                echo "⚡ Force stopping robot process..."
                kill -9 "$pid"
                sleep 1
            fi
            
            if ! ps -p "$pid" > /dev/null 2>&1; then
                echo "✅ Robot stopped successfully"
            else
                echo "❌ Failed to stop robot process"
                exit 1
            fi
        else
            echo "⚠️  Robot process not running (PID: $pid)"
        fi
        
        # Remove PID file
        rm -f "$PID_FILE"
    else
        echo "⚠️  No PID file found - robot may not be running"
    fi
}

# Function to cleanup any remaining processes
cleanup_processes() {
    echo "🧹 Cleaning up any remaining robot processes..."
    
    # Find and kill any remaining python processes running main.py
    local pids=$(pgrep -f "python.*main.py" 2>/dev/null || true)
    
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
        pids=$(pgrep -f "python.*main.py" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "⚡ Force killing remaining processes..."
            pkill -9 -f "python.*main.py" 2>/dev/null || true
        fi
    fi
    
    echo "✅ Process cleanup completed"
}

# Function to display status
show_status() {
    echo ""
    echo "📊 Robot Status After Stop:"
    echo "==========================="
    
    if [ -f "$PID_FILE" ]; then
        echo "❌ PID file still exists: $PID_FILE"
    else
        echo "✅ PID file removed"
    fi
    
    local running_processes=$(pgrep -f "python.*main.py" 2>/dev/null | wc -l)
    echo "🔍 Running robot processes: $running_processes"
    
    if [ "$running_processes" -eq 0 ]; then
        echo "✅ No robot processes running"
    else
        echo "⚠️  Some robot processes may still be running"
        pgrep -f "python.*main.py" 2>/dev/null || true
    fi
    
    echo ""
}

# Function to show recent logs
show_recent_logs() {
    echo "📝 Recent Robot Logs:"
    echo "===================="
    
    local latest_log=$(ls -t "$LOG_PATH"/robot-*.log 2>/dev/null | head -n1)
    
    if [ -n "$latest_log" ] && [ -f "$latest_log" ]; then
        echo "📄 Latest log file: $latest_log"
        echo "📋 Last 10 lines:"
        tail -n 10 "$latest_log"
    else
        echo "⚠️  No robot log files found"
    fi
    
    echo ""
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --force         Force kill all robot processes"
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
    echo "🚀 Initiating robot shutdown..."
    
    if [ "$FORCE_KILL" = true ]; then
        echo "⚡ Force kill mode enabled"
        cleanup_processes
    else
        stop_robot
        cleanup_processes
    fi
    
    if [ "$SHOW_STATUS" = true ]; then
        show_status
    fi
    
    if [ "$SHOW_LOGS" = true ]; then
        show_recent_logs
    fi
    
    echo "🎉 Robot shutdown completed!"
}

# Execute main function
main "$@"