variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "scanner_security_group_id" {
  type = string
}

variable "target_group_arn" {
  type = string
}

variable "image_tag" {
  type = string
}

variable "instance_profile_name" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "scanner_port" {
  type    = number
  default = 3000
}
