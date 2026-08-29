variable "qdrant_api_key" {
  description = "API Key generated in Qdrant Cloud (required)"
  type        = string
  sensitive   = true
}

variable "qdrant_account_id" {
  description = "Account ID generated in Qdrant Cloud (required)"
  type        = string
  sensitive   = true
}