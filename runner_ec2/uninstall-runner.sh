#!/bin/bash
# Uninstall GitHub Actions Self-Hosted Runner from EC2
# This script completely removes the GitHub Actions runner and all related files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}🚀 $1${NC}"
}

print_header "GITHUB ACTIONS RUNNER UNINSTALLER"

echo "This script will completely remove the GitHub Actions runner from this EC2 instance."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root. Run as ec2-user."
    exit 1
fi

# Confirmation prompt
read -p "Are you sure you want to uninstall the GitHub Actions runner? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Uninstallation cancelled."
    exit 0
fi

print_header "STEP 1: STOPPING RUNNER SERVICE"

RUNNER_DIR="/opt/github-runner"

if [ -d "$RUNNER_DIR" ]; then
    cd "$RUNNER_DIR"
    
    # Stop the service
    if [ -f "./svc.sh" ]; then
        print_info "Stopping runner service..."
        sudo ./svc.sh stop 2>/dev/null && print_status "Service stopped" || print_info "Service was not running"
        
        # Uninstall the service
        print_info "Uninstalling runner service..."
        sudo ./svc.sh uninstall 2>/dev/null && print_status "Service uninstalled" || print_info "Service was not installed"
    else
        print_info "Service script not found, skipping service operations"
    fi
else
    print_info "Runner directory not found at $RUNNER_DIR"
fi

print_header "STEP 2: REMOVING RUNNER FROM GITHUB"

if [ -d "$RUNNER_DIR" ] && [ -f "$RUNNER_DIR/config.sh" ]; then
    cd "$RUNNER_DIR"
    
    print_info "Attempting to remove runner from GitHub..."
    print_info "Note: This requires a removal token from GitHub"
    
    echo ""
    echo "To get a removal token:"
    echo "1. Go to: https://github.com/YOUR_OWNER/YOUR_REPO/settings/actions/runners"
    echo "2. Find your runner in the list"
    echo "3. Click the ... menu next to your runner"
    echo "4. Click 'Remove'"
    echo "5. Copy the removal token"
    echo ""
    
    read -p "Do you have a removal token? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter the removal token: " REMOVAL_TOKEN
        if [ -n "$REMOVAL_TOKEN" ]; then
            print_info "Removing runner from GitHub..."
            ./config.sh remove --token "$REMOVAL_TOKEN" && print_status "Runner removed from GitHub" || print_error "Failed to remove runner from GitHub"
        else
            print_info "No token provided, skipping GitHub removal"
        fi
    else
        print_info "Skipping GitHub removal - you can remove it manually from the GitHub web interface"
    fi
else
    print_info "Runner config not found, skipping GitHub removal"
fi

print_header "STEP 3: KILLING RUNNER PROCESSES"

# Kill any running runner processes
print_info "Stopping any running runner processes..."
pkill -f "Runner.Listener" 2>/dev/null && print_status "Killed runner processes" || print_info "No runner processes found"
pkill -f "Runner.Worker" 2>/dev/null && print_status "Killed worker processes" || print_info "No worker processes found"

print_header "STEP 4: REMOVING SYSTEMD SERVICE FILES"

# Remove systemd service files
print_info "Removing systemd service files..."
sudo rm -f /etc/systemd/system/actions.runner.* 2>/dev/null && print_status "Removed systemd service files" || print_info "No systemd service files found"

# Reload systemd
sudo systemctl daemon-reload
print_status "Reloaded systemd configuration"

print_header "STEP 5: REMOVING RUNNER DIRECTORY"

# Remove the entire runner directory
if [ -d "$RUNNER_DIR" ]; then
    print_info "Removing runner directory: $RUNNER_DIR"
    sudo rm -rf "$RUNNER_DIR"
    print_status "Runner directory removed"
else
    print_info "Runner directory already removed"
fi

print_header "STEP 6: CLEANING UP TEMPORARY FILES"

# Clean up temporary files
print_info "Cleaning up temporary files..."
sudo rm -rf /tmp/actions-runner-* 2>/dev/null || true
rm -f ~/actions-runner-linux-x64-*.tar.gz 2>/dev/null || true
print_status "Temporary files cleaned"

print_header "STEP 7: REMOVING RUNNER USER (IF EXISTS)"

# Remove runner user if it was created
if id "actions-runner" &>/dev/null; then
    print_info "Removing actions-runner user..."
    sudo userdel -r actions-runner 2>/dev/null || true
    print_status "Removed actions-runner user"
fi

if getent group "actions-runner" &>/dev/null; then
    print_info "Removing actions-runner group..."
    sudo groupdel actions-runner 2>/dev/null || true
    print_status "Removed actions-runner group"
fi

print_header "STEP 8: CLEANING UP LOGS"

# Clean up logs
print_info "Cleaning up runner logs..."
sudo rm -rf /var/log/actions-runner* 2>/dev/null || true
sudo journalctl --vacuum-time=1d 2>/dev/null || true
print_status "Logs cleaned up"

print_header "STEP 9: VERIFICATION"

echo ""
echo "📋 Uninstallation Verification:"

# Check if runner directory exists
if [ -d "$RUNNER_DIR" ]; then
    print_error "❌ Runner directory still exists: $RUNNER_DIR"
else
    print_status "✅ Runner directory removed"
fi

# Check for runner processes
if pgrep -f "Runner" > /dev/null 2>&1; then
    print_error "❌ Runner processes still running:"
    pgrep -f "Runner"
else
    print_status "✅ No runner processes found"
fi

# Check for systemd services
if systemctl list-units --all | grep -q "actions.runner"; then
    print_error "❌ Systemd services still exist:"
    systemctl list-units --all | grep "actions.runner"
else
    print_status "✅ No systemd services found"
fi

# Check for runner user
if id "actions-runner" &>/dev/null; then
    print_error "❌ Runner user still exists"
else
    print_status "✅ No runner user found"
fi

print_header "UNINSTALLATION COMPLETE"

echo ""
echo "🎯 What was removed:"
echo "  • GitHub Actions runner service"
echo "  • Runner directory ($RUNNER_DIR)"
echo "  • Systemd service files"
echo "  • Runner processes"
echo "  • Temporary installation files"
echo "  • Runner user and group (if they existed)"
echo "  • Runner logs"
echo ""

echo "🔧 What remains installed:"
echo "  • Terraform: $(terraform --version 2>/dev/null | head -n1 || echo 'Not installed')"
echo "  • AWS CLI: $(aws --version 2>/dev/null || echo 'Not installed')"
echo "  • Docker: $(docker --version 2>/dev/null || echo 'Not installed')"
echo "  • Git: $(git --version 2>/dev/null || echo 'Not installed')"
echo ""

echo "📝 Manual cleanup required:"
echo "  • Remove the runner from GitHub web interface if not done automatically"
echo "  • Go to: https://github.com/YOUR_OWNER/YOUR_REPO/settings/actions/runners"
echo "  • Find your runner and click 'Remove' if it still appears"
echo ""

print_status "🎉 GitHub Actions runner has been completely uninstalled!"
echo ""
echo "Your EC2 instance is now clean but retains all useful development tools."