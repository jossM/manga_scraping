variable "image-bucket" {
  type = string
}

resource "aws_s3_bucket" "image-bucket" {
  bucket = var.image-bucket
  provider = aws.us-east-aws
}
