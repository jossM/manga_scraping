module "week-day-lunch-trigger" {
  source = "./lambda_cron_trigger"
  rule-name = "mid-day"
  cron = "00 11 ? * MON-FRI *"
  lambda_function_name = aws_lambda_function.manga-scrapping.function_name
  lambda_function_arn = aws_lambda_function.manga-scrapping.arn
  providers = { aws = aws.us-east-aws }
}

module "week-end-trigger" {
  source = "./lambda_cron_trigger"
  rule-name = "weekend-cron"
  cron = "00 8/10 ? * SAT-SUN *"
  lambda_function_name = aws_lambda_function.manga-scrapping.function_name
  lambda_function_arn = aws_lambda_function.manga-scrapping.arn
  providers = { aws = aws.us-east-aws }
}
