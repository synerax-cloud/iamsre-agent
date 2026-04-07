#!/bin/bash
# Quick fix and redeploy after Terraform backend issue

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║      Terraform Backend Fixed - Ready to Deploy        ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Get project ID
read -p "Enter your GCP Project ID: " PROJECT_ID

echo ""
echo "Setting up project: $PROJECT_ID"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
echo "[1/4] Enabling required GCP APIs..."
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com \
  servicenetworking.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  2>/dev/null

# Grant Cloud Build permissions
echo "[2/4] Granting Cloud Build permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/container.developer \
  --quiet 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/artifactregistry.writer \
  --quiet 2>/dev/null || true

# Clean Terraform state
echo "[3/4] Cleaning any previous Terraform state..."
cd terraform
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* 2>/dev/null || true
cd ..

echo "[4/4] Initialization complete!"
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║          Now Running Full Deployment                 ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Run deployment
./scripts/deploy-gke.sh
