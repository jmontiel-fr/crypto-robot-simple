#!/bin/bash
# Crypto Robot Service Control Script
# Manages systemd services for robot and webapp

set -e

echo "⚙️  Crypto Robot Service Control"
echo "==============================="

# Configuration
ROBOT_SERVICE="crypto-robot"
WEBAPP_SERVICE="crypto-webapp"
LOG_PATH="/opt/crypto-robot/logs"

# Function to check if running as root/sudo for systemd operations
check_systemd_privileges() {
    if [ "$EUID" -ne 0 ] && [ "$1" != "status" ] && [ "$1" != "logs" ]; then
        echo "❌ This operation requires root privileges"
        echo "💡 Usage: sudo $0 $1"
        exit 1
    fi
}

# Function to start service
start_service() {
    local service="$1"
    
    echo "🚀 Starting $service service..."
    
    if systemctl is-active --quiet "$service"; then
        echo "⚠️  $service is already running"
        return 0
    fi
    
    systemctl start "$service"
    
    # Wait a moment and check status
    sleep 2
    
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service started successfully"
        
        # Show recent logs
        echo "📝 Recent logs:"
        journalctl -u "$service" --no-pager -n 5
    else
        echo "❌ Failed to start $service"
        echo "📝 Error logs:"
        journalctl -u "$service" --no-pager -n 10
        return 1
    fi
}

# Function to stop service
stop_service() {
    local service="$1"
    
    echo "🛑 Stopping $service service..."
    
    if ! systemctl is-active --quiet "$service"; then
        echo "⚠️  $service is not running"
        return 0
    fi
    
    systemctl stop "$service"
    
    # Wait a moment and check status
    sleep 2
    
    if ! systemctl is-active --quiet "$service"; then
        echo "✅ $service stopped successfully"
    else
        echo "❌ Failed to stop $service"
        return 1
    fi
}

# Function to restart service
restart_service() {
    local service="$1"
    
    echo "🔄 Restarting $service service..."
    
    systemctl restart "$service"
    
    # Wait a moment and check status
    sleep 3
    
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service restarted successfully"
        
        # Show recent logs
        echo "📝 Recent logs:"
        journalctl -u "$service" --no-pager -n 5
    else
        echo "❌ Failed to restart $service"
        echo "📝 Error logs:"
        journalctl -u "$service" --no-pager -n 10
        return 1
    fi
}

# Function to show service status
show_service_status() {
    local service="$1"
    
    echo "📊 $service Status:"
    echo "=================="
    
    # Basic status
    local status=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
    local enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "disabled")
    
    echo "  Active: $status"
    echo "  Enabled: $enabled"
    
    # Detailed status if active
    if [ "$status" = "active" ]; then
        echo ""
        echo "📋 Detailed Status:"
        systemctl status "$service" --no-pager -l
    fi
    
    echo ""
}

# Function to show logs
show_logs() {
    local service="$1"
    local lines="${2:-50}"
    local follow="${3:-false}"
    
    echo "📝 $service Logs (last $lines lines):"
    echo "====================================="
    
    if [ "$follow" = "true" ]; then
        echo "📡 Following logs (Ctrl+C to stop)..."
        journalctl -u "$service" -f
    else
        journalctl -u "$service" --no-pager -n "$lines"
    fi
}

# Function to enable service
enable_service() {
    local service="$1"
    
    echo "⚡ Enabling $service service..."
    
    if systemctl is-enabled --quiet "$service"; then
        echo "⚠️  $service is already enabled"
        return 0
    fi
    
    systemctl enable "$service"
    echo "✅ $service enabled successfully"
}

# Function to disable service
disable_service() {
    local service="$1"
    
    echo "🔌 Disabling $service service..."
    
    if ! systemctl is-enabled --quiet "$service"; then
        echo "⚠️  $service is already disabled"
        return 0
    fi
    
    systemctl disable "$service"
    echo "✅ $service disabled successfully"
}

