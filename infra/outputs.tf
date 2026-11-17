output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_ids" {
  value = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "alb_security_group_id" {
  value = module.network.alb_security_group_id
}

output "scanner_security_group_id" {
  value = module.network.scanner_security_group_id
}

output "alb_dns_name" {
  value = module.loadbalancer.alb_dns_name
}

output "scanner_url" {
  description = "HTTPS endpoint for the scanner (also in Parameter Store)"
  value       = module.loadbalancer.scanner_url
}

output "target_group_arn" {
  value = module.loadbalancer.target_group_arn
}

output "scanner_instance_id" {
  value = module.compute.instance_id
}

output "scanner_public_ip" {
  description = "Direct access should time out: the scanner only accepts ALB traffic"
  value       = module.compute.public_ip
}

output "ecr_repository_url" {
  value = module.compute.ecr_repository_url
}
