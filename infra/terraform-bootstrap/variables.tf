variable "aws_region" {
  description = "AWS region the main stack's IAM role lives in."
  type        = string
  default     = "eu-central-1"
}

variable "github_owner" {
  description = "GitHub owner/org for the repo that runs Terraform via GitHub Actions."
  type        = string
}

variable "github_repo" {
  description = "GitHub repo name that runs Terraform via GitHub Actions."
  type        = string
  default     = "travel-assistant"
}

variable "dockerhub_username" {
  description = "Docker Hub username for the account that owns the agent/frontend/mcp-hotels images."
  type        = string
}

variable "dockerhub_token" {
  description = "Docker Hub access token for the account that owns the agent/frontend/mcp-hotels images."
  type        = string
  sensitive   = true
}
