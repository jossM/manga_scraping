locals {
  s3_origin_id = "manga-scrapping-img"
}

resource "aws_s3_bucket" "image-bucket" {
  bucket = var.image-bucket
  acl    = "private"

  tags = {
    project = "MangaScrapping"
  }
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "block_image_bucket" {
  bucket = aws_s3_bucket.image-bucket.id

  block_public_acls = true
  block_public_policy = true
}


resource "aws_cloudfront_origin_access_identity" "cdn" {
  comment = "manga scrapping cdn s3 identity"
}

data "aws_iam_policy_document" "allow-cdn-access-to-s3" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.image-bucket.arn]
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.cdn.iam_arn]
    }
  }

  statement {
    actions = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.image-bucket.arn}/*"]
    principals {
      identifiers = [aws_cloudfront_origin_access_identity.cdn.iam_arn]
      type = "AWS"
    }
  }
}

resource "aws_s3_bucket_policy" "allow-cdn-access-to-s3" {
  bucket = aws_s3_bucket.image-bucket.id
  policy = data.aws_iam_policy_document.allow-cdn-access-to-s3.json
}

resource "aws_cloudfront_distribution" "s3_distribution" {

  origin {
    domain_name = aws_s3_bucket.image-bucket.bucket_regional_domain_name
    origin_id   = local.s3_origin_id

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.cdn.cloudfront_access_identity_path
    }
  }
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Manga series images representation"

  default_cache_behavior {
    allowed_methods  = ["HEAD", "GET", "OPTIONS"]
    cached_methods   = ["HEAD", "GET", "OPTIONS"]
    target_origin_id = local.s3_origin_id

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }
    trusted_signers = ["self"]

    viewer_protocol_policy = "https-only"
    min_ttl                = 86400 // a day
    default_ttl            = 3 * 7 * 86400
    max_ttl                = 5 * 7 * 604800
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = ["FR"]
    }
  }

  tags = {
    Environment = "production"
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_cloudfront_public_key" "access_key" {
  encoded_key = tls_private_key.cloud-front-key.public_key_pem
  name = "manga-scrapping-key"
}

resource "tls_private_key" "cloud-front-key" {
  // This stores the key in the terraform state which mean => here on S3.
  // This is fine since I am alone on the account. This should not be used in an organisation.
  algorithm = "RSA"
  rsa_bits = 2048

  lifecycle {
    prevent_destroy = true
  }
}