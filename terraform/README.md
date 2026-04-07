# Terraform Infrastructure for AI SRE Agent

This directory contains Terraform configurations to deploy a production-ready AI-powered Kubernetes SRE Agent on Google Kubernetes Engine (GKE).

## Architecture Components

The Terraform configuration deploys:

- **GKE Cluster**: Regional, multi-zone Kubernetes cluster with multiple node pools
- **VPC Network**: Custom VPC with subnets and secondary IP ranges for pods/services
- **Cloud SQL**: PostgreSQL instance for metadata storage
- **Cloud Storage**: Buckets for artifacts and embeddings
- **Artifact Registry**: Docker image repository
- **IAM**: Service accounts with Workload Identity bindings
- **Cloud NAT**: Internet access for private nodes
- **Secret Manager**: Secure storage for sensitive credentials
- **Monitoring**: Managed Prometheus and logging configuration

## Prerequisites

1. **Google Cloud SDK**: Install and configure `gcloud`
   ```bash
   curl https://sdk.cloud.google.com | bash
   gcloud init
   gcloud auth application-default login
   ```

2. **Terraform**: Install Terraform >= 1.5.0
   ```bash
   # macOS
   brew install terraform
   
   # Or download from https://www.terraform.io/downloads
   ```

3. **GCP Project**: Create a GCP project and enable billing
   ```bash
   gcloud projects create YOUR_PROJECT_ID
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **GCS Bucket for State**: Create a bucket for Terraform state
   ```bash
   gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_PROJECT_ID-terraform-state
   gsutil versioning set on gs://YOUR_PROJECT_ID-terraform-state
   ```

## Quick Start

### 1. Configure Variables

Copy the example variables file and customize it:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"
environment = "prod"

cluster_name = "ai-sre-agent"
network_name = "ai-sre-network"

# Update master authorized networks with your IP
master_authorized_networks = [
  {
    cidr_block   = "YOUR_IP/32"
    display_name = "My IP"
  }
]

# Set secure passwords (use environment variables in production)
db_password    = "CHANGE-ME-SECURE-PASSWORD"
jwt_secret     = "CHANGE-ME-JWT-SECRET"
openai_api_key = "sk-YOUR-KEY"  # Optional
```

### 2. Update Backend Configuration

Edit `main.tf` and update the backend bucket name:

```hcl
terraform {
  backend "gcs" {
    bucket = "YOUR_PROJECT_ID-terraform-state"
    prefix = "terraform/state"
  }
}
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Review Plan

```bash
terraform plan
```

### 5. Deploy Infrastructure

```bash
terraform apply
```

This will take approximately 15-20 minutes to create all resources.

### 6. Get Outputs

```bash
# View all outputs
terraform output

# Get kubectl configuration command
terraform output -raw configure_kubectl

# Get deployment summary
terraform output -raw deployment_summary
```

## Module Structure

```
terraform/
├── main.tf                  # Main configuration
├── variables.tf             # Input variables
├── outputs.tf               # Output values
├── terraform.tfvars.example # Example variables
├── Makefile                 # Automation commands
└── modules/
    ├── vpc/                 # VPC network module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── gke/                 # GKE cluster module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── cloudsql/            # Cloud SQL module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── iam/                 # IAM and Workload Identity
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── cloud-nat/           # Cloud NAT module
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Important Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `project_id` | GCP project ID | `my-project-123` |
| `region` | GCP region | `us-central1` |
| `db_password` | Cloud SQL password | Use Secret Manager |
| `jwt_secret` | JWT secret for API auth | Use Secret Manager |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `cluster_name` | GKE cluster name | `ai-sre-agent` |
| `kubernetes_version` | K8s version | `1.28` |
| `min_node_count` | Min nodes per zone | `1` |
| `max_node_count` | Max nodes per zone | `5` |
| `enable_private_nodes` | Use private nodes | `true` |
| `cloudsql_tier` | Database instance size | `db-custom-2-7680` |

## Security Best Practices

### 1. Use Environment Variables for Secrets

Instead of storing secrets in `terraform.tfvars`:

```bash
export TF_VAR_db_password="$(gcloud secrets versions access latest --secret=db-password)"
export TF_VAR_jwt_secret="$(gcloud secrets versions access latest --secret=jwt-secret)"
export TF_VAR_openai_api_key="$(gcloud secrets versions access latest --secret=openai-key)"
```

### 2. Restrict Master Authorized Networks

