output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "scanner_url" {
  value = "https://${aws_lb.main.dns_name}"
}

output "target_group_arn" {
  value = aws_lb_target_group.scanner.arn
}

output "certificate_pem" {
  description = "Public certificate clients use to verify HTTPS (safe to share)"
  value       = tls_self_signed_cert.alb.cert_pem
}
