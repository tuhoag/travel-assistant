// Get the cluster package
data "qdrant-cloud_booking_packages" "all_packages" {
  cloud_provider = var.cloud_provider
  cloud_region   = var.cloud_region
}

locals {
  desired_package = [
    for pkg in data.qdrant-cloud_booking_packages.all_packages.packages : pkg
    if pkg.type == var.package_type
  ]
}

resource "qdrant-cloud_accounts_cluster" "this" {
  name           = var.cluster_name
  cloud_provider = data.qdrant-cloud_booking_packages.all_packages.cloud_provider
  cloud_region   = data.qdrant-cloud_booking_packages.all_packages.cloud_region
  configuration {
    number_of_nodes = 1
    node_configuration {
      package_id = local.desired_package[0].id
    }
  }
}

resource "qdrant-cloud_accounts_database_api_key_v2" "this" {
  cluster_id = qdrant-cloud_accounts_cluster.this.id
  name       = "${var.cluster_name}-key"
}
