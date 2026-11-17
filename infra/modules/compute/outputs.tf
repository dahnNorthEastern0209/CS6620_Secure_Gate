output "instance_id" {
  value = aws_instance.scanner.id
}

output "public_ip" {
  value = aws_instance.scanner.public_ip
}

output "ecr_repository_url" {
  value = aws_ecr_repository.scanner.repository_url
}
