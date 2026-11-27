variable "project" {
  description = "Name prefix for all resources"
  type        = string
}

variable "lab_role_arn" {
  description = "Existing LabRole ARN. Learner Lab forbids creating IAM roles."
  type        = string
}

variable "alert_email" {
  description = "Address subscribed to the SNS alert topic"
  type        = string
}

variable "scanner_url_param" {
  description = "SSM parameter holding the scanner base URL. Created by the root config."
  type        = string
  default     = "/securegate/scanner-url"
}

variable "scanner_cert_param" {
  description = "SSM parameter holding the ALB certificate. Empty string disables custom CA verification."
  type        = string
  default     = "/securegate/alb-cert"
}

variable "schedule_expression" {
  description = "How often the health check runs"
  type        = string
  default     = "rate(5 minutes)"
}

variable "evaluation_periods" {
  description = "Consecutive failed checks before the alarm fires"
  type        = number
  default     = 2
}

variable "metric_namespace" {
  description = "CloudWatch namespace for custom metrics"
  type        = string
  default     = "SecureGate"
}

variable "log_retention_days" {
  description = "Lambda log retention"
  type        = number
  default     = 14
}

variable "depends_on_scanner" {
  description = "Pass the scanner URL from the loadbalancer module to order this module after it."
  type        = string
  default     = ""
}
