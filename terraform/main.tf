# IAM role for EC2 instance
resource "aws_iam_role" "ec2_s3_role" {
  name = local.iam_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "EC2-S3-Access-Role"
  })
}

# IAM policy for S3 read/write access
resource "aws_iam_policy" "s3_readwrite_policy" {
  name        = local.iam_policy_name
  description = "Policy for EC2 to read/write to S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
        ]
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "s3_policy_attachment" {
  role       = aws_iam_role.ec2_s3_role.name
  policy_arn = aws_iam_policy.s3_readwrite_policy.arn
}

# Instance profile for EC2
resource "aws_iam_instance_profile" "ec2_profile" {
  name = local.instance_profile_name
  role = aws_iam_role.ec2_s3_role.name
}

# Elastic IP for EC2 instance
resource "aws_eip" "crypto_robot_eip" {
  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = local.eip_name
  })
}

# Associate Elastic IP with EC2 instance
resource "aws_eip_association" "crypto_robot_eip_assoc" {
  instance_id   = aws_instance.crypto_robot.id
  allocation_id = aws_eip.crypto_robot_eip.id
}

# EC2 Instance
resource "aws_instance" "crypto_robot" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = local.instance_type
  key_name               = var.ssh_key_name
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  subnet_id              = data.aws_subnets.public.ids[0]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  # User data script for package installation
  user_data = base64encode(file("${path.module}/user-data.sh"))

  # EBS root volume configuration
  root_block_device {
    volume_type = local.root_volume_type
    volume_size = local.root_volume_size
    encrypted   = true
    tags = merge(local.common_tags, {
      Name = "ec2-root-volume"
    })
  }

  tags = merge(local.common_tags, {
    Name = local.instance_name
    Type = "crypto-robot"
  })
}
