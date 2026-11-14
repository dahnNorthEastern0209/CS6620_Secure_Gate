variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Name prefix and Project tag for all resources"
  type        = string
  default     = "securegate"
}

variable "vpc_cidr" {
  description = "CIDR block for the SecureGate VPC"
  type        = string
  default     = "10.20.0.0/16"
}
