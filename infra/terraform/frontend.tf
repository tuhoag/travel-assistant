module "frontend" {
  source = "./modules/fargate"

  name              = "travel-assistant-frontend"
  image             = "${var.frontend_image_repository}:${var.frontend_image_tag}"
  container_port    = 3000
  health_check_path = "/"
  vpc_id            = aws_vpc.this.id
  public_subnet_ids = aws_subnet.public[*].id
  cluster_id        = aws_ecs_cluster.this.arn

  # AGENT_URL/AGENT_ID are read server-side only (frontend/src/app/api/chat/route.ts
  # proxies to the agent), so this is a genuine runtime value now — no longer
  # baked into the image at build time, and no NEXT_PUBLIC_ prefix needed
  # since it never reaches the browser.
  environment = {
    AGENT_URL = module.agent.url
    AGENT_ID  = "agent"
  }
}
