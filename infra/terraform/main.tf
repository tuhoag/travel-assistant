terraform {
  required_version = ">= 1.7.0"
  required_providers {
    qdrant-cloud = {
      source  = "qdrant/qdrant-cloud"
      version = ">=1.1.0"
    }
  }
}

provider "qdrant-cloud" {
  api_key    = var.qdrant_api_key // API Key generated in Qdrant Cloud (required)
  account_id = var.qdrant_account_id // Account ID generated in Qdrant Cloud (required)
}

module "qdrant" {
  source = "./modules/qdrant"
}
