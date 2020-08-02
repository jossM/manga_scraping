terraform {
  required_version = "0.12.28"

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
  version = "~> 2.0"
}

provider "aws" {
  region = var.region
  version = "~> 2.0"
  alias = "us-east-aws"
}

provider "tls" {
  version = "~> 2.2"
}