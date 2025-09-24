#!/bin/bash

# EC2 Package Installation Script with Error Handling
# Log start
echo "$(date): Starting package installation script" >> /var/log/user-data.log

# Determine package manager without updating system first
if command -v dnf &> /dev/null; then
    echo "$(date): Using dnf package manager" >> /var/log/user-data.log
    PKG_MGR="dnf"
elif command -v yum &> /dev/null; then
    echo "$(date): Using yum package manager" >> /var/log/user-data.log
    PKG_MGR="yum"
else
    echo "$(date): ERROR: No package manager found" >> /var/log/user-data.log
    exit 1
fi

# Skip system update to avoid breaking core utilities
# System updates can sometimes corrupt essential commands
echo "$(date): Skipping system update to preserve system stability" >> /var/log/user-data.log

# Install basic packages including core utilities
echo "$(date): Installing basic packages" >> /var/log/user-data.log
if [ "$PKG_MGR" = "dnf" ]; then
    dnf install -y coreutils util-linux aws-cli git python3.12 python3.12-pip docker wget unzip coreutils
else
    yum install -y coreutils util-linux aws-cli git python3 python3-pip docker wget unzip coreutils
fi

# Start and enable Docker service
echo "$(date): Starting Docker service" >> /var/log/user-data.log
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
echo "$(date): Adding ec2-user to docker group" >> /var/log/user-data.log
usermod -a -G docker ec2-user

# Create convenient symlinks for python command
if command -v python3.12 &> /dev/null; then
    ln -sf $(which python3.12) /usr/bin/python
    ln -sf $(which python3.12) /usr/local/bin/python
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    ln -sf $(which python3) /usr/bin/python
    ln -sf $(which python3) /usr/local/bin/python
    PYTHON_CMD="python3"
fi

# Also create pip symlink if available
if command -v pip3.12 &> /dev/null; then
    ln -sf $(which pip3.12) /usr/bin/pip
    ln -sf $(which pip3.12) /usr/local/bin/pip
elif command -v pip3 &> /dev/null; then
    ln -sf $(which pip3) /usr/bin/pip
    ln -sf $(which pip3) /usr/local/bin/pip
fi

# Update PATH to include /usr/local/bin
echo 'export PATH="/usr/local/bin:$PATH"' >> /home/ec2-user/.bashrc
echo 'export PATH="/usr/local/bin:$PATH"' >> /root/.bashrc

# Create a profile script that ensures tools are available system-wide
echo 'export PATH="/usr/local/bin:$PATH"' > /etc/profile.d/custom-path.sh
chmod +x /etc/profile.d/custom-path.sh

# Ensure pip is up to date
$PYTHON_CMD -m pip install --upgrade pip

# Generate SSH key for ec2-user to access GitHub
sudo -u ec2-user ssh-keygen -t rsa -b 4096 -f /home/ec2-user/.ssh/id_rsa -N "" -C "ec2-crypto-robot@aws.com"
sudo -u ec2-user chmod 600 /home/ec2-user/.ssh/id_rsa
sudo -u ec2-user chmod 644 /home/ec2-user/.ssh/id_rsa.pub

# Configure Git for ec2-user
sudo -u ec2-user git config --global user.name "Crypto Robot EC2"
sudo -u ec2-user git config --global user.email "ec2-crypto-robot@aws.com"

# Install latest Terraform with robust error handling
echo "$(date): Installing latest Terraform" >> /var/log/user-data.log
cd /tmp

