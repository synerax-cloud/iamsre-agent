# VPC Module - Network Configuration
# Creates VPC network with subnets and secondary ranges for GKE

resource "google_compute_network" "network" {
  name                    = var.network_name
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  project                 = var.project_id
}

resource "google_compute_subnetwork" "subnets" {
  for_each = { for subnet in var.subnets : subnet.subnet_name => subnet }

  name                     = each.value.subnet_name
  ip_cidr_range            = each.value.subnet_ip
  region                   = each.value.subnet_region
  project                  = var.project_id
  network                  = google_compute_network.network.name
  private_ip_google_access = lookup(each.value, "private_ip_google_access", true)

  dynamic "secondary_ip_range" {
    for_each = lookup(var.secondary_ranges, each.value.subnet_name, [])
    content {
      range_name    = secondary_ip_range.value.range_name
      ip_cidr_range = secondary_ip_range.value.ip_cidr_range
    }
  }
}

# Firewall rule to allow internal communication
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.network_name}-allow-internal"
  network = google_compute_network.network.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16"
  ]
}
