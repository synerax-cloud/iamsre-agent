#!/bin/bash
# Setup script to prepare for first-time deployment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "╔═══════════════════════════════════════════════════════╗"
echo "║      AI SRE Agent - Initial Setup                    ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Get project ID
read -p "Enter your GCP Project ID: " PROJECT_ID

log_info "Setting GCP project..."
gcloud config set project $PROJECT_ID

log_info "Enabling required APIs..."
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com \
  servicenetworking.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

log_info "Checking if terraform state bucket exists..."
BUCKET_NAME="ai-sre-agent-terraform-state-${PROJECT_ID}"

if ! gcloud storage buckets describe gs://${BUCKET_NAME} &>/dev/null; then
    log_warn "Terraform state bucket doesn't exist"
    read -p "Create GCS bucket for Terraform state? (yes/no) " -r
    if [[ $REPLY =~ ^[Yy] ]]; then
        log_info "Creating GCS bucket for Terraform state..."
        gcloud storage buckets create gs://${BUCKET_NAME} \
            --location=us-central1 \
            --uniform-bucket-level-access
        
        log_info "Enabling versioning on state bucket..."
        gcloud storage buckets update gs://${BUCKET_NAME} --versioning
        
        log_info "✓ Bucket created: gs://${BUCKET_NAME}"
        log_warn "Update terraform/main.tf to uncomment the backend configuration"
    else
        log_info "Using local Terraform state (recommended for testing)"
        log_warn "Make sure backend 'gcs' block is commented out in terraform/main.tf"
    fi
else
    log_info "✓ Terraform state bucket already exists"
fi

log_info "Checking Cloud Build permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant Cloud Build necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
    --role=roles/container.developer \
    --no-user-output-enabled || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
    --role=roles/artifactregistry.writer \
    --no-user-output-enabled || true

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║          Initial Setup Complete!                     ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
log_info "Next steps:"
echo "  1. Run: cd terraform"
echo "  2. Run: terraform init"
echo "  3. Run: cd .. && ./scripts/deploy-gke.sh"
echo ""
