output "cluster_name" {
  description = "Cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_id" {
  description = "Cluster ID"
  value       = google_container_cluster.primary.id
}

output "cluster_endpoint" {
  description = "Cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate (base64 encoded)"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "Cluster location (region or zone)"
  value       = google_container_cluster.primary.location
}

output "cluster_region" {
  description = "Cluster region"
  value       = var.region
}

output "node_pools_names" {
  description = "List of node pool names"
  value       = [for np in google_container_node_pool.pools : np.name]
}

output "node_pools_versions" {
  description = "Node pool versions by pool name"
  value       = { for np in google_container_node_pool.pools : np.name => np.version }
}
