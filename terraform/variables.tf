# Terraform Variables for AI SRE Agent Infrastructure

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
  default     = "ai-sre-agent"
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "ai-sre-network"
}

variable "kubernetes_version" {
  description = "Kubernetes version for GKE cluster"
  type        = string
  default     = "1.28"
}

variable "master_authorized_networks" {
  description = "List of master authorized networks"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = [
    {
      cidr_block   = "0.0.0.0/0"  # Update with your IP ranges for security
      display_name = "All"
    }
  ]
}

variable "db_password" {
  description = "Password for the Cloud SQL database"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for LLM integration"
  type        = string
  sensitive   = true
  default     = ""  # Leave empty if using self-hosted LLM
}

variable "jwt_secret" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "enable_gpu" {
  description = "Enable GPU nodes for AI workloads"
  type        = bool
  default     = false
}

variable "enable_monitoring" {
  description = "Enable advanced monitoring features"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "node_pool_machine_type" {
  description = "Machine type for default node pool"
  type        = string
  default     = "n2-standard-4"
}

variable "ai_node_pool_machine_type" {
  description = "Machine type for AI workload node pool"
  type        = string
  default     = "n2-standard-8"
}

variable "min_node_count" {
  description = "Minimum number of nodes per zone"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes per zone"
  type        = number
  default     = 5
}

variable "disk_size_gb" {
  description = "Disk size in GB for nodes"
  type        = number
  default     = 100
}

variable "enable_private_endpoint" {
  description = "Enable private endpoint for GKE master"
  type        = bool
  default     = false
}

variable "enable_private_nodes" {
  description = "Enable private nodes (nodes without external IPs)"
  type        = bool
  default     = true
}

variable "enable_workload_identity" {
  description = "Enable workload identity"
  type        = bool
  default     = true
}

variable "enable_binary_authorization" {
  description = "Enable binary authorization"
  type        = bool
  default     = false
}

variable "cloudsql_tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-custom-2-7680"
}

variable "cloudsql_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 50
}

variable "cloudsql_availability_type" {
  description = "Cloud SQL availability type (REGIONAL or ZONAL)"
  type        = string
  default     = "REGIONAL"
}

variable "artifact_retention_days" {
  description = "Number of days to retain artifacts in GCS"
  type        = number
  default     = 90
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project    = "ai-sre-agent"
    managed-by = "terraform"
  }
}
