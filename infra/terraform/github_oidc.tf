resource "aws_iam_openid_connect_provider" "github_actions" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  # Computed live via `openssl s_client ... | openssl x509 -noout -fingerprint -sha1`
  # against the root of the current chain — the commonly-cited value
  # (6938fd4d98bab03faadb97b34396831e3780aea1, from when this endpoint was
  # served via DigiCert) is stale now that GitHub serves it via Let's Encrypt.
  thumbprint_list = ["AB9D0263244DD0326EB67015705A667E79CFE998"]
}

data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:tuhoag/travel-assistant:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions_deploy" {
  name               = "travel-assistant-github-actions-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json
}

# Necessarily broad — this role runs `terraform apply` for the whole stack
# (VPC, ECS, ELB, IAM role create/PassRole, OpenSearch, S3/DynamoDB state).
# Scoped only by the trust policy's `sub` condition above (main-branch
# pushes to this exact repo, nothing else can assume it).
data "aws_iam_policy_document" "github_actions_deploy_permissions" {
  statement {
    effect    = "Allow"
    actions   = ["ec2:*", "ecs:*", "elasticloadbalancing:*", "es:*", "logs:*", "iam:*", "s3:*", "dynamodb:*"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_actions_deploy" {
  name   = "deploy-permissions"
  role   = aws_iam_role.github_actions_deploy.id
  policy = data.aws_iam_policy_document.github_actions_deploy_permissions.json
}
