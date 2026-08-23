# terraform/main.tf
# AWS Infrastructure for CreditScoreV4 ML Governance

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "creditscorev4-vpc"
    Environment = var.environment
  }
}

# ECS Cluster for API serving
resource "aws_ecs_cluster" "main" {
  name = "creditscorev4-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECR Repository for Docker images
resource "aws_ecr_repository" "api" {
  name                 = "creditscorev4-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# S3 Bucket for data lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "creditscorev4-data-lake-${var.environment}"
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket for model artifacts
resource "aws_s3_bucket" "artifacts" {
  bucket = "creditscorev4-artifacts-${var.environment}"
}

# RDS PostgreSQL for Airflow/MLflow metadata
resource "aws_db_instance" "postgres" {
  identifier           = "creditscorev4-postgres"
  allocated_storage    = 100
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t3.medium"
  db_name              = "creditscorev4"
  username             = "postgres"
  password             = var.db_password
  parameter_group_name = "default.postgres15"
  skip_final_snapshot  = true

  vpc_security_group_ids = [aws_security_group.db.id]
}

# Security Groups
resource "aws_security_group" "db" {
  name_prefix = "creditscorev4-db-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/creditscorev4-api"
  retention_in_days = 30
}

# IAM Roles
resource "aws_iam_role" "ecs_task_execution" {
  name = "creditscorev4-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# SageMaker Model Endpoint (optional - for high-scale serving)
resource "aws_sagemaker_model" "creditscorev4" {
  name               = "creditscorev4-model"
  execution_role_arn = aws_iam_role.sagemaker.arn

  primary_container {
    image = "${aws_ecr_repository.api.repository_url}:latest"
    model_data_url = "s3://${aws_s3_bucket.artifacts.bucket}/models/creditscorev4.tar.gz"
  }
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

variable "db_password" {
  sensitive = true
}

# Outputs
output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "s3_data_lake" {
  value = aws_s3_bucket.data_lake.bucket
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}