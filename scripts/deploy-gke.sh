#!/bin/bash
# Deployment script for GKE using Cloud Build

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "╔═══════════════════════════════════════════════════════╗"
echo "║      AI SRE Agent - GKE Deployment Script            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Get configuration
read -p "GCP Project ID: " PROJECT_ID
read -p "Region [us-central1]: " REGION
REGION=${REGION:-us-central1}
read -p "Image Version [v1.0.0]: " VERSION
VERSION=${VERSION:-v1.0.0}

log_info "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region:     $REGION"
echo "  Version:    $VERSION"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# ============================================================
# STEP 1: Deploy Terraform Infrastructure
# ============================================================
log_info "STEP 1: Deploying Terraform Infrastructure..."
cd terraform

# Clean any previous state if needed
if [ -d .terraform ]; then
    log_warn "Found existing Terraform state, cleaning up..."
    rm -rf .terraform .terraform.lock.hcl
fi

if [ ! -f terraform.tfvars ]; then
    log_info "Creating terraform.tfvars..."
    cat > terraform.tfvars <<EOF
project_id   = "${PROJECT_ID}"
region       = "${REGION}"
cluster_name = "ai-sre-cluster"
environment  = "production"
EOF
fi

log_info "Initializing Terraform..."
terraform init

log_info "Planning Terraform deployment..."
terraform plan -out=tfplan

read -p "Deploy infrastructure? (yes/no) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_error "Deployment cancelled"
    exit 1
fi

log_info "Applying Terraform (this takes ~15 minutes)..."
terraform apply tfplan

log_info "Capturing outputs..."
INGRESS_IP=$(terraform output -raw ingress_ip)
DB_CONNECTION=$(terraform output -raw database_connection_name)

cd ..

# ============================================================
# STEP 2: Build Docker Images with Cloud Build
# ============================================================
log_info "STEP 2: Building Docker images with Cloud Build..."
log_info "This uses Google Cloud Build (free tier: 120 build-minutes/day)"

gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_REGION=${REGION},_VERSION=${VERSION} \
    --project=${PROJECT_ID}

log_info "✓ All images built and pushed successfully!"

# ============================================================
# STEP 3: Configure kubectl
# ============================================================
log_info "STEP 3: Configuring kubectl..."
gcloud container clusters get-credentials ai-sre-cluster \
    --region ${REGION} \
    --project ${PROJECT_ID}

# ============================================================
# STEP 4: Install Nginx Ingress Controller
# ============================================================
log_info "STEP 4: Installing Nginx Ingress Controller..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>/dev/null || true
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace \
    --set controller.service.loadBalancerIP=${INGRESS_IP} \
    --wait

# ============================================================
# STEP 5: Deploy AI SRE Agent with Helm
# ============================================================
log_info "STEP 5: Deploying AI SRE Agent..."
cd helm

cat > values-prod.yaml <<EOF
global:
  projectId: ${PROJECT_ID}
  region: ${REGION}
  ingressIP: ${INGRESS_IP}

backend:
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/backend
    tag: ${VERSION}
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: backend@${PROJECT_ID}.iam.gserviceaccount.com

aiEngine:
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/ai-engine
    tag: ${VERSION}
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: ai-engine@${PROJECT_ID}.iam.gserviceaccount.com

collector:
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/collector
    tag: ${VERSION}
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: collector@${PROJECT_ID}.iam.gserviceaccount.com

executor:
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/executor
    tag: ${VERSION}
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: executor@${PROJECT_ID}.iam.gserviceaccount.com

postgresql:
  cloudSql:
    instanceConnectionName: ${DB_CONNECTION}
EOF

helm upgrade --install ai-sre-agent ./ai-sre-agent \
    --namespace ai-sre-agent \
    --create-namespace \
    -f values-prod.yaml \
    --wait \
    --timeout 10m

cd ..

# ============================================================
# STEP 6: Wait for Pods and Pull Ollama Models
# ============================================================
log_info "STEP 6: Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod \
    --all \
    -n ai-sre-agent \
    --timeout=600s

log_info "Pulling Ollama models (this takes 5-10 minutes)..."
OLLAMA_POD=$(kubectl get pods -n ai-sre-agent \
    -l app.kubernetes.io/component=ollama \
    -o jsonpath='{.items[0].metadata.name}')

log_info "Pulling llama3.1:8b..."
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull llama3.1:8b

log_info "Pulling nomic-embed-text..."
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull nomic-embed-text

# ============================================================
# DONE
# ============================================================
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║          Deployment Completed Successfully!          ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
log_info "Your AI SRE Agent is now running!"
echo ""
echo "Test the deployment:"
echo "  kubectl get pods -n ai-sre-agent"
echo ""
echo "Port-forward to test locally:"
echo "  kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000"
echo "  curl http://localhost:8000/health"
echo ""
echo "Ingress IP: ${INGRESS_IP}"
echo "Configure your DNS to point to this IP"
echo ""
log_info "See README.md for API documentation and usage examples"