# Function to show all services status
show_all_status() {
    echo "📊 All Crypto Robot Services Status:"
    echo "===================================="
    
    for service in "$ROBOT_SERVICE" "$WEBAPP_SERVICE"; do
        local status=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
        local enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "disabled")
        
        printf "%-15s | %-8s | %-8s\n" "$service" "$status" "$enabled"
    done
    
    echo ""
    echo "🔍 Process Information:"
    echo "======================"
    
    # Show Python processes
    local robot_pids=$(pgrep -f "python.*main.py" 2>/dev/null || true)
    local webapp_pids=$(pgrep -f "python.*app.py" 2>/dev/null || true)
    
    if [ -n "$robot_pids" ]; then
        echo "🤖 Robot processes: $robot_pids"
    else
        echo "🤖 Robot processes: none"
    fi
    
    if [ -n "$webapp_pids" ]; then
        echo "🌐 WebApp processes: $webapp_pids"
    else
        echo "🌐 WebApp processes: none"
    fi
    
    # Show PID files
    echo ""
    echo "📄 PID Files:"
    echo "============="
    ls -la /opt/crypto-robot/*.pid 2>/dev/null || echo "No PID files found"
    
    # Show recent log files
    echo ""
    echo "📝 Recent Log Files:"
    echo "==================="
    ls -la "$LOG_PATH"/*.log 2>/dev/null | tail -5 || echo "No log files found"
}

# Function to perform health check
health_check() {
    local service="$1"
    
    echo "🏥 Health Check for $service:"
    echo "============================"
    
    local errors=0
    
    # Check if service is installed
    if ! systemctl list-unit-files | grep -q "$service.service"; then
        echo "❌ Service not installed: $service"
        errors=$((errors + 1))
    else
        echo "✅ Service installed: $service"
    fi
    
    # Check if service is enabled
    if systemctl is-enabled --quiet "$service"; then
        echo "✅ Service enabled: $service"
    else
        echo "⚠️  Service not enabled: $service"
    fi
    
    # Check if service is active
    if systemctl is-active --quiet "$service"; then
        echo "✅ Service active: $service"
        
        # Check process
        case "$service" in
            "$ROBOT_SERVICE")
                if pgrep -f "python.*main.py" > /dev/null; then
                    echo "✅ Robot process running"
                else
                    echo "❌ Robot process not found"
                    errors=$((errors + 1))
                fi
                ;;
            "$WEBAPP_SERVICE")
                if pgrep -f "python.*app.py" > /dev/null; then
                    echo "✅ WebApp process running"
                else
                    echo "❌ WebApp process not found"
                    errors=$((errors + 1))
                fi
                ;;
        esac
    else
        echo "❌ Service not active: $service"
        errors=$((errors + 1))
    fi
    
    # Check log files
    local log_pattern=""
    case "$service" in
        "$ROBOT_SERVICE")
            log_pattern="robot-*.log"
            ;;
        "$WEBAPP_SERVICE")
            log_pattern="webapp-*.log"
            ;;
    esac
    
    if ls "$LOG_PATH"/$log_pattern 1> /dev/null 2>&1; then
        echo "✅ Log files present"
        
        # Check for recent activity (last 5 minutes)
        local recent_logs=$(find "$LOG_PATH" -name "$log_pattern" -mmin -5 2>/dev/null)
        if [ -n "$recent_logs" ]; then
            echo "✅ Recent log activity detected"
        else
            echo "⚠️  No recent log activity"
        fi
    else
        echo "⚠️  No log files found"
    fi
    
    echo ""
    if [ $errors -eq 0 ]; then
        echo "🎉 Health check passed!"
        return 0
    else
        echo "❌ Health check failed with $errors errors"
        return 1
    fi
}

# Function to display usage
show_usage() {
    echo "Usage: $0 COMMAND [SERVICE] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start SERVICE       Start a service"
    echo "  stop SERVICE        Stop a service"
    echo "  restart SERVICE     Restart a service"
    echo "  status [SERVICE]    Show service status"
    echo "  logs SERVICE [N]    Show service logs (last N lines, default: 50)"
    echo "  follow SERVICE      Follow service logs in real-time"
    echo "  enable SERVICE      Enable service for auto-start"
    echo "  disable SERVICE     Disable service auto-start"
    echo "  health [SERVICE]    Perform health check"
    echo "  start-all          Start all services"
    echo "  stop-all           Stop all services"
    echo "  restart-all        Restart all services"
    echo ""
    echo "Services:"
    echo "  robot              Trading robot service ($ROBOT_SERVICE)"
    echo "  webapp             Web application service ($WEBAPP_SERVICE)"
    echo ""
    echo "Examples:"
    echo "  $0 start robot"
    echo "  $0 status"
    echo "  $0 logs webapp 100"
    echo "  $0 follow robot"
    echo "  $0 restart-all"
    echo ""
}

# Function to resolve service name
resolve_service_name() {
    case "$1" in
        "robot")
            echo "$ROBOT_SERVICE"
            ;;
        "webapp")
            echo "$WEBAPP_SERVICE"
            ;;
        "$ROBOT_SERVICE"|"$WEBAPP_SERVICE")
            echo "$1"
            ;;
        *)
            echo "❌ Unknown service: $1"
            echo "💡 Available services: robot, webapp"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    local command="${1:-}"
    local service_arg="${2:-}"
    local option="${3:-}"
    
    case "$command" in
        "start")
            if [ -z "$service_arg" ]; then
                echo "❌ Service name required"
                show_usage
                exit 1
            fi
            check_systemd_privileges "$command"
            local service=$(resolve_service_name "$service_arg")
            start_service "$service"
            ;;
        "stop")
            if [ -z "$service_arg" ]; then
                echo "❌ Service name required"
                show_usage
                exit 1
            fi
            check_systemd_privileges "$command"
            local service=$(resolve_service_name "$service_arg")
            stop_service "$service"
            ;;
        "restart")
            if [ -z "$service_arg" ]; then
                echo "❌ Service name required"
                show_usage
                exit 1
            fi
            check_systemd_privileges "$command"
            local service=$(resolve_service_name "$service_arg")
            restart_service "$service"
            ;;
        "status")
            if [ -z "$service_arg" ]; then
                show_all_status
            else
                local service=$(resolve_service_name "$service_arg")
                show_service_status "$service"
            fi
            ;;
        "logs")
            if [ -z "$service_arg" ]; then
                echo "❌ Service name required"
                show_usage
                exit 1
            fi
            local service=$(resolve_service_name "$service_arg")
            local lines="${option:-50}"
            show_logs "$service" "$lines"
            ;;
        "follow")
            if [ -z "$service_arg" ]; then
                echo "❌ Service name required"
                show_usage
                exit 1
            fi
            local service=$(resolve_service_name "$service_arg")
            show_logs "$service" "50" "true"
            ;;
        "enable")
            if [ -z "$service_arg" ]; then
                echo "❌ Service name required"
                show_usage
                exit 1
            fi
            check_systemd_privileges "$command"
            local service=$(resolve_service_name "$service_arg")
            enable_service "$service"
            ;;
        "disable")
            if [ -z "$service_arg" ]; then
                echo "❌ Service name required"
                show_usage
                exit 1
            fi
            check_systemd_privileges "$command"
            local service=$(resolve_service_name "$service_arg")
            disable_service "$service"
            ;;
        "health")
            if [ -z "$service_arg" ]; then
                health_check "$ROBOT_SERVICE"
                echo ""
                health_check "$WEBAPP_SERVICE"
            else
                local service=$(resolve_service_name "$service_arg")
                health_check "$service"
            fi
            ;;
        "start-all")
            check_systemd_privileges "$command"
            start_service "$ROBOT_SERVICE"
            echo ""
            start_service "$WEBAPP_SERVICE"
            ;;
        "stop-all")
            check_systemd_privileges "$command"
            stop_service "$ROBOT_SERVICE"
            echo ""
            stop_service "$WEBAPP_SERVICE"
            ;;
        "restart-all")
            check_systemd_privileges "$command"
            restart_service "$ROBOT_SERVICE"
            echo ""
            restart_service "$WEBAPP_SERVICE"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"