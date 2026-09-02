data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = ["arn:aws:bedrock:${var.aws_region}::foundation-model/*"]
  }
}

module "agent" {
  source = "./modules/fargate"

  name              = "travel-assistant-agent"
  image             = "${var.agent_image_repository}:${var.agent_image_tag}"
  container_port    = 8000
  health_check_path = "/health"
  vpc_id            = aws_vpc.this.id
  public_subnet_ids = aws_subnet.public[*].id
  cluster_id        = aws_ecs_cluster.this.arn

  # No secrets block at all: Bedrock and OpenSearch are both authenticated via
  # this service's own task IAM role (SigV4), not a static API key — unlike
  # the Groq/OpenRouter + Qdrant setup this replaced.
  environment = {
    AWS_REGION      = var.aws_region
    OPENSEARCH_URL  = "https://${aws_opensearch_domain.travel_assistant.endpoint}"
    CHAT_MODEL      = var.chat_model
    EMBEDDING_MODEL = var.embedding_model
    # Cloud Map DNS name — deterministic from the service name + namespace,
    # so this doesn't need to reference module.mcp_hotels's outputs at all
    # (avoids a module dependency cycle: mcp_hotels's own ingress rule
    # already depends on module.agent.security_group_id).
    MCP_HOTELS_URL = "http://travel-assistant-mcp-hotels.${aws_service_discovery_private_dns_namespace.internal.name}:8080/mcp"
  }

  task_role_policy_json = data.aws_iam_policy_document.bedrock_invoke.json
}
