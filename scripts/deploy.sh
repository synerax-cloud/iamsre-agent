#!/bin/bash
# Quick deployment script for AI SRE Agent

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Banner
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   AI-Powered Kubernetes SRE Agent - Quick Deploy     ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."
check_command gcloud
check_command terraform
check_command kubectl
check_command helm
check_command docker

# Get configuration
echo ""
log_info "Please provide the following information:"
echo ""

read -p "GCP Project ID: " PROJECT_ID
read -p "Region [us-central1]: " REGION
REGION=${REGION:-us-central1}
read -p "Cluster Name [ai-sre-cluster]: " CLUSTER_NAME
CLUSTER_NAME=${CLUSTER_NAME:-ai-sre-cluster}
read -p "Domain for ingress (e.g., api.example.com) [skip]: " DOMAIN
read -p "Email for Let's Encrypt [admin@${DOMAIN}]: " EMAIL
EMAIL=${EMAIL:-admin@${DOMAIN}}

echo ""
log_info "Configuration:"
echo "  Project ID:    $PROJECT_ID"
echo "  Region:        $REGION"
echo "  Cluster Name:  $CLUSTER_NAME"
echo "  Domain:        ${DOMAIN:-none}"
echo ""

read -p "Continue with deployment? (yes/no) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Deployment cancelled"
    exit 1
fi

# Set gcloud project
log_info "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable APIs
log_info "Enabling required GCP APIs (this may take a few minutes)..."
gcloud services enable \
    container.googleapis.com \
    compute.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudresourcemanager.googleapis.com \
    servicenetworking.googleapis.com \
    artifactregistry.googleapis.com \
    2>/dev/null || log_warn "Some APIs may already be enabled"

# Deploy Terraform
log_info "Deploying infrastructure with Terraform..."
cd terraform

cat > terraform.tfvars <<EOF
project_id   = "$PROJECT_ID"
region       = "$REGION"
cluster_name = "$CLUSTER_NAME"
environment  = "production"
EOF

terraform init
terraform apply -auto-approve

log_info "Capturing Terraform outputs..."
INGRESS_IP=$(terraform output -raw ingress_ip)
DB_CONNECTION=$(terraform output -raw database_connection_name)

cd ..

# Build and push images
log_info "Building Docker images..."
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent"

gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

log_info "Building backend..."
docker build -t ${REGISTRY}/backend:latest backend/ --quiet

log_info "Building ai-engine..."
docker build -t ${REGISTRY}/ai-engine:latest ai-engine/ --quiet

log_info "Building collector..."
docker build -t ${REGISTRY}/collector:latest collector/ --quiet

log_info "Building executor..."
docker build -t ${REGISTRY}/executor:latest executor/ --quiet

log_info "Pushing images to Artifact Registry..."
docker push ${REGISTRY}/backend:latest
docker push ${REGISTRY}/ai-engine:latest
docker push ${REGISTRY}/collector:latest
docker push ${REGISTRY}/executor:latest

# Configure kubectl
log_info "Configuring kubectl..."
gcloud container clusters get-credentials $CLUSTER_NAME \
    --region $REGION \
    --project $PROJECT_ID

# Install ingress-nginx
log_info "Installing Nginx Ingress Controller..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>/dev/null || true
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace \
    --set controller.service.loadBalancerIP=${INGRESS_IP} \
    --wait

# Install cert-manager if domain provided
if [ ! -z "$DOMAIN" ]; then
    log_info "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # Wait for cert-manager
    kubectl wait --for=condition=available --timeout=300s \
        deployment/cert-manager -n cert-manager
    
    # Create ClusterIssuer
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ${EMAIL}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
fi

# Create Helm values
log_info "Creating Helm values..."
cd helm

INGRESS_CONFIG=""
if [ ! -z "$DOMAIN" ]; then
    INGRESS_CONFIG="ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: ${DOMAIN}
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: backend
              port: 8000
  tls:
    - secretName: ai-sre-tls
      hosts:
        - ${DOMAIN}"
fi

cat > values-prod.yaml <<EOF
global:
  projectId: ${PROJECT_ID}
  region: ${REGION}
  ingressIP: ${INGRESS_IP}

backend:
  image:
    repository: ${REGISTRY}/backend
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: backend@${PROJECT_ID}.iam.gserviceaccount.com

aiEngine:
  image:
    repository: ${REGISTRY}/ai-engine
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: ai-engine@${PROJECT_ID}.iam.gserviceaccount.com

collector:
  image:
    repository: ${REGISTRY}/collector
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: collector@${PROJECT_ID}.iam.gserviceaccount.com

executor:
  image:
    repository: ${REGISTRY}/executor
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: executor@${PROJECT_ID}.iam.gserviceaccount.com

postgresql:
  cloudSql:
    instanceConnectionName: ${DB_CONNECTION}

${INGRESS_CONFIG}
EOF

# Install AI SRE Agent
log_info "Installing AI SRE Agent with Helm..."
helm upgrade --install ai-sre-agent ./ai-sre-agent \
    --namespace ai-sre-agent \
    --create-namespace \
    -f values-prod.yaml \
    --wait \
    --timeout 10m

# Wait for pods
log_info "Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod \
    --all \
    -n ai-sre-agent \
    --timeout=600s

# Pull Ollama models
log_info "Pulling Ollama models (this takes 5-10 minutes)..."
OLLAMA_POD=$(kubectl get pods -n ai-sre-agent \
    -l app.kubernetes.io/component=ollama \
    -o jsonpath='{.items[0].metadata.name}')

log_info "Pulling llama3.1:8b..."
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull llama3.1:8b

log_info "Pulling nomic-embed-text..."
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull nomic-embed-text

# Verify
log_info "Verifying installation..."
kubectl get pods -n ai-sre-agent

# Success message
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║            Deployment Completed Successfully!        ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
log_info "Access your deployment:"
echo ""
echo "  Port-forward (local access):"
echo "    kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000"
echo "    curl http://localhost:8000/health"
echo ""

if [ ! -z "$DOMAIN" ]; then
    echo "  DNS Configuration:"
    echo "    Add this A record to your DNS:"
    echo "    ${DOMAIN} -> ${INGRESS_IP}"
    echo ""
    echo "  After DNS propagates:"
    echo "    https://${DOMAIN}/health"
    echo ""
fi

echo "  Get pods status:"
echo "    kubectl get pods -n ai-sre-agent"
echo ""
echo "  View logs:"
echo "    kubectl logs -n ai-sre-agent deployment/ai-sre-agent-backend"
echo ""
log_info "See docs/DEPLOYMENT.md for detailed configuration and troubleshooting"
echo ""
