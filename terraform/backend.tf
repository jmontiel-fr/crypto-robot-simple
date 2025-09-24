# Terraform backend configuration for S3
# Note: You need to create the backend S3 bucket and DynamoDB table manually first
# or use a separate Terraform configuration to create them

terraform {
  backend "s3" {
    # Replace these values with your actual backend configuration
    bucket         = "tfstates-059247592146-s3bucket" # Change this to your state bucket name
    key            = "crypto-robot/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "tfstates-059247592146-lock-table" # Optional: for state locking
    encrypt        = true
  }
}
