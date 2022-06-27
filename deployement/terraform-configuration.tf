terraform {
  required_version = "1.2.3"

  required_providers {
      aws = ">= 2.68.0"
  }

  backend "s3" {
    key = "manga-scrapping"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = "eu-west-1"
}

provider "aws" {
  region = var.region
  alias = "us-east-aws"
}

provider "tls" {}