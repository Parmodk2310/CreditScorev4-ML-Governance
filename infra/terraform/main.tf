data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = "CreditScoreV4-ML-Governance"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Phase       = "7"
  }
}
