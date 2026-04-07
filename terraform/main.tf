# Main Terraform Configuration for AI SRE Agent on GKE
# This deploys a production-ready GKE cluster with all supporting infrastructure

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  # Backend configuration for state storage
  # For initial deployment, using local state (comment out for production)
  # To use remote state, create GCS bucket first:
  # gcloud storage buckets create gs://ai-sre-agent-terraform-state-${PROJECT_ID} --location=us-central1
  # Then uncomment below:
  # backend "gcs" {
  #   bucket = "ai-sre-agent-terraform-state-${PROJECT_ID}"
  #   prefix = "terraform/state"
  # }
}

# Provider Configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Data source for GKE cluster authentication
data "google_client_config" "default" {}

data "google_container_cluster" "primary" {
  name     = module.gke.cluster_name
  location = var.region
  
  depends_on = [module.gke]
}

provider "kubernetes" {
  host                   = "https://${data.google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(data.google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${data.google_container_cluster.primary.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(data.google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
  }
}

# Enable required GCP APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "servicenetworking.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# VPC Network Module
module "vpc" {
  source = "./modules/vpc"

  project_id   = var.project_id
  network_name = var.network_name
  region       = var.region
  
  # Subnet configuration
  subnets = [
    {
      subnet_name   = "${var.network_name}-gke-subnet"
      subnet_ip     = "10.0.0.0/20"
      subnet_region = var.region
    },
  ]