Update the `master_authorized_networks` variable with your specific IP ranges:

```hcl
master_authorized_networks = [
  {
    cidr_block   = "YOUR_OFFICE_IP/32"
    display_name = "Office"
  },
  {
    cidr_block   = "YOUR_VPN_RANGE/24"
    display_name = "VPN"
  }
]
```

### 3. Enable Deletion Protection

For production, ensure deletion protection is enabled:

```hcl
# In variables.tf or terraform.tfvars
deletion_protection = true  # For GKE cluster
```

### 4. Use Private Endpoints

For maximum security, enable private endpoints:

```hcl
enable_private_endpoint = true
enable_private_nodes    = true
```

## Post-Deployment Steps

### 1. Configure kubectl

```bash
# Get credentials
gcloud container clusters get-credentials ai-sre-agent \
  --region us-central1 \
  --project YOUR_PROJECT_ID

# Verify connection
kubectl get nodes
kubectl create namespace ai-sre-agent
```

### 2. Verify Infrastructure

```bash
# Check GKE cluster
gcloud container clusters describe ai-sre-agent --region us-central1

# Check Cloud SQL
gcloud sql instances describe ai-sre-agent-db

# Check service accounts
gcloud iam service-accounts list
```

### 3. Build and Push Images

```bash
# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Get push commands from output
terraform output -raw docker_push_commands
```

### 4. Deploy Applications

```bash
# Get Helm deployment commands
terraform output -raw helm_deploy_commands
```

## Customization

### Adding Node Pools

Edit the `node_pools` variable in `main.tf`:

```hcl
node_pools = [
  {
    name               = "custom-pool"
    machine_type       = "n2-standard-8"
    min_count          = 0
    max_count          = 10
    disk_size_gb       = 200
    disk_type          = "pd-ssd"
    preemptible        = false
  }
]
```

### Enabling GPU Nodes

Set `enable_gpu = true` and configure accelerators:

```hcl
node_pools = [
  {
    name              = "gpu-pool"
    machine_type      = "n1-standard-8"
    accelerator_count = 1
    accelerator_type  = "nvidia-tesla-t4"
    # ... other settings
  }
]
```

### Multi-Region Setup

To deploy in multiple regions, use Terraform workspaces:

```bash
# Create workspace for each region
terraform workspace new us-central1
terraform workspace new europe-west1

# Deploy to each
terraform workspace select us-central1
terraform apply -var="region=us-central1"

terraform workspace select europe-west1
terraform apply -var="region=europe-west1"
```

## Troubleshooting

### API Not Enabled Error

```bash
# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable servicenetworking.googleapis.com
```

### Quota Exceeded

Check and request quota increases:

```bash
gcloud compute project-info describe --project=YOUR_PROJECT_ID
```

Request increases at: https://console.cloud.google.com/iam-admin/quotas

### State Lock Issues

If Terraform state is locked:

```bash
# Force unlock (use carefully)
terraform force-unlock LOCK_ID
```

### Cluster Creation Timeout

Increase timeout in `modules/gke/main.tf`:

```hcl
timeouts {
  create = "60m"
  update = "60m"
}
```

## Maintenance

### Updating Infrastructure

```bash
# Review changes
terraform plan

# Apply updates
terraform apply

# Upgrade Kubernetes version
terraform apply -var="kubernetes_version=1.29"
```

### Backing Up State

```bash
# State is automatically backed up in GCS with versioning
gsutil ls -a gs://YOUR_BUCKET/terraform/state/

# Restore previous version if needed
gsutil cp gs://YOUR_BUCKET/terraform/state/default.tfstate#GENERATION ./
```

### Cost Optimization

- Use preemptible nodes for non-critical workloads
- Enable cluster autoscaling
- Right-size node pools
- Clean up unused resources

```bash
# List resources by cost
gcloud billing accounts list
gcloud alpha billing projects describe YOUR_PROJECT_ID
```

## Cleanup

### Destroying Infrastructure

**WARNING**: This will delete all resources including data!

```bash
# Remove deletion protection first
terraform apply -var="deletion_protection=false"

# Destroy infrastructure
terraform destroy
```

### Selective Cleanup

```bash
# Destroy specific resources
terraform destroy -target=module.gke
terraform destroy -target=google_storage_bucket.artifacts
```

## Support and Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [Workload Identity Guide](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)

## License

Copyright (c) 2026. See LICENSE file for details.
