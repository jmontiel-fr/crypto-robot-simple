#!/bin/bash

# EC2 Package Installation Script
# This script should be run as root (with sudo)
# Usage: sudo ./install-pkges.sh

# Log start
echo "$(date): Starting package installation script" >> /var/log/user-data.log

# Update system
if command -v dnf &> /dev/null; then
    echo "$(date): Using dnf package manager" >> /var/log/user-data.log
    dnf update -y
    PKG_MGR="dnf"
elif command -v yum &> /dev/null; then
    echo "$(date): Using yum package manager" >> /var/log/user-data.log
    yum update -y
    PKG_MGR="yum"
else
    echo "$(date): ERROR: No package manager found" >> /var/log/user-data.log
    exit 1
fi

# Install basic packages
echo "$(date): Installing basic packages" >> /var/log/user-data.log
if [ "$PKG_MGR" = "dnf" ]; then
    dnf install -y aws-cli git python3.12 python3.12-pip 
else
    yum install -y aws-cli git python3 python3-pip 
fi

# Create convenient symlinks for python command
# Check which Python version is available and create symlinks
if command -v python3.12 &> /dev/null; then
     # Create symlinks in both /usr/bin and /usr/local/bin for immediate availability
     ln -sf $(which python3.12) /usr/bin/python
     ln -sf $(which python3.12) /usr/bin/python3
     ln -sf $(which python3.12) /usr/local/bin/python
     ln -sf $(which python3.12) /usr/local/bin/python3
    PYTHON_CMD="python3.12"
    PYTHON_PATH=$(which python3.12)
elif command -v python3 &> /dev/null; then
     # Create symlinks in both /usr/bin and /usr/local/bin for immediate availability
     ln -sf $(which python3) /usr/bin/python
     ln -sf $(which python3) /usr/local/bin/python
     PYTHON_CMD="python3"
     PYTHON_PATH=$(which python3)
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

# Create a profile script that ensures python is available system-wide
echo 'export PATH="/usr/local/bin:$PATH"' > /etc/profile.d/python-path.sh
chmod +x /etc/profile.d/python-path.sh

# Ensure pip is up to date for Python 3.12
$PYTHON_CMD -m pip install --upgrade pip

# Generate SSH key for ec2-user to access GitHub
sudo -u ec2-user ssh-keygen -t rsa -b 4096 -f /home/ec2-user/.ssh/id_rsa -N "" -C "ec2-crypto-robot@aws.com"
sudo -u ec2-user chmod 600 /home/ec2-user/.ssh/id_rsa
sudo -u ec2-user chmod 644 /home/ec2-user/.ssh/id_rsa.pub

# Configure Git for ec2-user
sudo you install git
sudo -u ec2-user git config --global user.name "Crypto Robot EC2"
sudo -u ec2-user git config --global user.email "ec2-crypto-robot@aws.com"

# Create a test file to verify S3 access (if S3_BUCKET_NAME is provided)
S3_BUCKET_NAME="${s3_bucket_name}"
if [ ! -z "$S3_BUCKET_NAME" ]; then
    echo "Hello from EC2 instance - $(date)" > /tmp/test-file.txt
    aws s3 cp /tmp/test-file.txt s3://$S3_BUCKET_NAME/test-file.txt
    echo "$(date): S3 test file uploaded to $S3_BUCKET_NAME" >> /var/log/user-data.log
fi

# Log installation status
echo "$(date): System setup started" >> /var/log/user-data.log
echo "$(date): Package manager: $(which dnf >/dev/null && echo 'dnf' || echo 'yum')" >> /var/log/user-data.log
echo "$(date): Git version: $(git --version 2>/dev/null || echo 'not installed')" >> /var/log/user-data.log
echo "$(date): AWS CLI version: $(aws --version 2>/dev/null || echo 'not installed')" >> /var/log/user-data.log
echo "$(date): Python version: $(python --version 2>/dev/null || echo 'not available')" >> /var/log/user-data.log
echo "$(date): Python3 version: $(python3 --version 2>/dev/null || echo 'not available')" >> /var/log/user-data.log
echo "$(date): Python 3.12 version: $(python3.12 --version 2>/dev/null || echo 'not installed')" >> /var/log/user-data.log
echo "$(date): Pip version: $(pip --version 2>/dev/null || echo 'not available')" >> /var/log/user-data.log
echo "$(date): Python symlinks: $(ls -la /usr/bin/python* 2>/dev/null || echo 'no symlinks found')" >> /var/log/user-data.log
echo "$(date): System setup completed" >> /var/log/user-data.log

echo "Package installation completed successfully!"
