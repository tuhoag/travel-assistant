provider "github" {
  owner = var.github_owner
}

resource "github_actions_secret" "aws_deploy_role_arn" {
  repository  = var.github_repo
  secret_name = "AWS_DEPLOY_ROLE_ARN"
  value       = aws_iam_role.github_actions_deploy.arn
}