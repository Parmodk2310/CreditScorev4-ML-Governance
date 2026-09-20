# Phase 7 — Automation, Security, and Gated Cloud Deployment

## Goal

Phase 7 automates the already-verified governance and safe-release system without weakening its controls. It is infrastructure/deployment work, not a new credit-model phase.

## CI boundary

Every pull request to `main` runs Python quality checks, the cumulative Phase 9 governance/evidence verification, Phase 7 automation tests, and Terraform validation without a remote backend. Container CI builds the existing Phase 6 serving image and smoke-tests `/health`, `/ready`, and `/model` without publishing an image.

## Security boundary

Gitleaks scans Git history for secrets. Trivy blocks HIGH/CRITICAL filesystem vulnerabilities and Terraform configuration findings. These are engineering controls, not a compliance certification.

## Deployment safety model

AWS deployment is disabled by default. The deployment workflow is manual only and requires all of the following:

- repository variable `AWS_DEPLOY_ENABLED=true`
- manual input `DEPLOY`
- GitHub OIDC role variable `AWS_ROLE_TO_ASSUME`
- `AWS_REGION`
- persistent Terraform S3 backend variables `TF_STATE_BUCKET` and `TF_STATE_KEY`
- successful quality and cumulative Phase 9 governance/evidence verification

No long-lived AWS access keys are required by the workflow.

## Infrastructure

Terraform manages an immutable ECR repository, two-AZ public VPC, internet gateway, ALB, restricted ECS service security group, ECS/Fargate cluster/service/task definition, task-execution IAM role, and CloudWatch logs. The service security group accepts model traffic only from the ALB security group.

The example uses public subnets plus Fargate public IPs to avoid a NAT gateway in this cost-conscious reference architecture. It still creates billable AWS resources when deployment is explicitly enabled.

## Image evidence

The deploy workflow tags the image with the Git commit SHA, resolves the pushed ECR digest, deploys the digest-addressed image, and writes a release manifest containing the Git commit, image digest, governance/release/security status, and deployment flag.

## Terraform state

Validation uses `terraform init -backend=false`. Enabled deployment supplies an S3 backend at runtime with S3 native lockfiles. The state bucket is a prerequisite/bootstrap resource and is intentionally not created by this stack.

## Verification

```bash
make phase7-test
make phase7-verify
```

When Terraform is installed locally:

```bash
make phase7-terraform
```

The expected local default is `AWS_DEPLOY_ENABLED=false`, which is a passing safety condition, not an error.

## Scope boundary

This is a synthetic ML governance system. Phase 7 covers CI/CD, security, infrastructure-as-code, and gated cloud deployment. It does not claim a live regulated lending deployment or legal/regulatory compliance.
