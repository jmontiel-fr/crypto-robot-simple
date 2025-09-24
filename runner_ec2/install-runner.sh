#!/bin/bash
# Install GitHub Actions Self-Hosted Runner on EC2
# This script automates the complete installation process

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

# Configuration variables
RUNNER_VERSION="2.311.0"  # Update this to latest version
RUNNER_DIR="/opt/github-runner"
RUNNER_USER="ec2-user"

print_header "GITHUB ACTIONS SELF-HOSTED RUNNER INSTALLER"

echo "This script will install and configure a GitHub Actions self-hosted runner on this EC2 instance."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root. Run as ec2-user."
    exit 1
fi

# Check if runner already exists
if [ -d "$RUNNER_DIR" ]; then
    print_error "Runner directory already exists at $RUNNER_DIR"
    print_info "If you want to reinstall, first run the uninstall script."
    exit 1
fi

# Get GitHub repository information
print_header "STEP 1: REPOSITORY CONFIGURATION"

if [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "Please provide the following information:"
    echo ""
    
    if [ -z "$GITHUB_OWNER" ]; then
        read -p "GitHub Owner/Organization: " GITHUB_OWNER
    fi
    
    if [ -z "$GITHUB_REPO" ]; then
        read -p "GitHub Repository Name: " GITHUB_REPO
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo ""
        echo "To get a registration token:"
        echo "1. Go to: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/settings/actions/runners"
        echo "2. Click 'New self-hosted runner'"
        echo "3. Select 'Linux'"
        echo "4. Copy the token from the configuration command"
        echo ""
        read -p "GitHub Registration Token: " GITHUB_TOKEN
    fi
fi

# Validate inputs
if [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ] || [ -z "$GITHUB_TOKEN" ]; then
    print_error "Missing required information. Please provide GitHub owner, repo, and token."
    exit 1
fi

print_status "Repository: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}"

# Get runner name and labels
if [ -z "$RUNNER_NAME" ]; then
    RUNNER_NAME="${GITHUB_REPO}-ec2-runner"
    read -p "Runner Name [$RUNNER_NAME]: " INPUT_NAME
    if [ -n "$INPUT_NAME" ]; then
        RUNNER_NAME="$INPUT_NAME"
    fi
fi

if [ -z "$RUNNER_LABELS" ]; then
    RUNNER_LABELS="self-hosted,linux,x64,aws"
    read -p "Runner Labels [$RUNNER_LABELS]: " INPUT_LABELS
    if [ -n "$INPUT_LABELS" ]; then
        RUNNER_LABELS="$INPUT_LABELS"
    fi
fi

print_header "STEP 2: SYSTEM PREPARATION"

# Update system
print_info "Updating system packages..."
sudo dnf update -y

# Install required packages
print_info "Installing required packages..."
sudo dnf install -y wget unzip curl git

print_header "STEP 3: INSTALL DEVELOPMENT TOOLS"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    sudo dnf install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ec2-user
    print_status "Docker installed"
else
    print_status "Docker already installed"
fi

# Install AWS CLI v2 if not present
if ! command -v aws &> /dev/null; then
    print_info "Installing AWS CLI v2..."
    cd /tmp
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws/
    print_status "AWS CLI v2 installed"
else
    print_status "AWS CLI already installed"
fi

# Install Terraform if not present
if ! command -v terraform &> /dev/null; then
    print_info "Installing Terraform..."
    cd /tmp
    TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')
    wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
    unzip -q terraform_${TERRAFORM_VERSION}_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
    rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip
    print_status "Terraform installed"
else
    print_status "Terraform already installed"
fi

print_header "STEP 4: DOWNLOAD AND SETUP RUNNER"

# Create runner directory
print_info "Creating runner directory..."
sudo mkdir -p "$RUNNER_DIR"
sudo chown "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Download GitHub Actions Runner
print_info "Downloading GitHub Actions Runner v${RUNNER_VERSION}..."
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"

# Extract runner
print_info "Extracting runner..."
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Install dependencies
print_info "Installing runner dependencies..."
sudo ./bin/installdependencies.sh

print_header "STEP 5: CONFIGURE RUNNER"

# Configure runner
print_info "Configuring GitHub Actions runner..."
./config.sh \
  --url "https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}" \
  --token "$GITHUB_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --work "_work" \
  --unattended

if [ $? -eq 0 ]; then
    print_status "Runner configured successfully"
else
    print_error "Runner configuration failed"
    exit 1
fi

print_header "STEP 6: INSTALL AS SERVICE"

# Install as service
print_info "Installing runner as system service..."
sudo ./svc.sh install

if [ $? -eq 0 ]; then
    print_status "Service installed successfully"
else
    print_error "Service installation failed"
    exit 1
fi

# Start service
print_info "Starting runner service..."
sudo ./svc.sh start

if [ $? -eq 0 ]; then
    print_status "Service started successfully"
else
    print_error "Service start failed"
    exit 1
fi

# Enable auto-start
print_info "Enabling auto-start on boot..."
sudo systemctl enable actions.runner.* 2>/dev/null || true

print_header "STEP 7: VERIFICATION"

# Wait for service to start
sleep 5

# Check service status
print_info "Checking service status..."
SERVICE_STATUS=$(sudo ./svc.sh status 2>&1)

if echo "$SERVICE_STATUS" | grep -q "active (running)"; then
    print_status "✅ Service is running!"
else
    print_error "❌ Service is not running properly"
    echo "Service status: $SERVICE_STATUS"
fi

# Check if runner process is running
if pgrep -f "Runner.Listener" > /dev/null; then
    print_status "✅ Runner process is active"
else
    print_error "❌ Runner process not found"
fi

print_header "INSTALLATION COMPLETE"

echo ""
echo "🎯 Installation Summary:"
echo "  • Repository: https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}"
echo "  • Runner Name: $RUNNER_NAME"
echo "  • Runner Labels: $RUNNER_LABELS"
echo "  • Installation Directory: $RUNNER_DIR"
echo ""

echo "🔧 Installed Tools:"
echo "  • Docker: $(docker --version 2>/dev/null || echo 'Not available')"
echo "  • AWS CLI: $(aws --version 2>/dev/null || echo 'Not available')"
echo "  • Terraform: $(terraform --version 2>/dev/null | head -n1 || echo 'Not available')"
echo "  • Git: $(git --version 2>/dev/null || echo 'Not available')"
echo ""

echo "📋 Next Steps:"
echo "1. Verify runner in GitHub:"
echo "   https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/settings/actions/runners"
echo "2. Look for '$RUNNER_NAME' with green dot (Idle status)"
echo "3. Update your workflows to use: runs-on: [self-hosted, linux, x64, aws]"
echo "4. Test a workflow to verify functionality"
echo ""

echo "🔍 Useful Commands:"
echo "  • Check status: sudo /opt/github-runner/svc.sh status"
echo "  • View logs: sudo journalctl -u actions.runner.* -f"
echo "  • Restart: sudo /opt/github-runner/svc.sh stop && sudo /opt/github-runner/svc.sh start"
echo ""

if sudo ./svc.sh status | grep -q "active (running)"; then
    print_status "🎉 INSTALLATION SUCCESSFUL!"
    echo ""
    echo "Your GitHub Actions self-hosted runner is now installed and running."
    echo "It will automatically start when the EC2 instance boots."
    echo ""
    echo "⚠️  IMPORTANT: You may need to logout and login again for Docker group membership to take effect."
else
    print_error "❌ INSTALLATION INCOMPLETE"
    echo ""
    echo "The runner was installed but the service is not running properly."
    echo "Check the logs with: sudo journalctl -u actions.runner.* -f"
fi