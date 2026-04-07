# Cloud SQL Module - PostgreSQL Database Configuration
# Creates a highly available Cloud SQL instance for metadata storage

resource "google_sql_database_instance" "instance" {
  name             = var.instance_name
  database_version = var.database_version
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_size         = var.disk_size
    disk_type         = var.disk_type
    disk_autoresize   = var.disk_autoresize
    
    # Backup configuration
    backup_configuration {
      enabled                        = var.backup_enabled
      start_time                     = var.backup_start_time
      point_in_time_recovery_enabled = var.point_in_time_recovery
      transaction_log_retention_days = var.transaction_log_retention_days
      backup_retention_settings {
        retained_backups = var.retained_backups
        retention_unit   = "COUNT"
      }
    }

    # IP configuration
    ip_configuration {
      ipv4_enabled    = var.ipv4_enabled
      private_network = var.private_network
      require_ssl     = var.require_ssl

      dynamic "authorized_networks" {
        for_each = var.authorized_networks
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.value
        }
      }
    }

    # Maintenance window
    maintenance_window {
      day          = var.maintenance_window_day
      hour         = var.maintenance_window_hour
      update_track = var.maintenance_window_update_track
    }

    # Database flags
    dynamic "database_flags" {
      for_each = var.database_flags
      content {
        name  = database_flags.value.name
        value = database_flags.value.value
      }
    }

    # Insights config
    insights_config {
      query_insights_enabled  = var.query_insights_enabled
      query_string_length     = var.query_string_length
      record_application_tags = var.record_application_tags
      record_client_address   = var.record_client_address
    }

    # User labels
    user_labels = var.user_labels
  }

  deletion_protection = var.deletion_protection

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }
}

# Create databases
resource "google_sql_database" "databases" {
  for_each = toset(var.databases)

  name     = each.value
  instance = google_sql_database_instance.instance.name
  project  = var.project_id
}

# Create users
resource "google_sql_user" "users" {
  for_each = { for user in var.users : user.name => user }

  name     = each.value.name
  instance = google_sql_database_instance.instance.name
  password = each.value.password
  project  = var.project_id
}

# Read replica (optional)
resource "google_sql_database_instance" "replica" {
  count = var.read_replica_enabled ? var.read_replica_count : 0

  name                 = "${var.instance_name}-replica-${count.index}"
  database_version     = var.database_version
  region               = var.read_replica_region != "" ? var.read_replica_region : var.region
  project              = var.project_id
  master_instance_name = google_sql_database_instance.instance.name

  replica_configuration {
    failover_target = false
  }

  settings {
    tier              = var.read_replica_tier != "" ? var.read_replica_tier : var.tier
    availability_type = "ZONAL"
    disk_size         = var.disk_size
    disk_type         = var.disk_type
    disk_autoresize   = var.disk_autoresize

    ip_configuration {
      ipv4_enabled    = var.ipv4_enabled
      private_network = var.private_network
      require_ssl     = var.require_ssl
    }

    user_labels = var.user_labels
  }

  deletion_protection = var.deletion_protection

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }
}
