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

output "hotels_db_endpoint" {
  value = aws_db_instance.hotels.address
}

output "assets_bucket_name" {
  value = aws_s3_bucket.assets.bucket
}

output "assets_bucket_url" {
  value = "https://${aws_s3_bucket.assets.bucket}.s3.${var.aws_region}.amazonaws.com"
}