  # Secondary ranges for GKE pods and services
  secondary_ranges = {
    "${var.network_name}-gke-subnet" = [
      {
        range_name    = "pods"
        ip_cidr_range = "10.4.0.0/14"
      },
      {
        range_name    = "services"
        ip_cidr_range = "10.8.0.0/20"
      },
    ]
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud NAT for private GKE nodes
module "cloud_nat" {
  source = "./modules/cloud-nat"

  project_id = var.project_id
  region     = var.region
  router     = "${var.network_name}-router"
  network    = module.vpc.network_name
}

# GKE Cluster Module
module "gke" {
  source = "./modules/gke"

  project_id        = var.project_id
  cluster_name      = var.cluster_name
  region            = var.region
  network           = module.vpc.network_name
  subnetwork        = module.vpc.subnets_names[0]
  ip_range_pods     = "pods"
  ip_range_services = "services"

  # Cluster configuration
  kubernetes_version      = var.kubernetes_version
  release_channel         = "REGULAR"
  regional                = true
  enable_private_endpoint = false
  enable_private_nodes    = true
  master_ipv4_cidr_block = "172.16.0.0/28"

  # Workload Identity
  enable_workload_identity = true

  # Security features
  enable_shielded_nodes       = true
  enable_binary_authorization = false
  enable_pod_security_policy  = false

  # Networking
  network_policy             = true
  http_load_balancing        = true
  horizontal_pod_autoscaling = true
  
  # Monitoring
  monitoring_enable_managed_prometheus = true
  logging_enabled_components          = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  monitoring_enabled_components       = ["SYSTEM_COMPONENTS"]

  # Master authorized networks (adjust as needed)
  master_authorized_networks = var.master_authorized_networks

  # Node pools configuration
  node_pools = [
    {
      name               = "default-pool"
      machine_type       = "n2-standard-4"
      min_count          = 1
      max_count          = 5
      initial_node_count = 2
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      image_type         = "COS_CONTAINERD"
      auto_repair        = true
      auto_upgrade       = true
      preemptible        = false
      
      node_metadata      = "GKE_METADATA"
    },
    {
      name               = "ai-workload-pool"
      machine_type       = "n2-standard-8"
      min_count          = 0
      max_count          = 10
      initial_node_count = 1
      disk_size_gb       = 200
      disk_type          = "pd-ssd"
      image_type         = "COS_CONTAINERD"
      auto_repair        = true
      auto_upgrade       = true
      preemptible        = false
      
      node_metadata      = "GKE_METADATA"
      
      # GPU configuration for AI workloads (optional)
      # accelerator_count = 1
      # accelerator_type  = "nvidia-tesla-t4"
    },
    {
      name               = "spot-pool"
      machine_type       = "n2-standard-4"
      min_count          = 0
      max_count          = 10
      initial_node_count = 0
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      image_type         = "COS_CONTAINERD"
      auto_repair        = true
      auto_upgrade       = true
      preemptible        = true  # Spot instances for cost savings
      
      node_metadata      = "GKE_METADATA"
    },
  ]

  node_pools_labels = {
    all = {
      environment = var.environment
      managed-by  = "terraform"
    }
    default-pool = {
      workload-type = "general"
    }
    ai-workload-pool = {
      workload-type = "ai"
    }
    spot-pool = {
      workload-type = "spot"
    }
  }

  node_pools_taints = {
    ai-workload-pool = [
      {
        key    = "workload-type"
        value  = "ai"
        effect = "NO_SCHEDULE"
      }
    ]
    spot-pool = [
      {
        key    = "cloud.google.com/gke-preemptible"
        value  = "true"
        effect = "NO_SCHEDULE"
      }
    ]
  }

  depends_on = [
    module.vpc,
    google_project_service.required_apis
  ]
}

# Cloud SQL for metadata storage
module "cloudsql" {
  source = "./modules/cloudsql"

  project_id = var.project_id
  region     = var.region
  
  instance_name = "${var.cluster_name}-db"
  database_version = "POSTGRES_15"
  
  tier = "db-custom-2-7680"  # 2 vCPU, 7.68 GB RAM
  
  availability_type = "REGIONAL"  # High availability
  disk_size        = 50
  disk_type        = "PD_SSD"
  
  # Backup configuration
  backup_enabled              = true
  backup_start_time          = "03:00"
  point_in_time_recovery     = true
  retained_backups           = 7
  
  # Network
  private_network = module.vpc.network_self_link
  
  # Databases to create
  databases = ["ai_sre_agent", "vector_store"]
  
  # Users to create
  users = [
    {
      name     = "app_user"
      password = var.db_password
    }
  ]

  depends_on = [
    module.vpc,
    google_project_service.required_apis
  ]
}

# Google Cloud Storage for artifacts and embeddings
resource "google_storage_bucket" "artifacts" {
  name          = "${var.project_id}-ai-sre-artifacts"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "embeddings" {
  name          = "${var.project_id}-ai-sre-embeddings"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "ai-sre-agent"
  description   = "Docker repository for AI SRE Agent images"
  format        = "DOCKER"
}

# IAM Module - Service Accounts and Workload Identity
module "iam" {
  source = "./modules/iam"

  project_id   = var.project_id
  cluster_name = var.cluster_name
  
  # Service accounts for different components
  service_accounts = {
    backend = {
      account_id   = "ai-sre-backend"
      display_name = "AI SRE Backend Service Account"
      description  = "Service account for backend API"
      roles = [
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/cloudtrace.agent",
      ]
    }
    ai-engine = {
      account_id   = "ai-sre-ai-engine"
      display_name = "AI SRE AI Engine Service Account"
      description  = "Service account for AI engine"
      roles = [
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/storage.objectViewer",
      ]
    }
    collector = {
      account_id   = "ai-sre-collector"
      display_name = "AI SRE Collector Service Account"
      description  = "Service account for observability collector"
      roles = [
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/monitoring.viewer",
      ]
    }
    executor = {
      account_id   = "ai-sre-executor"
      display_name = "AI SRE Executor Service Account"
      description  = "Service account for action executor"
      roles = [
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/container.developer",  # For K8s operations
      ]
    }
  }
  
  # Workload Identity bindings
  workload_identity_bindings = {
    backend = {
      service_account = "ai-sre-backend"
      namespace       = "ai-sre-agent"
      ksa_name        = "backend"
    }
    ai-engine = {
      service_account = "ai-sre-ai-engine"
      namespace       = "ai-sre-agent"
      ksa_name        = "ai-engine"
    }
    collector = {
      service_account = "ai-sre-collector"
      namespace       = "ai-sre-agent"
      ksa_name        = "collector"
    }
    executor = {
      service_account = "ai-sre-executor"
      namespace       = "ai-sre-agent"
      ksa_name        = "executor"
    }
  }

  depends_on = [
    module.gke,
    google_project_service.required_apis
  ]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.cluster_name}-db-password"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "openai_api_key" {
  count = var.openai_api_key != "" ? 1 : 0
  
  secret_id = "${var.cluster_name}-openai-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  count = var.openai_api_key != "" ? 1 : 0
  
  secret      = google_secret_manager_secret.openai_api_key[0].id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${var.cluster_name}-jwt-secret"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret
}

# Grant secret access to service accounts
resource "google_secret_manager_secret_iam_member" "backend_secrets" {
  for_each = toset([
    google_secret_manager_secret.db_password.id,
    google_secret_manager_secret.jwt_secret.id,
  ])
  
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.iam.service_account_emails["backend"]}"
}

resource "google_secret_manager_secret_iam_member" "ai_engine_secrets" {
  count = var.openai_api_key != "" ? 1 : 0
  
  secret_id = google_secret_manager_secret.openai_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"  
  member    = "serviceAccount:${module.iam.service_account_emails["ai-engine"]}"
}

# Storage bucket IAM
resource "google_storage_bucket_iam_member" "artifacts_backend" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${module.iam.service_account_emails["backend"]}"
}

resource "google_storage_bucket_iam_member" "embeddings_ai_engine" {
  bucket = google_storage_bucket.embeddings.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${module.iam.service_account_emails["ai-engine"]}"
}

# Cloud SQL IAM
resource "google_project_iam_member" "cloudsql_client" {
  for_each = toset(["backend", "ai-engine"])
  
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${module.iam.service_account_emails[each.key]}"
}

# Static IP for Ingress
resource "google_compute_address" "ingress_ip" {
  name   = "${var.cluster_name}-ingress-ip"
  region = var.region
}

# DNS Zone (optional - adjust as needed)
# resource "google_dns_managed_zone" "main" {
#   name     = "${var.cluster_name}-zone"
#   dns_name = "${var.domain_name}."
# }

# resource "google_dns_record_set" "ingress" {
#   name         = "api.${var.domain_name}."
#   type         = "A"
#   ttl          = 300
#   managed_zone = google_dns_managed_zone.main.name
#   rrdatas      = [google_compute_address.ingress_ip.address]
# }
