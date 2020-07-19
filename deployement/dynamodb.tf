resource "aws_dynamodb_table" "page-mark-table" {
  name           = "manga_page_marks"
  billing_mode   = "PROVISIONED"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "serie_id"

  attribute {
    name = "serie_id"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }
  provider = aws.us-east-aws
}
