locals {
  function-name="manga-scrapping"
}

// IAM
data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["lambda.amazonaws.com"]
      type = "Service"
    }
    effect = "Allow"
  }
}

resource "aws_iam_role" "manga_scrapping_role" {
  name = "manga_scrapping_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}


resource "aws_iam_policy" "allow-db-access" {
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListAndDescribe",
            "Effect": "Allow",
            "Action": [
                "dynamodb:List*",
                "dynamodb:DescribeReservedCapacity*",
                "dynamodb:DescribeLimits",
                "dynamodb:DescribeTimeToLive"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SpecificTable",
            "Effect": "Allow",
            "Action": [
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
            ],
            "Resource": "${aws_dynamodb_table.page-mark-table.arn}"
        }
    ]
}
EOF
}
resource "aws_iam_policy_attachment" "attach-lambda-read-db-policy" {
  name = "AllowDynamodbAccess"
  policy_arn = aws_iam_policy.allow-db-access.arn
  roles = [aws_iam_role.manga_scrapping_role.name]
}

resource "aws_iam_policy" "allow-ses-calls" {
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_policy_attachment" "send-mails" {
  name = "AllowSESAccess"
  policy_arn = aws_iam_policy.allow-ses-calls.arn
  roles = [aws_iam_role.manga_scrapping_role.name]
}

resource "aws_iam_policy" "allow-sns-errors-report" {
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "${data.terraform_remote_state.aws-common.outputs.monitoring_sns_us_arn}"
        }
    ]
}
EOF
}

resource "aws_iam_policy_attachment" "send-error-mails" {
  name = "AllowFailedHandlingAlert"
  policy_arn = aws_iam_policy.allow-sns-errors-report.arn
  roles = [aws_iam_role.manga_scrapping_role.name]
}

// Lambda config
resource "aws_lambda_function" "manga-scrapping" {
  function_name = local.function-name
  handler = "main.handle_scheduled_scraping"
  role = aws_iam_role.manga_scrapping_role.arn
  runtime = "python3.6"

  s3_bucket = "north-virginia-code"
  s3_key = "manga-scrapping-code.zip"
  timeout = 240
  memory_size = 256

  environment {
    variables = {
      AWS_REGION_SCRAPPING = var.region
      EMAIL_PERSO = var.receiver-mail
      NEWSLETTER_SENDER	= var.sender-mail
      CLOUD_FRONT_DISTRIBUTION_DOMAIN = aws_cloudfront_distribution.s3_distribution.domain_name
      CLOUD_FRONT_KEY_ID = aws_cloudfront_public_key.access_key.id
      CLOUD_FRONT_KEY_SECRET = tls_private_key.cloud-front-key.private_key_pem // Aws Secret Manager isn't used as I am alone on the project and I don't want to pay.
    }
  }

  dead_letter_config {
    target_arn = data.terraform_remote_state.aws-common.outputs.monitoring_sns_us_arn
  }

  tags = {
    project	= "MangaScrapping"
  }
  provider = aws.us-east-aws
  depends_on = [
    aws_iam_policy_attachment.attach-lambda-read-db-policy,
    aws_iam_policy_attachment.send-mails,
    aws_iam_policy_attachment.send-error-mails
  ]
}