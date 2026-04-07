variable "project_id" {
  description = "The project ID to host the cluster in"
  type        = string
}

variable "cluster_name" {
  description = "The name of the cluster"
  type        = string
}

variable "region" {
  description = "The region for the cluster"
  type        = string
}

variable "zone" {
  description = "The zone for the cluster (if zonal)"
  type        = string
  default     = ""
}

variable "regional" {
  description = "Whether the cluster is regional or zonal"
  type        = bool
  default     = true
}

variable "network" {
  description = "The VPC network to host the cluster in"
  type        = string
}

variable "subnetwork" {
  description = "The subnetwork to host the cluster in"
  type        = string
}

variable "ip_range_pods" {
  description = "The secondary IP range name for pods"
  type        = string
}

variable "ip_range_services" {
  description = "The secondary IP range name for services"
  type        = string
}

variable "kubernetes_version" {
  description = "The Kubernetes version for the cluster"
  type        = string
  default     = "latest"
}

variable "release_channel" {
  description = "The release channel for the cluster"
  type        = string
  default     = "REGULAR"
}

variable "enable_private_endpoint" {
  description = "Whether to enable private endpoint for the cluster master"
  type        = bool
  default     = false
}

variable "enable_private_nodes" {
  description = "Whether to enable private nodes"
  type        = bool
  default     = true
}

variable "master_ipv4_cidr_block" {
  description = "The IP range for the cluster master"
  type        = string
  default     = "172.16.0.0/28"
}

variable "master_authorized_networks" {
  description = "List of master authorized networks"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = []
}

variable "network_policy" {
  description = "Enable network policy addon"
  type        = bool
  default     = true
}

variable "http_load_balancing" {
  description = "Enable HTTP load balancing addon"
  type        = bool
  default     = true
}

variable "horizontal_pod_autoscaling" {
  description = "Enable horizontal pod autoscaling addon"
  type        = bool
  default     = true
}

variable "filestore_csi_driver" {
  description = "Enable Filestore CSI driver"
  type        = bool
  default     = false
}

variable "gcs_fuse_csi_driver" {
  description = "Enable GCS Fuse CSI driver"
  type        = bool
  default     = true
}

variable "enable_workload_identity" {
  description = "Enable workload identity"
  type        = bool
  default     = true
}

variable "enable_shielded_nodes" {
  description = "Enable shielded nodes"
  type        = bool
  default     = true
}

variable "enable_binary_authorization" {
  description = "Enable binary authorization"
  type        = bool
  default     = false
}

variable "maintenance_start_time" {
  description = "Time window for maintenance (HH:MM format)"
  type        = string
  default     = "03:00"
}

variable "monitoring_enabled_components" {
  description = "List of monitoring components to enable"
  type        = list(string)
  default     = ["SYSTEM_COMPONENTS"]
}

variable "monitoring_enable_managed_prometheus" {
  description = "Enable managed Prometheus"
  type        = bool
  default     = true
}

variable "logging_enabled_components" {
  description = "List of logging components to enable"
  type        = list(string)
  default     = ["SYSTEM_COMPONENTS", "WORKLOADS"]
}

variable "enable_resource_usage_export" {
  description = "Enable resource usage export to BigQuery"
  type        = bool
  default     = false
}

variable "resource_usage_export_dataset_id" {
  description = "BigQuery dataset ID for resource usage export"
  type        = string
  default     = ""
}

variable "enable_vertical_pod_autoscaling" {
  description = "Enable vertical pod autoscaling"
  type        = bool
  default     = true
}

variable "security_posture_mode" {
  description = "Security posture mode"
  type        = string
  default     = "BASIC"
}

variable "security_posture_vulnerability_mode" {
  description = "Security posture vulnerability mode"
  type        = string
  default     = "VULNERABILITY_MODE_UNSPECIFIED"
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "node_pools" {
  description = "List of node pools"
  type        = list(any)
  default     = []
}

variable "node_pools_labels" {
  description = "Map of maps containing node labels by node pool name"
  type        = map(map(string))
  default     = {}
}

variable "node_pools_tags" {
  description = "Map of lists containing node tags by node pool name"
  type        = map(list(string))
  default     = {}
}

variable "node_pools_taints" {
  description = "Map of lists containing node taints by node pool name"
  type = map(list(object({
    key    = string
    value  = string
    effect = string
  })))
  default = {}
}
