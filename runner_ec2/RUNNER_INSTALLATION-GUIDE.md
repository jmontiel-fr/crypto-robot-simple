# GitHub Actions Self-Hosted Runner Installation Guide

This guide provides complete instructions for installing and configuring a GitHub Actions self-hosted runner on an EC2 instance.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Terraform Integration](#terraform-integration)
3. [EC2 Instance Setup](#ec2-instance-setup)
4. [GitHub Repository Configuration](#github-repository-configuration)
5. [Runner Installation](#runner-installation)
6. [Service Configuration](#service-configuration)
7. [Workflow Configuration](#workflow-configuration)
8. [Testing](#testing)
9. [Maintenance](#maintenance)
10. [Uninstallation](#uninstallation)
11. [Troubleshooting](#troubleshooting)

## ✅ Prerequisites

### EC2 Instance Requirements

- **Instance Type**: t3.medium or larger (recommended)
- **Operating System**: Amazon Linux 2023
- **Storage**: At least 20GB EBS volume
- **Network**: Outbound HTTPS (443) access to GitHub
- **IAM Role**: EC2 instance with appropriate AWS permissions

### Required Tools on EC2

- Docker (latest)
- Git (latest)
- Terraform (latest) - optional
- AWS CLI v2 (latest) - optional

### GitHub Repository Requirements

- **Admin access** to the repository
- **Actions enabled** in repository settings

## 🚀 EC2 Instance Setup

### Step 1: Launch EC2 Instance

If you're using the provided Terraform configuration:

#### Using Terraform (Recommended)

1. **Deploy infrastructure** using the build-robot-infra workflow:

   - Go to GitHub Actions → "Build Robot Infrastructure"
   - Click "Run workflow"
   - Action: `apply`
   - Auto-approve: `true`
   - Click "Run workflow"
2. **Get the Elastic IP** from Terraform outputs:

   ```bash
   # Navigate to terraform directory
   cd terraform

   # Get all outputs
   terraform output

   # Get specific EIP address
   terraform output ec2_eip_address

   # Example output: "18.200.57.167"
   ```
3. **Connect via SSH** using the EIP:

   ```bash
   # Navigate to terraform directory first
   cd terraform

   # Export EIP as environment variable for easier use
   export EC2_IP=$(terraform output -raw ec2_eip_address)

   # Connect using the exported variable
   ssh -i web-crypto-robot-key.pem ec2-user@$EC2_IP

   # Alternative: Direct connection
   ssh -i web-crypto-robot-key.pem ec2-user@$(terraform output -raw ec2_eip_address)
   ```
4. **Handle SSH key conflicts** (if EC2 instance was recreated):

   ```bash
   # Remove old host key if EC2 instance was recreated
   ssh-keygen -R $EC2_IP

   # Then connect normally
   ssh -i web-crypto-robot-key.pem ec2-user@$EC2_IP
   ```

#### Manual EC2 Launch

If launching manually:

1. **Launch EC2 instance** with Amazon Linux 2023
2. **Configure security group** to allow outbound HTTPS (port 443)
3. **Attach IAM role** with necessary AWS permissions
4. **Allocate Elastic IP** and associate with instance
5. **Connect via SSH** using the EIP

### Step 2: Install Required Tools (optional)

Not required if already in EC2!

```bash
# check if required
docker --version
git --version
aws --version
python -V
terraform --version

# Update system
sudo dnf update -y

# Install Docker
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Git (usually pre-installed)
sudo dnf install -y git

# Install AWS CLI v2 (optional)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/

# Install Terraform (optional)
TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')
wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip
sudo mv terraform /usr/local/bin/
rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Verify installations
docker --version
git --version
aws --version
python -V
terraform --version
```

### Step 3: Logout and Login

```bash
# Logout and login again to apply docker group membership
exit

# SSH back in using Terraform EIP output
ssh -i terraform/web-crypto-robot-key.pem ec2-user@$(terraform output -raw ec2_eip_address)

# Or manually with the IP address
ssh -i your-key.pem ec2-user@your-ec2-ip
```

## 🔧 GitHub Repository Configuration

### Step 1: Enable Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Ensure **"Allow all actions and reusable workflows"** is selected

### Step 2: Get Runner Registration Token

1. Go to **Settings** → **Actions** → **Runners**
2. Click **"New self-hosted runner"**
3. Select **"Linux"**
4. **Copy the token** from the configuration command (starts with `A`)

## 🏃 Runner Installation

### Step 1: Create Runner Directory

```bash
# Create runner directory
sudo mkdir -p /opt/github-runner
sudo chown ec2-user:ec2-user /opt/github-runner
cd /opt/github-runner
```

### Step 2: Download GitHub Actions Runner

```bash
# Download latest runner (check https://github.com/actions/runner/releases for latest version)
RUNNER_VERSION="2.328.0"
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Extract runner
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
```

### Step 3: Install Dependencies

```bash
# Install runner dependencies
sudo ./bin/installdependencies.sh
```

### Step 4: Configure Runner

```bash
# Configure runner (replace YOUR_TOKEN with the token from GitHub)
./config.sh \
  --url https://github.com/jmontiel-fr/crypto-robot \
  --token AGBPJ3DFWUDHR7634XMH5SDIZUBTU \
  --name aws-runner \
  --labels self-hosted,linux,x64,aws \
  --work _work
```

**Configuration Prompts:**

- **Runner group**: Press Enter (use default)
- **Runner name**: Enter a descriptive name or press Enter for default
- **Additional labels**: Add custom labels (comma-separated)
- **Work folder**: Press Enter (use default `_work`)

## ⚙️ Service Configuration

### Step 1: Install as System Service

```bash
# Install runner as systemd service
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Enable auto-start on boot
sudo systemctl enable actions.runner.*
```

### Step 2: Verify Service

```bash
# Check service status
sudo ./svc.sh status

# Check systemd status
sudo systemctl status actions.runner.*

# View logs
sudo journalctl -u actions.runner.* -f
```

## 📝 Workflow Configuration

### Update Workflow Files

Update your `.github/workflows/*.yml` files to use the self-hosted runner:

```yaml
jobs:
  your-job:
    runs-on: [self-hosted, linux, x64, aws]  # Use your runner labels
  
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Use pre-installed tools
      run: |
        # Tools are already installed on the runner
        terraform --version
        aws --version
        docker --version
```

### Authentication Configuration

For AWS authentication, you have two options:

#### Option 1: Use EC2 IAM Role (Recommended)

```yaml
- name: Configure AWS credentials
  run: |
    # AWS credentials provided via EC2 IAM role
    aws sts get-caller-identity
```

#### Option 2: Use GitHub Secrets

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
```

## 🧪 Testing

### Step 1: Verify Runner in GitHub

1. Go to **Settings** → **Actions** → **Runners**
2. Your runner should appear with a **green dot** and **"Idle"** status

### Step 2: Test Workflow

Create a simple test workflow:

```yaml
name: Test Self-Hosted Runner

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: [self-hosted, linux, x64, aws]
  
    steps:
    - name: Test runner
      run: |
        echo "Runner is working!"
        whoami
        pwd
        df -h
        docker --version
        terraform --version || echo "Terraform not installed"
        aws --version || echo "AWS CLI not installed"
```

### Step 3: Run Test Workflow

1. Go to **Actions** tab in your repository
2. Select **"Test Self-Hosted Runner"**
3. Click **"Run workflow"**
4. Verify it runs on your self-hosted runner

## 🔄 Maintenance

### Regular Tasks

#### Check Runner Status

```bash
# SSH to EC2 instance using Terraform EIP
ssh -i terraform/web-crypto-robot-key.pem ec2-user@$(terraform output -raw ec2_eip_address)

# Check service status
cd /opt/github-runner
sudo ./svc.sh status

# View logs
sudo journalctl -u actions.runner.* --since "1 hour ago"
```

#### Update Runner

```bash
# Stop service
sudo ./svc.sh stop

# Download new version
RUNNER_VERSION="2.312.0"  # Check latest version
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Extract (overwrites existing files)
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Start service
sudo ./svc.sh start
```

#### Clean Up Work Directory

```bash
# Clean old workflow runs (optional)
cd /opt/github-runner/_work
sudo rm -rf */
```

### Monitoring

#### Service Health

```bash
# Check if runner is responding
sudo ./svc.sh status

# Check system resources
htop
df -h
free -h
```

#### GitHub Status

- Monitor runner status in GitHub repository settings
- Check for "Offline" status and investigate if needed

## 🗑️ Uninstallation

### Automated Uninstallation

Use the provided uninstall script:

```bash
# Download and run uninstall script
curl -o uninstall-runner.sh https://raw.githubusercontent.com/YOUR_OWNER/YOUR_REPO/main/runner_ec2/uninstall-runner.sh
chmod +x uninstall-runner.sh
./uninstall-runner.sh
```

### Manual Uninstallation

If you prefer manual removal:

```bash
# Stop and uninstall service
cd /opt/github-runner
sudo ./svc.sh stop
sudo ./svc.sh uninstall

# Remove from GitHub (get removal token from GitHub settings)
./config.sh remove --token YOUR_REMOVAL_TOKEN

# Remove runner directory
sudo rm -rf /opt/github-runner

# Remove systemd files
sudo rm -f /etc/systemd/system/actions.runner.*
sudo systemctl daemon-reload
```

## 💡 Connection Hints

### Quick Connection Commands

```bash
# Navigate to terraform directory
cd terraform

# Export EIP for easier use
export EC2_IP=$(terraform output -raw ec2_eip_address)

# Connect to EC2 instance
ssh -i web-crypto-robot-key.pem ec2-user@$EC2_IP
```

### Handle EC2 Recreation

When EC2 instance is recreated (via terraform apply), the SSH host key changes:

```bash
# Remove old host key to avoid SSH warnings
ssh-keygen -R $EC2_IP

# Then connect normally
ssh -i web-crypto-robot-key.pem ec2-user@$EC2_IP
```

### Useful One-Liners

```bash
# Get EIP and connect in one command
ssh -i terraform/web-crypto-robot-key.pem ec2-user@$(cd terraform && terraform output -raw ec2_eip_address)

# Copy files to EC2 using EIP
scp -i terraform/web-crypto-robot-key.pem file.txt ec2-user@$(cd terraform && terraform output -raw ec2_eip_address):~/

# Execute command on EC2 remotely
ssh -i terraform/web-crypto-robot-key.pem ec2-user@$(cd terraform && terraform output -raw ec2_eip_address) "docker --version"
```

### Terraform Output Commands

```bash
# Get all terraform outputs
terraform output

# Get specific outputs
terraform output ec2_eip_address        # Elastic IP
terraform output ec2_instance_id        # Instance ID
terraform output s3_bucket_name         # S3 bucket
terraform output security_group_id      # Security group
```

## 🔧 Troubleshooting

### Common Issues

#### Runner Shows as Offline

**Symptoms:** Runner appears offline in GitHub

**Solutions:**

1. Check service status: `sudo ./svc.sh status`
2. Check network connectivity: `curl -I https://github.com`
3. Restart service: `sudo ./svc.sh stop && sudo ./svc.sh start`
4. Check logs: `sudo journalctl -u actions.runner.* -f`

#### Workflows Don't Use Self-Hosted Runner

**Symptoms:** Workflows run on GitHub hosted runners

**Solutions:**

1. Verify workflow uses correct `runs-on` labels
2. Check runner labels match workflow requirements
3. Ensure runner is "Idle" and available

#### Permission Errors

**Symptoms:** Runner can't access files or execute commands

**Solutions:**

1. Check file permissions: `ls -la /opt/github-runner/`
2. Ensure ec2-user owns runner directory: `sudo chown -R ec2-user:ec2-user /opt/github-runner`
3. Check docker group membership: `groups ec2-user`

#### Service Won't Start

**Symptoms:** Runner service fails to start

**Solutions:**

1. Check service logs: `sudo journalctl -u actions.runner.* -f`
2. Verify configuration: `./config.sh --check`
3. Re-install service: `sudo ./svc.sh uninstall && sudo ./svc.sh install`

### Getting Help

#### Log Files

```bash
# Service logs
sudo journalctl -u actions.runner.* -f

# Runner logs
tail -f /opt/github-runner/_diag/Runner_*.log

# System logs
sudo journalctl -f
```

#### Diagnostic Commands

```bash
# Check runner configuration
cd /opt/github-runner
cat .runner

# Check network connectivity
curl -v https://api.github.com

# Check system resources
df -h
free -h
ps aux | grep Runner
```

## 📚 Additional Resources

- [GitHub Actions Self-Hosted Runners Documentation](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Runner Releases](https://github.com/actions/runner/releases)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)

## 🔐 Security Considerations

### Best Practices

1. **Isolate Runner Environment**

   - Use dedicated EC2 instance for runners
   - Implement proper network security groups
   - Regular security updates
2. **Monitor Runner Activity**

   - Regular log review
   - Monitor for unexpected workflow executions
   - Set up CloudWatch alerts
3. **Keep Runner Updated**

   - Update runner software regularly
   - Monitor GitHub security advisories
   - Update EC2 instance packages
4. **Limit Repository Access**

   - Use repository-specific runners when possible
   - Regularly rotate runner registration tokens
   - Monitor runner usage patterns

---

**Last Updated:** December 2024
**Version:** 1.0
