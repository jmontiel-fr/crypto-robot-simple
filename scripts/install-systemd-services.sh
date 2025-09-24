#!/bin/bash
# Install Crypto Robot Systemd Services

set -e

echo "⚙️  Installing Crypto Robot Systemd Services"
echo "============================================"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"
APP_PATH="/opt/crypto-robot"

# Function to check if running as root or with sudo
check_privileges() {
    if [ "$EUID" -ne 0 ]; then
        echo "❌ This script must be run as root or with sudo"
        echo "💡 Usage: sudo $0"
        exit 1
    fi
    echo "✅ Running with appropriate privileges"
}

# Function to validate service files
validate_service_files() {
    echo "🔍 Validating service files..."
    
    local robot_service="$SCRIPT_DIR/systemd/crypto-robot.service"
    local webapp_service="$SCRIPT_DIR/systemd/crypto-webapp.service"
    
    if [ ! -f "$robot_service" ]; then
        echo "❌ Robot service file not found: $robot_service"
        exit 1
    fi
    
    if [ ! -f "$webapp_service" ]; then
        echo "❌ WebApp service file not found: $webapp_service"
        exit 1
    fi
    
    echo "✅ Service files validated"
}

# Function to stop existing services
stop_existing_services() {
    echo "🛑 Stopping existing services (if running)..."
    
    for service in crypto-robot crypto-webapp; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo "🔄 Stopping $service..."
            systemctl stop "$service"
        fi
        
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo "🔄 Disabling $service..."
            systemctl disable "$service"
        fi
    done
    
    echo "✅ Existing services stopped"
}

# Function to install service files
install_service_files() {
    echo "📋 Installing service files..."
    
    # Copy service files to systemd directory
    cp "$SCRIPT_DIR/systemd/crypto-robot.service" "$SYSTEMD_DIR/"
    cp "$SCRIPT_DIR/systemd/crypto-webapp.service" "$SYSTEMD_DIR/"
    
    # Set proper permissions
    chmod 644 "$SYSTEMD_DIR/crypto-robot.service"
    chmod 644 "$SYSTEMD_DIR/crypto-webapp.service"
    
    echo "✅ Service files installed"
}

# Function to reload systemd
reload_systemd() {
    echo "🔄 Reloading systemd daemon..."
    systemctl daemon-reload
    echo "✅ Systemd daemon reloaded"
}

# Function to enable services
enable_services() {
    echo "⚡ Enabling services..."
    
    systemctl enable crypto-robot.service
    systemctl enable crypto-webapp.service
    
    echo "✅ Services enabled"
}

# Function to validate installation
validate_installation() {
    echo "🔍 Validating installation..."
    
    for service in crypto-robot crypto-webapp; do
        if systemctl is-enabled --quiet "$service"; then
            echo "✅ $service: enabled"
        else
            echo "❌ $service: not enabled"
            return 1
        fi
        
        # Check service file syntax
        if systemd-analyze verify "$SYSTEMD_DIR/$service.service" 2>/dev/null; then
            echo "✅ $service: syntax valid"
        else
            echo "❌ $service: syntax error"
            return 1
        fi
    done
    
    echo "✅ Installation validated"
}

# Function to display service status
show_service_status() {
    echo ""
    echo "📊 Service Status:"
    echo "=================="
    
    for service in crypto-robot crypto-webapp; do
        echo ""
        echo "🔍 $service:"
        echo "  Enabled: $(systemctl is-enabled $service 2>/dev/null || echo 'disabled')"
        echo "  Active: $(systemctl is-active $service 2>/dev/null || echo 'inactive')"
    done
    
    echo ""
}

# Function to display usage instructions
show_usage_instructions() {
    echo ""
    echo "🎉 Installation Complete!"
    echo "========================"
    echo ""
    echo "📋 Service Management Commands:"
    echo "  Start robot:     sudo systemctl start crypto-robot"
    echo "  Start webapp:    sudo systemctl start crypto-webapp"
    echo "  Stop robot:      sudo systemctl stop crypto-robot"
    echo "  Stop webapp:     sudo systemctl stop crypto-webapp"
    echo "  Restart robot:   sudo systemctl restart crypto-robot"
    echo "  Restart webapp:  sudo systemctl restart crypto-webapp"
    echo "  Status robot:    sudo systemctl status crypto-robot"
    echo "  Status webapp:   sudo systemctl status crypto-webapp"
    echo ""
    echo "📝 Log Files:"
    echo "  Robot logs:      /opt/crypto-robot/logs/robot-systemd.log"
    echo "  WebApp logs:     /opt/crypto-robot/logs/webapp-systemd.log"
    echo "  System logs:     journalctl -u crypto-robot -f"
    echo "                   journalctl -u crypto-webapp -f"
    echo ""
    echo "⚠️  Important Notes:"
    echo "  - Services are enabled and will start automatically on boot"
    echo "  - Ensure /opt/crypto-robot/.env file exists and is properly configured"
    echo "  - Ensure Python virtual environment is set up at /opt/crypto-robot/venv"
    echo "  - Services run as ec2-user with restricted permissions"
    echo ""
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --uninstall     Uninstall services"
    echo "  --status        Show service status"
    echo "  --help          Show this help message"
    echo ""
}

# Function to uninstall services
uninstall_services() {
    echo "🗑️  Uninstalling Crypto Robot Systemd Services"
    echo "=============================================="
    
    # Stop and disable services
    for service in crypto-robot crypto-webapp; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo "🛑 Stopping $service..."
            systemctl stop "$service"
        fi
        
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo "🔄 Disabling $service..."
            systemctl disable "$service"
        fi
        
        # Remove service file
        if [ -f "$SYSTEMD_DIR/$service.service" ]; then
            echo "🗑️  Removing $service.service..."
            rm -f "$SYSTEMD_DIR/$service.service"
        fi
    done
    
    # Reload systemd
    systemctl daemon-reload
    
    echo "✅ Services uninstalled successfully"
}

# Parse command line arguments
case "${1:-}" in
    --uninstall)
        check_privileges
        uninstall_services
        exit 0
        ;;
    --status)
        show_service_status
        exit 0
        ;;
    --help)
        show_usage
        exit 0
        ;;
    "")
        # Default installation
        ;;
    *)
        echo "❌ Unknown option: $1"
        show_usage
        exit 1
        ;;
esac

# Main installation flow
main() {
    echo "🚀 Starting systemd service installation..."
    
    check_privileges
    validate_service_files
    stop_existing_services
    install_service_files
    reload_systemd
    enable_services
    validate_installation
    show_service_status
    show_usage_instructions
    
    echo "🎉 Systemd service installation completed successfully!"
}

# Execute main function
main "$@"