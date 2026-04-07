# Cloud NAT Module - Provides internet access for private GKE nodes
# Creates a Cloud Router and Cloud NAT configuration

resource "google_compute_router" "router" {
  name    = var.router
  region  = var.region
  network = var.network
  project = var.project_id

  bgp {
    asn = var.bgp_asn
  }
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.router}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = var.nat_ip_allocate_option
  source_subnetwork_ip_ranges_to_nat = var.source_subnetwork_ip_ranges_to_nat

  # Static IPs for NAT (optional)
  nat_ips = var.nat_ips

  # Logging configuration
  log_config {
    enable = var.enable_logging
    filter = var.log_filter
  }

  # Minimum ports per VM
  min_ports_per_vm = var.min_ports_per_vm

  # TCP timeouts
  tcp_established_idle_timeout_sec = var.tcp_established_idle_timeout_sec
  tcp_transitory_idle_timeout_sec  = var.tcp_transitory_idle_timeout_sec
  tcp_time_wait_timeout_sec        = var.tcp_time_wait_timeout_sec

  # UDP timeout
  udp_idle_timeout_sec = var.udp_idle_timeout_sec

  # ICMP timeout
  icmp_idle_timeout_sec = var.icmp_idle_timeout_sec

  # Enable dynamic port allocation
  enable_dynamic_port_allocation = var.enable_dynamic_port_allocation

  # Endpoint independent mapping
  enable_endpoint_independent_mapping = var.enable_endpoint_independent_mapping
}
