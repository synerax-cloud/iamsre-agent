# Terraform Outputs for AI SRE Agent Infrastructure

# GKE Cluster Outputs
output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = module.gke.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for the GKE cluster"
  value       = module.gke.cluster_endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate (base64 encoded)"
  value       = module.gke.cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "Location of the GKE cluster"
  value       = module.gke.cluster_location
}

output "get_credentials_command" {
  description = "Command to get GKE cluster credentials"
  value       = "gcloud container clusters get-credentials ${module.gke.cluster_name} --region ${var.region} --project ${var.project_id}"
}

# Network Outputs
output "network_name" {
  description = "Name of the VPC network"
  value       = module.vpc.network_name
}

output "network_self_link" {
  description = "Self link of the VPC network"
  value       = module.vpc.network_self_link
}

output "subnet_names" {
  description = "Names of the subnets"
  value       = module.vpc.subnets_names
}

output "subnet_ips" {
  description = "IP ranges of the subnets"
  value       = module.vpc.subnets_ips
}

# Cloud SQL Outputs
output "cloudsql_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = module.cloudsql.instance_name
}

output "cloudsql_connection_name" {
  description = "Connection name of the Cloud SQL instance"
  value       = module.cloudsql.instance_connection_name
}

output "cloudsql_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = module.cloudsql.private_ip_address
  sensitive   = true
}

output "cloudsql_database_names" {
  description = "Names of the databases"
  value       = module.cloudsql.database_names
}

# Storage Outputs
output "artifacts_bucket_name" {
  description = "Name of the artifacts storage bucket"
  value       = google_storage_bucket.artifacts.name
}

output "artifacts_bucket_url" {
  description = "URL of the artifacts storage bucket"
  value       = google_storage_bucket.artifacts.url
}

output "embeddings_bucket_name" {
  description = "Name of the embeddings storage bucket"
  value       = google_storage_bucket.embeddings.name
}

output "embeddings_bucket_url" {
  description = "URL of the embeddings storage bucket"
  value       = google_storage_bucket.embeddings.url
}

# Artifact Registry Outputs
output "artifact_registry_repository" {
  description = "Name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "artifact_registry_repository_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}"
}

# IAM Outputs
output "service_account_emails" {
  description = "Map of service account emails"
  value       = module.iam.service_account_emails
}

output "service_account_names" {
  description = "Map of service account names"
  value       = module.iam.service_account_names
}

# Secret Manager Outputs
output "secret_names" {
  description = "Names of the Secret Manager secrets"
  value = {
    db_password    = google_secret_manager_secret.db_password.secret_id
    openai_api_key = var.openai_api_key != "" ? google_secret_manager_secret.openai_api_key[0].secret_id : "not-configured"
    jwt_secret     = google_secret_manager_secret.jwt_secret.secret_id
  }
}

# Ingress IP Output
output "ingress_ip_address" {
  description = "Static IP address for ingress"
  value       = google_compute_address.ingress_ip.address
}

# Kubernetes Configuration Commands
output "configure_kubectl" {
  description = "Commands to configure kubectl and access the cluster"
  value = <<-EOT
    # Get cluster credentials
    gcloud container clusters get-credentials ${module.gke.cluster_name} \
      --region ${var.region} \
      --project ${var.project_id}
    
    # Verify connection
    kubectl get nodes
    
    # Create namespace
    kubectl create namespace ai-sre-agent
    
    # Set default namespace
    kubectl config set-context --current --namespace=ai-sre-agent
  EOT
}

# Docker Build and Push Commands
output "docker_push_commands" {
  description = "Commands to build and push Docker images"
  value = <<-EOT
    # Configure Docker to use Artifact Registry
    gcloud auth configure-docker ${var.region}-docker.pkg.dev
    
    # Build and push backend image
    docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/backend:latest ./backend
    docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/backend:latest
    
    # Build and push ai-engine image
    docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/ai-engine:latest ./ai-engine
    docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/ai-engine:latest
    
    # Build and push collector image
    docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/collector:latest ./collector
    docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/collector:latest
    
    # Build and push executor image
    docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/executor:latest ./executor
    docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/executor:latest
    
    # Build and push frontend image
    docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/frontend:latest ./frontend
    docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/frontend:latest
  EOT
}

# Helm Deployment Commands
output "helm_deploy_commands" {
  description = "Commands to deploy using Helm"
  value = <<-EOT
    # Deploy using Helm
    cd helm/ai-sre-agent
    
    helm upgrade --install ai-sre-agent . \
      --namespace ai-sre-agent \
      --create-namespace \
      --set global.projectId=${var.project_id} \
      --set global.region=${var.region} \
      --set global.ingressIP=${google_compute_address.ingress_ip.address} \
      --set backend.image.repository=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/backend \
      --set backend.serviceAccount.name=backend \
      --set backend.serviceAccount.annotations."iam\\.gke\\.io/gcp-service-account"=${module.iam.service_account_emails["backend"]} \
      --set aiEngine.image.repository=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/ai-engine \
      --set aiEngine.serviceAccount.name=ai-engine \
      --set aiEngine.serviceAccount.annotations."iam\\.gke\\.io/gcp-service-account"=${module.iam.service_account_emails["ai-engine"]} \
      --set collector.image.repository=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/collector \
      --set collector.serviceAccount.name=collector \
      --set collector.serviceAccount.annotations."iam\\.gke\\.io/gcp-service-account"=${module.iam.service_account_emails["collector"]} \
      --set executor.image.repository=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/executor \
      --set executor.serviceAccount.name=executor \
      --set executor.serviceAccount.annotations."iam\\.gke\\.io/gcp-service-account"=${module.iam.service_account_emails["executor"]} \
      --set frontend.image.repository=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/frontend
  EOT
}

# Summary Output
output "deployment_summary" {
  description = "Summary of deployed resources"
  sensitive   = true  # Contains sensitive connection strings
  value = <<-EOT
    ========================================
    AI SRE Agent Infrastructure Deployed
    ========================================
    
    Project ID: ${var.project_id}
    Region: ${var.region}
    Environment: ${var.environment}
    
    GKE Cluster: ${module.gke.cluster_name}
    Cluster Endpoint: ${module.gke.cluster_endpoint}
    
    Cloud SQL Instance: ${module.cloudsql.instance_name}
    Database Connection: ${module.cloudsql.instance_connection_name}
    
    Artifact Registry: ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}
    
    Ingress IP: ${google_compute_address.ingress_ip.address}
    
    Service Accounts:
    - Backend: ${module.iam.service_account_emails["backend"]}
    - AI Engine: ${module.iam.service_account_emails["ai-engine"]}
    - Collector: ${module.iam.service_account_emails["collector"]}
    - Executor: ${module.iam.service_account_emails["executor"]}
    
    Next Steps:
    1. Configure kubectl: Run 'terraform output -raw configure_kubectl'
    2. Build and push images: Run 'terraform output -raw docker_push_commands'
    3. Deploy with Helm: Run 'terraform output -raw helm_deploy_commands'
    
    ========================================
  EOT
}
