output "network_name" {
  description = "The name of the VPC network"
  value       = google_compute_network.network.name
}

output "network_self_link" {
  description = "The self link of the VPC network"
  value       = google_compute_network.network.self_link
}

output "subnets_names" {
  description = "List of subnet names"
  value       = [for subnet in google_compute_subnetwork.subnets : subnet.name]
}

output "subnets_ips" {
  description = "List of subnet IP ranges"
  value       = [for subnet in google_compute_subnetwork.subnets : subnet.ip_cidr_range]
}

output "subnets_self_links" {
  description = "List of subnet self links"
  value       = [for subnet in google_compute_subnetwork.subnets : subnet.self_link]
}

output "subnets_regions" {
  description = "List of subnet regions"
  value       = [for subnet in google_compute_subnetwork.subnets : subnet.region]
}
