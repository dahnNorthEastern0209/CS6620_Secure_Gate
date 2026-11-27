data "aws_caller_identity" "current" {}

# Latest Amazon Linux 2023 (x86_64) AMI for whichever region we deploy to
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

locals {
  registry = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
  image    = "${aws_ecr_repository.scanner.repository_url}:${var.image_tag}"
}

resource "aws_ecr_repository" "scanner" {
  name         = "${var.project}-scanner"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_instance" "scanner" {
  ami                    = data.aws_ssm_parameter.al2023.value
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.scanner_security_group_id]
  iam_instance_profile   = var.instance_profile_name

  metadata_options {
    http_tokens = "required" # IMDSv2
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    region            = var.region
    registry          = local.registry
    image             = local.image
    api_key_parameter = "/${var.project}/api-key"
    port              = var.scanner_port
  })
  user_data_replace_on_change = true

  # Don't replace the instance just because a newer Amazon Linux image is released
  lifecycle {
    ignore_changes = [ami]
  }

  tags = { Name = "${var.project}-scanner" }
}

resource "aws_lb_target_group_attachment" "scanner" {
  target_group_arn = var.target_group_arn
  target_id        = aws_instance.scanner.id
  port             = var.scanner_port
}
