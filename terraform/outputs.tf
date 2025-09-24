# Output values
output "vpc_id" {
  description = "ID of the VPC"
  value       = data.aws_vpc.existing.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = data.aws_vpc.existing.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = data.aws_subnets.public.ids
}

output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.crypto_robot.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.crypto_robot.public_ip
}

output "ec2_eip_address" {
  description = "Elastic IP address attached to the EC2 instance"
  value       = aws_eip.crypto_robot_eip.public_ip
}

output "ec2_eip_allocation_id" {
  description = "Allocation ID of the Elastic IP"
  value       = aws_eip.crypto_robot_eip.id
}

output "ec2_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.crypto_robot.private_ip
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.ec2_sg.id
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "iam_role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.ec2_s3_role.arn
}

output "ssh_key_name" {
  description = "Name of the SSH key pair"
  value       = var.ssh_key_name
}
