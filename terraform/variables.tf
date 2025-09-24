variable "vpc_id" {
  description = "The ID of the existing VPC"
  type        = string
  default     = "vpc-0ee30813b6d1cd7fd"
}

variable "s3_bucket_name" {
  description = "Name for the S3 bucket"
  type        = string
  default     = "crypto-robot-backups-059247592146" # Default value, change as needed
}

variable "ssh_key_name" {
  description = "Name of the SSH key pair for EC2 instance"
  type        = string
  default     = "web-crypto-robot-key" # Default value, change as needed
}

variable "create_ssh_key" {
  description = "Whether to create a new SSH key pair or use existing one"
  type        = bool
  default     = true
}

variable "allowed_cidrs" {
  description = "List of CIDR blocks allowed for SSH and HTTPS access"
  type        = list(string)
  default = [
    "163.116.163.0/24",
    "163.116.176.0/24",
    "163.116.242.0/24",
    "91.160.77.169/32",
    "109.208.89.176/32"
  ]
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}