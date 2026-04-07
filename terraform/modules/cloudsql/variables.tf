variable "project_id" {
  description = "The project ID"
  type        = string
}

variable "instance_name" {
  description = "The name of the Cloud SQL instance"
  type        = string
}

variable "region" {
  description = "The region of the Cloud SQL instance"
  type        = string
}

variable "database_version" {
  description = "The database version"
  type        = string
  default     = "POSTGRES_15"
}

variable "tier" {
  description = "The machine tier for the Cloud SQL instance"
  type        = string
  default     = "db-custom-2-7680"
}

variable "availability_type" {
  description = "The availability type (REGIONAL or ZONAL)"
  type        = string
  default     = "REGIONAL"
}

variable "disk_size" {
  description = "The disk size in GB"
  type        = number
  default     = 50
}

variable "disk_type" {
  description = "The disk type (PD_SSD or PD_HDD)"
  type        = string
  default     = "PD_SSD"
}

variable "disk_autoresize" {
  description = "Enable automatic disk size increase"
  type        = bool
  default     = true
}

variable "backup_enabled" {
  description = "Enable backups"
  type        = bool
  default     = true
}

variable "backup_start_time" {
  description = "Backup start time in HH:MM format"
  type        = string
  default     = "03:00"
}

variable "point_in_time_recovery" {
  description = "Enable point in time recovery"
  type        = bool
  default     = true
}

variable "transaction_log_retention_days" {
  description = "Number of days to retain transaction logs"
  type        = number
  default     = 7
}

variable "retained_backups" {
  description = "Number of backups to retain"
  type        = number
  default     = 7
}

variable "ipv4_enabled" {
  description = "Enable IPv4 for the instance"
  type        = bool
  default     = false
}

variable "private_network" {
  description = "The VPC network from which the Cloud SQL instance is accessible"
  type        = string
}

variable "require_ssl" {
  description = "Require SSL for connections"
  type        = bool
  default     = true
}

variable "authorized_networks" {
  description = "List of authorized networks"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "maintenance_window_day" {
  description = "Day of week for maintenance window (1-7, Sunday = 7)"
  type        = number
  default     = 7
}

variable "maintenance_window_hour" {
  description = "Hour of day for maintenance window (0-23)"
  type        = number
  default     = 3
}

variable "maintenance_window_update_track" {
  description = "Maintenance track (stable or canary)"
  type        = string
  default     = "stable"
}

variable "database_flags" {
  description = "Database flags to set"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "query_insights_enabled" {
  description = "Enable query insights"
  type        = bool
  default     = true
}

variable "query_string_length" {
  description = "Maximum query string length"
  type        = number
  default     = 1024
}

variable "record_application_tags" {
  description = "Record application tags in query insights"
  type        = bool
  default     = false
}

variable "record_client_address" {
  description = "Record client address in query insights"
  type        = bool
  default     = false
}

variable "user_labels" {
  description = "User labels"
  type        = map(string)
  default     = {}
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "databases" {
  description = "List of databases to create"
  type        = list(string)
  default     = []
}

variable "users" {
  description = "List of users to create"
  type = list(object({
    name     = string
    password = string
  }))
  default = []
}

variable "read_replica_enabled" {
  description = "Enable read replicas"
  type        = bool
  default     = false
}

variable "read_replica_count" {
  description = "Number of read replicas"
  type        = number
  default     = 0
}

variable "read_replica_region" {
  description = "Region for read replicas (defaults to main region)"
  type        = string
  default     = ""
}

variable "read_replica_tier" {
  description = "Tier for read replicas (defaults to main tier)"
  type        = string
  default     = ""
}
