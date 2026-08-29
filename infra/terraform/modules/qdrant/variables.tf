variable "cluster_name" {
  description = "Name of the Qdrant Cloud cluster"
  type        = string
  default     = "tf-travel-assistant"
}

variable "cloud_provider" {
  description = "Cloud provider to host the Qdrant cluster on"
  type        = string
  default     = "aws"
}

variable "cloud_region" {
  description = "Cloud region to host the Qdrant cluster in"
  type        = string
  default     = "eu-central-1"
}

variable "package_type" {
  description = "Qdrant Cloud package type to select (e.g. \"free\" or \"paid\")"
  type        = string
  default     = "free"
}
