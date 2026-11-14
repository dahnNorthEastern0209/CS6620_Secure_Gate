# Remote state in S3. Bucket and region come from backend.hcl,
# which scripts/bootstrap.sh generates for whichever account you're in:
#   terraform init -backend-config=backend.hcl
terraform {
  backend "s3" {
    key          = "securegate/terraform.tfstate"
    encrypt      = true
    use_lockfile = true # S3-native state locking (Terraform >= 1.11)
  }
}
