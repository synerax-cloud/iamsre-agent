# GKE Module - Kubernetes Cluster Configuration
# Creates a production-ready GKE cluster with node pools

resource "google_container_cluster" "primary" {
  provider = google-beta
  
  name     = var.cluster_name
  location = var.regional ? var.region : var.zone
  project  = var.project_id

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network configuration
  network    = var.network
  subnetwork = var.subnetwork

  # IP allocation policy for VPC-native cluster
  ip_allocation_policy {
    cluster_secondary_range_name  = var.ip_range_pods
    services_secondary_range_name = var.ip_range_services
  }

  # Networking configuration
  networking_mode = "VPC_NATIVE"

  # Network policy
  network_policy {
    enabled  = var.network_policy
    provider = var.network_policy ? "PROVIDER_UNSPECIFIED" : null
  }

  # Addons configuration
  addons_config {
    http_load_balancing {
      disabled = !var.http_load_balancing
    }
    horizontal_pod_autoscaling {
      disabled = !var.horizontal_pod_autoscaling
    }
    network_policy_config {
      disabled = !var.network_policy
    }
    gcp_filestore_csi_driver_config {
      enabled = var.filestore_csi_driver
    }
    gcs_fuse_csi_driver_config {
      enabled = var.gcs_fuse_csi_driver
    }
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = var.enable_workload_identity ? "${var.project_id}.svc.id.goog" : null
  }

  # Private cluster configuration
  dynamic "private_cluster_config" {
    for_each = var.enable_private_nodes || var.enable_private_endpoint ? [1] : []
    content {
      enable_private_endpoint = var.enable_private_endpoint
      enable_private_nodes    = var.enable_private_nodes
      master_ipv4_cidr_block  = var.master_ipv4_cidr_block
    }
  }

  # Master authorized networks
  dynamic "master_authorized_networks_config" {
    for_each = length(var.master_authorized_networks) > 0 ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.master_authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = var.maintenance_start_time
    }
  }

  # Release channel
  release_channel {
    channel = var.release_channel
  }

  # Binary authorization
  dynamic "binary_authorization" {
    for_each = var.enable_binary_authorization ? [1] : []
    content {
      evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
    }
  }

  # Shielded nodes
  enable_shielded_nodes = var.enable_shielded_nodes

  # Monitoring and logging configuration
  monitoring_config {
    enable_components = var.monitoring_enabled_components
    
    dynamic "managed_prometheus" {
      for_each = var.monitoring_enable_managed_prometheus ? [1] : []
      content {
        enabled = true
      }
    }
  }

  logging_config {
    enable_components = var.logging_enabled_components
  }

  # Resource usage export (for billing)
  dynamic "resource_usage_export_config" {
    for_each = var.enable_resource_usage_export ? [1] : []
    content {
      enable_network_egress_metering = true
      enable_resource_consumption_metering = true
      
      bigquery_destination {
        dataset_id = var.resource_usage_export_dataset_id
      }
    }
  }

  # Vertical Pod Autoscaling
  vertical_pod_autoscaling {
    enabled = var.enable_vertical_pod_autoscaling
  }

  # Security settings
  security_posture_config {
    mode               = var.security_posture_mode
    vulnerability_mode = var.security_posture_vulnerability_mode
  }

  # Deletion protection
  deletion_protection = var.deletion_protection

  timeouts {
    create = "45m"
    update = "45m"
    delete = "45m"
  }
}

# Node Pools
resource "google_container_node_pool" "pools" {
  for_each = { for np in var.node_pools : np.name => np }

  name       = each.value.name
  project    = var.project_id
  location   = var.regional ? var.region : var.zone
  cluster    = google_container_cluster.primary.name
  
  initial_node_count = lookup(each.value, "initial_node_count", 1)

  # Autoscaling configuration
  autoscaling {
    min_node_count = lookup(each.value, "min_count", 1)
    max_node_count = lookup(each.value, "max_count", 3)
  }

  # Management configuration
  management {
    auto_repair  = lookup(each.value, "auto_repair", true)
    auto_upgrade = lookup(each.value, "auto_upgrade", true)
  }

  # Node configuration
  node_config {
    machine_type = lookup(each.value, "machine_type", "n2-standard-4")
    disk_size_gb = lookup(each.value, "disk_size_gb", 100)
    disk_type    = lookup(each.value, "disk_type", "pd-standard")
    image_type   = lookup(each.value, "image_type", "COS_CONTAINERD")
    preemptible  = lookup(each.value, "preemptible", false)
    spot         = lookup(each.value, "spot", false)

    # Service account
    service_account = lookup(each.value, "service_account", null)
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    # Labels
    labels = merge(
      lookup(var.node_pools_labels, "all", {}),
      lookup(var.node_pools_labels, each.value.name, {})
    )

    # Tags
    tags = concat(
      lookup(var.node_pools_tags, "all", []),
      lookup(var.node_pools_tags, each.value.name, [])
    )

    # Taints
    dynamic "taint" {
      for_each = concat(
        lookup(var.node_pools_taints, "all", []),
        lookup(var.node_pools_taints, each.value.name, [])
      )
      content {
        key    = taint.value.key
        value  = taint.value.value
        effect = taint.value.effect
      }
    }

    # Metadata
    metadata = merge(
      {
        "disable-legacy-endpoints" = "true"
      },
      lookup(each.value, "node_metadata", "GKE_METADATA") == "GKE_METADATA" ? {
        "google-compute-enable-virtio-rng" = "true"
      } : {}
    )

    # Workload metadata config
    workload_metadata_config {
      mode = lookup(each.value, "node_metadata", "GKE_METADATA")
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = lookup(each.value, "enable_secure_boot", false)
      enable_integrity_monitoring = lookup(each.value, "enable_integrity_monitoring", true)
    }

    # GPU configuration (if enabled)
    dynamic "guest_accelerator" {
      for_each = lookup(each.value, "accelerator_count", 0) > 0 ? [1] : []
      content {
        type  = lookup(each.value, "accelerator_type", "nvidia-tesla-t4")
        count = lookup(each.value, "accelerator_count", 1)
        gpu_driver_installation_config {
          gpu_driver_version = "DEFAULT"
        }
      }
    }
  }

  timeouts {
    create = "45m"
    update = "45m"
    delete = "45m"
  }
}
