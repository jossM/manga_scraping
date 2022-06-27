


data "aws_iam_policy_document" "allow-db-access" {
  version = "2012-10-17"
  statement {
    sid = "ListAndDescribe"
    effect = "Allow"
    actions = [
      "dynamodb:List*",
      "dynamodb:DescribeReservedCapacity*",
      "dynamodb:DescribeLimits",
      "dynamodb:DescribeTimeToLive"
    ]
    resources = ["*"]
  }

  statement {
    sid = "SpecificTable"
    effect = "Allow"
    actions = [
      "dynamodb:BatchGet*",
      "dynamodb:DescribeStream",
      "dynamodb:DescribeTable",
      "dynamodb:Get*",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchWrite*",
      "dynamodb:CreateTable",
      "dynamodb:Delete*",
      "dynamodb:Update*",
      "dynamodb:PutItem"
    ]
    resources = [aws_dynamodb_table.page-mark-table.arn]
  }
}

data "aws_iam_policy_document" "allow-ses-calls" {
  version = "2012-10-17"
  statement {
    sid = "AllowSendMails"
    effect = "Allow"
    actions = ["ses:Send*"]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "allow-sns-errors-report" {
  version = "2012-10-17"
  statement {
    sid = "AllowSnsError"
    effect = "Allow"
    actions = ["sns:Publish"]
    resources = [data.terraform_remote_state.aws-common.outputs.monitoring_sns_us_arn]
  }
}

data "aws_iam_policy_document" "lambda_policy" {
  source_policy_documents = [
    data.aws_iam_policy_document.allow-db-access.json,
    data.aws_iam_policy_document.allow-sns-errors-report.json,
    data.aws_iam_policy_document.allow-ses-calls.json,
    data.aws_iam_policy_document.lambda-logging.json
  ]
}

module "lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "manga_scrapping"
  handler = "main.handle_scheduled_scraping"
  runtime = "python3.9"
  source_path = "../lambda"

  store_on_s3 = true
  s3_bucket = "north-virginia-code"
  memory_size = 256
  timeout = 240
  role_name = "manga_scrapping_role"

  attach_policy_json = true
  policy_json = data.aws_iam_policy_document.lambda_policy.json

  environment_variables = {
    AWS_REGION_SCRAPPING = var.region
    EMAIL_PERSO = var.receiver-mail
    NEWSLETTER_SENDER	= var.sender-mail
    CLOUD_FRONT_DISTRIBUTION_DOMAIN = aws_cloudfront_distribution.s3_distribution.domain_name
    CLOUD_FRONT_KEY_ID = var.cloudfront-key-pair-id
  }

  dead_letter_target_arn = data.terraform_remote_state.aws-common.outputs.monitoring_sns_us_arn
  tags = {
    project	= "MangaScrapping"
  }

  providers = {aws: aws.us-east-aws}
}
