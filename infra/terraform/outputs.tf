output "agent_url" {
  value = module.agent.url
}

output "frontend_url" {
  value = module.frontend.url
}

output "opensearch_endpoint" {
  value = aws_opensearch_domain.travel_assistant.endpoint
}