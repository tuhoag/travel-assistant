# Read-only access to the RDS-managed secret this service fetches at
# runtime via boto3 (see mcp-hotels/src/db.py) — needed on the task role,
# not the execution role, since the app itself calls Secrets Manager
# rather than ECS injecting the value as a container env var.
data "aws_iam_policy_document" "read_hotels_db_secret" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_db_instance.hotels.master_user_secret[0].secret_arn]
  }
}

module "mcp_hotels" {
  source = "./modules/fargate"

  name              = "travel-assistant-mcp-hotels"
  image             = "${var.mcp_hotels_image_repository}:${var.mcp_hotels_image_tag}"
  container_port    = 8080
  vpc_id            = aws_vpc.this.id
  public_subnet_ids = aws_subnet.public[*].id
  cluster_id        = aws_ecs_cluster.this.arn

  # Internal-only: no public ALB, reached by the agent via Cloud Map
  # (service_discovery.tf) instead. Ingress is scoped to the agent's own
  # security group — nothing else in the VPC can reach it.
  enable_alb                     = false
  allowed_security_group_ids     = [module.agent.security_group_id]
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.internal.id

  environment = {
    AWS_REGION           = var.aws_region
    PGHOST               = aws_db_instance.hotels.address
    PGPORT               = "5432"
    PGDATABASE           = "hotels"
    HOTELS_DB_SECRET_ARN = aws_db_instance.hotels.master_user_secret[0].secret_arn
  }

  task_role_policy_json = data.aws_iam_policy_document.read_hotels_db_secret.json
}
