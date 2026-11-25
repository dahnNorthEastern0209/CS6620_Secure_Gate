locals {
  name = "${var.project}-health-check"
}

# ---------- Lambda ----------

data "archive_file" "health_check" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/.build/health_check.zip"
}

resource "aws_lambda_function" "health_check" {
  function_name    = local.name
  role             = var.lab_role_arn
  handler          = "health_check.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128
  filename         = data.archive_file.health_check.output_path
  source_code_hash = data.archive_file.health_check.output_base64sha256

  environment {
    variables = {
      SCANNER_URL_PARAM  = var.scanner_url_param
      SCANNER_CERT_PARAM = var.scanner_cert_param
      METRIC_NAMESPACE   = var.metric_namespace
    }
  }
}

resource "aws_cloudwatch_log_group" "health_check" {
  name              = "/aws/lambda/${aws_lambda_function.health_check.function_name}"
  retention_in_days = var.log_retention_days
}

# ---------- EventBridge schedule ----------

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.project}-health-schedule"
  description         = "Invokes the SecureGate scanner health check"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "schedule" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "health-check"
  arn       = aws_lambda_function.health_check.arn
}

resource "aws_lambda_permission" "allow_events" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}

# ---------- SNS ----------

resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ---------- Alarm ----------

resource "aws_cloudwatch_metric_alarm" "scanner_down" {
  alarm_name        = "${var.project}-scanner-down"
  alarm_description = "Scanner /health failed ${var.evaluation_periods} consecutive checks"

  namespace   = var.metric_namespace
  metric_name = "ScannerHealthy"
  statistic   = "Average"
  period      = 300

  comparison_operator = "LessThanThreshold"
  threshold           = 1
  evaluation_periods  = var.evaluation_periods
  datapoints_to_alarm = var.evaluation_periods
  treat_missing_data  = "breaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}
