output "all_packages" {
  value = data.qdrant-cloud_booking_packages.all_packages.packages
}

output "cluster_id" {
  value = qdrant-cloud_accounts_cluster.this.id
}

output "url" {
  value = qdrant-cloud_accounts_cluster.this.url
}

output "key" {
  value     = qdrant-cloud_accounts_database_api_key_v2.this.key
  sensitive = true
}
