# Security Group for EC2 instance
resource "aws_security_group" "ec2_sg" {
  name_prefix = "ec2-web-sg-"
  description = "Security group for EC2 instance allowing SSH and HTTPS"
  vpc_id      = var.vpc_id

  # SSH access from specified CIDRs
  ingress {
    description = "SSH"
    from_port   = 0
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  # HTTPS access from specified CIDRs
  ingress {
    description = "HTTPS"
    from_port   = 0
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  # # HTTP access (often needed for web applications)
  # ingress {
  #   description = "HTTP"
  #   from_port   = 0
  #   to_port     = 80
  #   protocol    = "tcp"
  #   cidr_blocks = var.allowed_cidrs
  # }

  # # Access to robot
  # ingress {
  #   description = "HTTP access to robot"
  #   from_port   = 0
  #   to_port     = 5000
  #   protocol    = "tcp"
  #   cidr_blocks = var.allowed_cidrs
  # }

  # HTTPS access from all IPv4 addresses
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 0
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ICMP ping access from specified CIDRs
  ingress {
    description = "ICMP ping"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = var.allowed_cidrs
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "ec2-web-security-group"
  })
}
