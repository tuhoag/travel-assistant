variable "aws_region" {
  description = "AWS region to deploy Fargate services and Bedrock/OpenSearch into."
  type        = string
  default     = "eu-central-1"
}

variable "agent_image_repository" {
  description = "Docker Hub repository for the agent image (without a tag)."
  type        = string
  default     = "tuhoag/travel-assistant-agent"
}

variable "agent_image_tag" {
  description = "Tag to deploy, e.g. \"prod-v1.2.3\". No default — every apply must state explicitly which version it's deploying, rather than silently tracking whatever :latest happens to point to."
  type        = string
}

variable "chat_model" {
  description = "Bedrock model id the agent uses for chat. Defaults to the model already in use; the account must have model access granted in the Bedrock console — Terraform cannot grant that."
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "embedding_model" {
  description = "The embedding model FastEmbed uses locally to generate query vectors before searching OpenSearch."
  type        = string
  default     = "BAAI/bge-small-en-v1.5"
}

variable "frontend_image_repository" {
  description = "Docker Hub repository for the frontend image (without a tag)."
  type        = string
  default     = "tuhoag/travel-assistant-frontend"
}

variable "frontend_image_tag" {
  description = "Tag to deploy, e.g. \"prod-v1.2.3\". No default — every apply must state explicitly which version it's deploying. The agent's URL is wired in at runtime (frontend.tf), not baked in at build time, so this image can be built independently of the agent."
  type        = string
}
