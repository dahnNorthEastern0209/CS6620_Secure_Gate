output "lambda_function_name" {
  description = "Health check function name"
  value       = aws_lambda_function.health_check.function_name
}

output "log_group_name" {
  description = "CloudWatch log group for the health check"
  value       = aws_cloudwatch_log_group.health_check.name
}

output "sns_topic_arn" {
  description = "Alert topic other modules can publish to"
  value       = aws_sns_topic.alerts.arn
}

output "alarm_name" {
  description = "Scanner availability alarm"
  value       = aws_cloudwatch_metric_alarm.scanner_down.alarm_name
}
