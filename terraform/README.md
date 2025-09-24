# EC2 Infrastructure with S3 Access - Crypto Robot

This Terraform configuration creates an EC2 instance with S3 access in an existing VPC for the crypto robot project.

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (version >= 1.0)
3. An existing VPC with public subnets
4. A separate S3 bucket for Terraform state (if using remote backend)

**Note**: SSH key pair is automatically created by Terraform - no manual key creation needed!

## Files Description

- `providers.tf` - Terraform and AWS provider configuration
- `variables.tf` - Input variables for the configuration
- `locals.tf` - Local values and common configurations
- `data.tf` - Data sources to fetch existing VPC and subnet information
- `main.tf` - Main infrastructure resources (EC2, Security Group, IAM)
- `ssh-key.tf` - SSH key pair generation and management
- `s3.tf` - S3 bucket configuration
- `backend.tf` - Terraform backend configuration
- `outputs.tf` - Output values after deployment
- `terraform.tfvars.example` - Example variable values

## Setup Instructions

1. **Clone and navigate to the directory:**
   ```bash
   cd terraform
   ```

2. **Create your variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit terraform.tfvars with your actual values:**
   - `vpc_id`: Your existing VPC ID (default: vpc-0ee30813b6d1cd7fd)
   - `s3_bucket_name`: Unique S3 bucket name (default: crypto-robot-backups-059247592146)
   - `ssh_key_name`: SSH key pair name (default: web-crypto-robot-key) 
   - `allowed_cidrs`: CIDR blocks for SSH/HTTPS access (default includes company networks)
   - `region`: AWS region (default: eu-west-1)

4. **Update backend configuration (optional):**
   - Edit `backend.tf` with your state bucket details
   - Or comment out the backend block to use local state

5. **Initialize Terraform:**
   ```bash
   terraform init
   ```

6. **Plan the deployment:**
   ```bash
   terraform plan
   ```

7. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Resources Created

- **EC2 Instance**: t3.micro with Amazon Linux 2023
- **EBS Volume**: 100GB encrypted root volume (gp3)
- **Security Group**: Allows SSH (22), HTTP (80) and HTTPS (443) from specified CIDRs
- **SSH Key Pair**: Automatically generated RSA 4096-bit key pair
- **IAM Role & Policy**: Provides S3 read/write access to the EC2 instance
- **Instance Profile**: Links IAM role to EC2 instance
- **Elastic IP**: Static public IP address for the EC2 instance
- **S3 Bucket**: With versioning and encryption enabled
- **Python 3.12**: Installed with pip for running Python applications

## Security Features

- EC2 instance uses IAM roles (no hardcoded credentials)
- S3 bucket has public access blocked
- Security group restricts access to specified CIDR blocks (company networks)
- EBS volumes are encrypted with AWS managed keys
- S3 bucket has server-side encryption enabled
- SSH key pair is automatically generated and managed by Terraform
- Private key is stored locally with proper file permissions (0600)

## SSH Key Management

The Terraform configuration automatically:
- Generates a 4096-bit RSA key pair
- Creates the key pair in AWS EC2
- Saves the private key as `web-crypto-robot-key.pem` (with 0600 permissions)
- Saves the public key as `web-crypto-robot-key.pub` (with 0644 permissions)

**Important**: Keep the private key file secure and do not commit it to version control!

## Connecting to the Instance

After deployment, use the automatically generated private key:

```bash
# Method 1: Get the Elastic IP from Terraform outputs and set as environment variable
export EC2_IP=$(terraform output -raw ec2_eip_address)
ssh -i web-crypto-robot-key.pem ec2-user@$EC2_IP

# Method 2: Direct one-liner using Terraform output
ssh -i web-crypto-robot-key.pem ec2-user@$(terraform output -raw ec2_eip_address)

# Method 3: Manual connection (if you know the IP)
ssh -i web-crypto-robot-key.pem ec2-user@<elastic-ip-address>

# Method 4: Use the start-stop script which automatically shows the SSH command
./start-stop-ec2.sh status
```

