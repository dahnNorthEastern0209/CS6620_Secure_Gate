#!/usr/bin/env bash
# One-time setup for any AWS account: state bucket, API key, backend config.
# Usage: ./scripts/bootstrap.sh   (optionally AWS_REGION=us-west-2 ./scripts/bootstrap.sh)
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
PROJECT="${PROJECT:-securegate}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="${PROJECT}-tfstate-${ACCOUNT}"
echo "Account: ${ACCOUNT}  Region: ${REGION}"

# 1. Terraform state bucket (versioned)
if aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
  echo "State bucket exists: ${BUCKET}"
else
  if [ "${REGION}" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" >/dev/null
  else
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" \
      --create-bucket-configuration LocationConstraint="${REGION}" >/dev/null
  fi
  echo "Created state bucket: ${BUCKET}"
fi
aws s3api put-bucket-versioning --bucket "${BUCKET}" --region "${REGION}" \
  --versioning-configuration Status=Enabled

# 2. Scanner API key in Parameter Store (never stored in code or Terraform state)
PARAM="/${PROJECT}/api-key"
if aws ssm get-parameter --name "${PARAM}" --region "${REGION}" >/dev/null 2>&1; then
  echo "API key parameter exists: ${PARAM}"
else
  aws ssm put-parameter --name "${PARAM}" --type SecureString \
    --value "$(openssl rand -hex 16)" --region "${REGION}" >/dev/null
  echo "Created API key parameter: ${PARAM}"
fi

# 3. Backend config for this account
cat > "${ROOT}/infra/backend.hcl" << EOT
bucket = "${BUCKET}"
region = "${REGION}"
EOT
echo "Wrote infra/backend.hcl"

echo
echo "Next:"
echo "  export TF_VAR_region=${REGION}"
echo "  cd infra && terraform init -backend-config=backend.hcl"
