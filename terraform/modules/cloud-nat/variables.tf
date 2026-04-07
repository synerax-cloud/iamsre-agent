variable "project_id" {
  description = "The project ID"
  type        = string
}

variable "region" {
  description = "The region for the Cloud NAT"
  type        = string
}

variable "router" {
  description = "The name of the Cloud Router"
  type        = string
}

variable "network" {
  description = "The VPC network name"
  type        = string
}

variable "bgp_asn" {
  description = "BGP ASN for the router"
  type        = number
  default     = 64514
}

variable "nat_ip_allocate_option" {
  description = "How external IPs should be allocated (AUTO_ONLY or MANUAL_ONLY)"
  type        = string
  default     = "AUTO_ONLY"
}

variable "source_subnetwork_ip_ranges_to_nat" {
  description = "How NAT should be configured per subnetwork"
  type        = string
  default     = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

variable "nat_ips" {
  description = "List of self-link of external IPs for NAT"
  type        = list(string)
  default     = []
}

variable "enable_logging" {
  description = "Enable NAT logging"
  type        = bool
  default     = true
}

variable "log_filter" {
  description = "NAT log filter (ERRORS_ONLY, TRANSLATIONS_ONLY, ALL)"
  type        = string
  default     = "ERRORS_ONLY"
}

variable "min_ports_per_vm" {
  description = "Minimum number of ports allocated to a VM"
  type        = number
  default     = 64
}

variable "tcp_established_idle_timeout_sec" {
  description = "Timeout for established TCP connections"
  type        = number
  default     = 1200
}

variable "tcp_transitory_idle_timeout_sec" {
  description = "Timeout for transitory TCP connections"
  type        = number
  default     = 30
}

variable "tcp_time_wait_timeout_sec" {
  description = "Timeout for TCP connections in TIME_WAIT state"
  type        = number
  default     = 120
}

variable "udp_idle_timeout_sec" {
  description = "Timeout for UDP connections"
  type        = number
  default     = 30
}

variable "icmp_idle_timeout_sec" {
  description = "Timeout for ICMP connections"
  type        = number
  default     = 30
}

variable "enable_dynamic_port_allocation" {
  description = "Enable dynamic port allocation"
  type        = bool
  default     = true
}

variable "enable_endpoint_independent_mapping" {
  description = "Enable endpoint independent mapping"
  type        = bool
  default     = false
}
