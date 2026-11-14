module "network" {
  source   = "./modules/network"
  project  = var.project
  vpc_cidr = var.vpc_cidr
}

module "loadbalancer" {
  source                = "./modules/loadbalancer"
  project               = var.project
  vpc_id                = module.network.vpc_id
  public_subnet_ids     = module.network.public_subnet_ids
  alb_security_group_id = module.network.alb_security_group_id
}

# Shared configuration for the other components (Lambda, GitHub Actions)
resource "aws_ssm_parameter" "scanner_url" {
  name  = "/${var.project}/scanner-url"
  type  = "String"
  value = module.loadbalancer.scanner_url
}

resource "aws_ssm_parameter" "alb_cert" {
  name  = "/${var.project}/alb-cert"
  type  = "String"
  value = module.loadbalancer.certificate_pem
}

# Modules added by the team as they are built:
# module "compute"    { source = "./modules/compute" ... }    # Yuzhe: ECR, EC2 behind the ALB
# module "storage"    { source = "./modules/storage" ... }    # David: S3 reports bucket, parameters
# module "monitoring" { source = "./modules/monitoring" ... } # Nishnath: Lambda, EventBridge, CloudWatch, SNS
