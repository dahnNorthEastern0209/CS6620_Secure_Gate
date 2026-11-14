module "network" {
  source   = "./modules/network"
  project  = var.project
  vpc_cidr = var.vpc_cidr
}

# Modules added by the team as they are built:
# module "loadbalancer" { source = "./modules/loadbalancer" ... } # Yuzhe: ALB, target group, HTTPS listener
# module "compute"      { source = "./modules/compute" ... }      # Yuzhe: ECR, launch template, EC2
# module "storage"      { source = "./modules/storage" ... }      # David: S3 reports bucket, parameters
# module "monitoring"   { source = "./modules/monitoring" ... }   # Nishath: Lambda, EventBridge, CloudWatch, SNS
