output "all_packages" {
  value = module.qdrant.all_packages
}

output "cluster_id" {
  value = module.qdrant.cluster_id
}

output "url" {
  value = module.qdrant.url
}

output "key" {
  value     = module.qdrant.key
  sensitive = true
}
