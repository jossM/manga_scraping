variable "lambda_function_name" { type = string }
variable "lambda_function_arn" { type = string }
variable "rule-name" {type = string}
variable "cron" { type = string}

resource "aws_cloudwatch_event_rule" "cron" {
    name = var.rule-name
    schedule_expression = "cron(${var.cron})"
}

resource "aws_cloudwatch_event_target" "cron-target" {
    rule = aws_cloudwatch_event_rule.cron.name
    target_id = var.lambda_function_name
    arn = var.lambda_function_arn
}

resource "aws_lambda_permission" "allow-cloudwatch-to-call-lambda" {
    statement_id = "AllowExecutionOf${var.lambda_function_name}FromCloudWatch${var.rule-name}"
    action = "lambda:InvokeFunction"
    function_name = var.lambda_function_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.cron.arn
}
