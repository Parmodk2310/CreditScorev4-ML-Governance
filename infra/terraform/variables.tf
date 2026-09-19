variable "aws_region" {
  description = "AWS region used by the deployment."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Resource-name prefix."
  type        = string
  default     = "creditscorev4"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "production"
}

variable "image_uri" {
  description = "Immutable ECR image URI (prefer repository@sha256:digest)."
  type        = string
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "task_cpu" {
  type    = number
  default = 512
}

variable "task_memory" {
  type    = number
  default = 1024
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN used by the public HTTPS ALB listener."
  type        = string
  default     = ""

  validation {
    condition = (
      var.acm_certificate_arn == "" ||
      startswith(var.acm_certificate_arn, "arn:aws:acm:")
    )
    error_message = "acm_certificate_arn must be empty for local validation or a valid ACM ARN."
  }
}
