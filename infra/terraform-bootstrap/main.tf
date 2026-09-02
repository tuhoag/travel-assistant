# Applied manually, by hand, from your own machine — never by CI. The
# `github` provider needs a token capable of managing repo Actions secrets,
# and GitHub Actions' own ephemeral GITHUB_TOKEN is deliberately barred
# from that API regardless of workflow `permissions:` — there is no way
# for a CI job to authenticate this provider. Local state is fine here:
# three resources, reapplied rarely, only ever from a machine that already
# has its own `gh`/GitHub auth (this provider reads GITHUB_TOKEN, or use
# `gh auth login` + `gh auth token` — see README in this directory).
terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "github" {
  owner = var.github_owner
}

# Looked up by name rather than via remote state — this bootstrap step
# runs after the main stack has already created the role, and the name is
# fixed (see infra/terraform/github_oidc.tf).
data "aws_iam_role" "github_actions_deploy" {
  name = "travel-assistant-github-actions-deploy"
}

resource "github_actions_secret" "aws_deploy_role_arn" {
  repository  = var.github_repo
  secret_name = "AWS_DEPLOY_ROLE_ARN"
  value       = data.aws_iam_role.github_actions_deploy.arn
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
