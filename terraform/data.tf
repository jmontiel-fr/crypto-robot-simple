# Data source to get existing VPC information
data "aws_vpc" "existing" {
  id = var.vpc_id
}

# Data source to get all subnets in the VPC
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  # Filter for public subnets (subnets with route to internet gateway)
  filter {
    name   = "tag:Name"
    values = ["*public*", "*Public*"]
  }
}

# Alternative way to get public subnets by checking route tables
data "aws_subnets" "public_alternative" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

# Get availability zones for the region
data "aws_availability_zones" "available" {
  state = "available"
}

# Get the most recent Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
