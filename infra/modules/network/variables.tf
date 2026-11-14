variable "project" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "scanner_port" {
  type    = number
  default = 3000
}
