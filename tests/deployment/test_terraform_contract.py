from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_terraform_uses_fargate_and_immutable_ecr() -> None:
    ecs = (ROOT / "infra/terraform/ecs.tf").read_text()
    ecr = (ROOT / "infra/terraform/ecr.tf").read_text()
    assert 'requires_compatibilities = ["FARGATE"]' in ecs
    assert 'image_tag_mutability = "IMMUTABLE"' in ecr
    assert "scan_on_push = true" in ecr


def test_service_is_only_reachable_from_alb_security_group() -> None:
    networking = (ROOT / "infra/terraform/networking.tf").read_text()
    assert "security_groups = [aws_security_group.alb.id]" in networking
