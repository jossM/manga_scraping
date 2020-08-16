variable "region" {
  type = string
}

variable "receiver-mail" {
  type = string
}

variable "sender-mail" {
  type = string
}

variable "bucket" {
  type = string
  description = "backend bucket for remote state"
}

variable "image-bucket" {
  type = string
}

variable "cloudfront-key-pair-id" {
  type = string
}

data "terraform_remote_state" "aws-common" {
  backend = "s3"
  config = {
    bucket = var.bucket
    key = "aws-common"
    region = "eu-west-1"
  }
}