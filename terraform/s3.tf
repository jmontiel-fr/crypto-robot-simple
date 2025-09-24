# S3 bucket
resource "aws_s3_bucket" "main" {
  bucket        = var.s3_bucket_name
  force_destroy = true  # This allows Terraform to delete the bucket even if it contains objects

  tags = merge(local.common_tags, {
    Name = "Main S3 Bucket"
  })
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }

  depends_on = [aws_s3_bucket.main]
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket public access block (security best practice)
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
