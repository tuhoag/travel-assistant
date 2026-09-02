provider "github" {
  owner = var.github_owner
}

resource "github_actions_secret" "aws_deploy_role_arn" {
  repository  = var.github_repo
  secret_name = "AWS_DEPLOY_ROLE_ARN"
  value       = aws_iam_role.github_actions_deploy.arn
}

resource "github_actions_secret" "dockerhub_username" {
  repository  = var.github_repo
  secret_name = "DOCKERHUB_USERNAME"
  value       = var.dockerhub_username
}

resource "github_actions_secret" "dockerhub_token" {
  repository  = var.github_repo
  secret_name = "DOCKERHUB_TOKEN"
  value       = var.dockerhub_token
}
