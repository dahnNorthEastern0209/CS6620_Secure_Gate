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

variable "image_tag" {
  description = "Scanner image tag in ECR (e.g. a commit SHA)"
  type        = string
  default     = "latest"
}

variable "instance_profile_name" {
  description = "Existing EC2 instance profile (Learner Lab: LabInstanceProfile)"
  type        = string
  default     = "LabInstanceProfile"
}