# Get latest Terraform version with multiple attempts
TERRAFORM_VERSION=""
for i in {1..3}; do
    TERRAFORM_VERSION=$(curl -s --connect-timeout 10 https://api.github.com/repos/hashicorp/terraform/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')
    if [ -n "$TERRAFORM_VERSION" ]; then
        break
    fi
    echo "$(date): Attempt $i to get Terraform version failed, retrying..." >> /var/log/user-data.log
    sleep 5
done

# Use fallback version if API call failed
if [ -z "$TERRAFORM_VERSION" ]; then
    echo "$(date): Failed to get latest version, using fallback" >> /var/log/user-data.log
    TERRAFORM_VERSION="1.9.5"
fi

echo "$(date): Installing Terraform version: $TERRAFORM_VERSION" >> /var/log/user-data.log

# Download Terraform with retries
DOWNLOAD_SUCCESS=false
for i in {1..3}; do
    wget -q --timeout=30 https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
    if [ $? -eq 0 ] && [ -f "terraform_${TERRAFORM_VERSION}_linux_amd64.zip" ]; then
        DOWNLOAD_SUCCESS=true
        break
    fi
    echo "$(date): Download attempt $i failed, retrying..." >> /var/log/user-data.log
    sleep 5
done

if [ "$DOWNLOAD_SUCCESS" = false ]; then
    echo "$(date): ERROR: Failed to download Terraform after 3 attempts" >> /var/log/user-data.log
    exit 1
fi

# Extract Terraform
unzip -q terraform_${TERRAFORM_VERSION}_linux_amd64.zip
if [ $? -ne 0 ]; then
    echo "$(date): ERROR: Failed to extract Terraform" >> /var/log/user-data.log
    exit 1
fi

# Verify terraform binary exists
if [ ! -f "terraform" ]; then
    echo "$(date): ERROR: Terraform binary not found after extraction" >> /var/log/user-data.log
    exit 1
fi

# Install Terraform
mv terraform /usr/local/bin/
chmod +x /usr/local/bin/terraform
rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Verify installation
if [ ! -f "/usr/local/bin/terraform" ]; then
    echo "$(date): ERROR: Terraform binary not found after installation" >> /var/log/user-data.log
    exit 1
fi

# Create multiple PATH configurations for maximum compatibility
echo 'export PATH="/usr/local/bin:$PATH"' >> /etc/environment
echo 'export PATH="/usr/local/bin:$PATH"' > /etc/profile.d/terraform-path.sh
chmod +x /etc/profile.d/terraform-path.sh

# Create symlink in standard location
ln -sf /usr/local/bin/terraform /usr/bin/terraform

# Test Terraform installation
export PATH="/usr/local/bin:$PATH"
TERRAFORM_TEST=$(/usr/local/bin/terraform --version 2>&1)
if [ $? -eq 0 ]; then
    echo "$(date): Terraform installation verified: $TERRAFORM_TEST" >> /var/log/user-data.log
else
    echo "$(date): ERROR: Terraform installation verification failed: $TERRAFORM_TEST" >> /var/log/user-data.log
fi

# Log final installation status
echo "$(date): System setup completed" >> /var/log/user-data.log
echo "$(date): Package manager: $(which dnf >/dev/null && echo 'dnf' || echo 'yum')" >> /var/log/user-data.log
echo "$(date): Git version: $(git --version 2>/dev/null || echo 'not installed')" >> /var/log/user-data.log
echo "$(date): AWS CLI version: $(aws --version 2>/dev/null || echo 'not installed')" >> /var/log/user-data.log
echo "$(date): Python version: $(python --version 2>/dev/null || echo 'not available')" >> /var/log/user-data.log
echo "$(date): Python3 version: $(python3 --version 2>/dev/null || echo 'not available')" >> /var/log/user-data.log
echo "$(date): Python 3.12 version: $(python3.12 --version 2>/dev/null || echo 'not installed')" >> /var/log/user-data.log
echo "$(date): Pip version: $(pip --version 2>/dev/null || echo 'not available')" >> /var/log/user-data.log
echo "$(date): Docker version: $(docker --version 2>/dev/null || echo 'not installed')" >> /var/log/user-data.log
echo "$(date): Docker service status: $(systemctl is-active docker 2>/dev/null || echo 'not running')" >> /var/log/user-data.log
echo "$(date): Terraform version: $(/usr/local/bin/terraform --version 2>/dev/null | head -n1 || echo 'not installed')" >> /var/log/user-data.log

echo "Package installation completed successfully!"