**Tip**: The Elastic IP address remains consistent even when the instance is stopped and started.

## Managing the Instance

Use the provided script to easily start, stop, and check the status of your instance:

```bash
# Start the instance
./start-stop-ec2.sh start

# Stop the instance (saves costs when not in use)
./start-stop-ec2.sh stop

# Check instance status and get SSH command
./start-stop-ec2.sh status

# Smart toggle (start if stopped, stop if running)
./start-stop-ec2.sh toggle

# Get help
./start-stop-ec2.sh help
```

The script automatically uses the 'perso' AWS profile and provides the correct SSH command with the current IP address.

## Testing S3 Access

Once connected to the instance:
```bash
# List S3 buckets
aws s3 ls

# Test file upload
echo "test" > test.txt
aws s3 cp test.txt s3://your-bucket-name/
```

## Python Environment

The EC2 instance comes with Python 3.12 pre-installed with convenient command aliases. You can use any of these commands:

```bash
# All of these work and point to Python 3.12
python --version
python3 --version  
python3.12 --version

# Check pip version
python -m pip --version
pip --version

# Install Python packages
python -m pip install requests pandas numpy
pip install requests pandas numpy

# Create and run a simple Python script
echo 'print("Hello from Python 3.12!")' > test.py
python test.py
```

**Troubleshooting**: If `python` command is not found:
```bash
# Check if Python is installed
python3.12 --version

# If the above works but 'python' doesn't, try:
# 1. Check the symlinks
ls -la /usr/bin/python*

# 2. Manually reload your environment
source /etc/profile.d/python-path.sh
export PATH="/usr/local/bin:$PATH"

# 3. Check the user data installation log
sudo tail -n 20 /var/log/user-data.log

# 4. If needed, create the symlink manually
sudo ln -sf $(which python3.12) /usr/bin/python

# 5. Or reconnect to SSH to get fresh environment
exit
# Then SSH back in
```

## GitHub Repository Access

The EC2 instance is configured with Git and an SSH key pair for GitHub access. To clone your private repository:

1. **Get the SSH public key from the instance:**
   ```bash
   cat ~/.ssh/id_rsa.pub
   ```

2. **Add the public key to your GitHub account:**
   - Copy the output from the command above
   - Go to GitHub → Settings → SSH and GPG keys → New SSH key
   - Paste the public key and save

3. **Clone the repository using SSH:**
   ```bash
   git clone git@github.com:jmontiel-fr/crypto-robot.git
   ```

**Alternative: Using Personal Access Token (PAT)**
If you prefer HTTPS over SSH:
1. Create a Personal Access Token on GitHub (Settings → Developer settings → Personal access tokens)
2. Use the token when cloning:
   ```bash
   git clone https://your-token@github.com/jmontiel-fr/crypto-robot.git
   ```

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

## Notes

- The EC2 instance is placed in the first available public subnet
- An Elastic IP is assigned for consistent public IP addressing
- Make sure your VPC has public subnets with proper routing to an Internet Gateway
- S3 bucket names must be globally unique
- SSH key files are generated locally and should be kept secure
- The configuration uses company-specific CIDR blocks for security
- All resources are tagged consistently using local values
- Consider using more restrictive CIDR blocks for production environments

## File Structure

```
terraform/
├── providers.tf          # Terraform and provider configurations
├── variables.tf          # Input variables with defaults
├── locals.tf            # Local values and common configurations  
├── data.tf              # Data sources for existing resources
├── main.tf              # Main infrastructure resources
├── ssh-key.tf           # SSH key pair generation
├── s3.tf                # S3 bucket configuration
├── backend.tf           # Remote state configuration
├── outputs.tf           # Output values
├── terraform.tfvars.example  # Example variables
├── start-stop-ec2.sh    # EC2 instance management script
├── web-crypto-robot-key.pem  # Generated SSH private key (keep secure!)
├── web-crypto-robot-key.pub  # Generated SSH public key
└── README.md            # This file
```
