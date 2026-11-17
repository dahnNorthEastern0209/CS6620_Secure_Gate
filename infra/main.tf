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

module "compute" {
  source                    = "./modules/compute"
  project                   = var.project
  region                    = var.region
  subnet_id                 = module.network.public_subnet_ids[0]
  scanner_security_group_id = module.network.scanner_security_group_id
  target_group_arn          = module.loadbalancer.target_group_arn
  image_tag                 = var.image_tag
  instance_profile_name     = var.instance_profile_name
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
# module "storage"    { source = "./modules/storage" ... }    # David: S3 reports bucket, parameters
# module "monitoring" { source = "./modules/monitoring" ... } # Nishnath: Lambda, EventBridge, CloudWatch, SNS
