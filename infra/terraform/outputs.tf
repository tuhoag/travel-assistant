output "agent_url" {
  value = module.agent.url
}

output "frontend_url" {
  value = module.frontend.url
}

output "opensearch_endpoint" {
  value = aws_opensearch_domain.travel_assistant.endpoint
}

output "github_actions_deploy_role_arn" {
  value = aws_iam_role.github_actions_deploy.arn
}