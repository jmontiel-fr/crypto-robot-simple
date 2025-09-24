locals {
  # Common tags to be applied to all resources
  common_tags = {
    Environment   = "dev"
    Project      = "crypto-robot"
    Owner        = "terraform"
    CreatedBy    = "terraform"
    ManagedBy    = "terraform"
  }

  # Naming conventions
  name_prefix = "web-crypto-robot"

  # Security group configuration
  security_group_name = "${local.name_prefix}-sg"

  # IAM configuration
  iam_role_name         = "${local.name_prefix}-ec2-s3-role"
  iam_policy_name       = "${local.name_prefix}-s3-policy"
  instance_profile_name = "${local.name_prefix}-instance-profile"

  # EC2 configuration
  instance_name = "${local.name_prefix}-instance"
  instance_type = "t3.micro"

  # EIP configuration
  eip_name = "${local.name_prefix}-eip"

  # EBS configuration
  root_volume_size = 100
  root_volume_type = "gp3"

  # S3 configuration - using variable with local prefix if needed
  s3_bucket_name_full = var.s3_bucket_name

  # Network configuration
  vpc_id        = var.vpc_id
  allowed_cidrs = var.allowed_cidrs

  # SSH configuration
  ssh_key_name = var.ssh_key_name

  # Region configuration
  aws_region = var.region
}
