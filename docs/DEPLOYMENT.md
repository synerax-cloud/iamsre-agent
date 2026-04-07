# Deployment Guide

This guide walks you through deploying the AI-Powered Kubernetes SRE Agent to Google Kubernetes Engine (GKE).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GCP Setup](#gcp-setup)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [Building Docker Images](#building-docker-images)
5. [Helm Installation](#helm-installation)
6. [Post-Installation Configuration](#post-installation-configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

Install the following tools before starting:

```bash
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Terraform 1.5+
brew install terraform  # macOS
# OR
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# kubectl
gcloud components install kubectl

# Helm 3.8+
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Docker
# Follow instructions at https://docs.docker.com/get-docker/
```

### GCP Requirements

- **Project**: Active GCP project with billing enabled
- **APIs**: Enable required APIs (done automatically by Terraform)
- **Permissions**: Project Owner or these roles:
  - Compute Admin
  - Kubernetes Engine Admin
  - Service Account Admin
  - Cloud SQL Admin
  - Secret Manager Admin

---

## GCP Setup

### 1. Configure gcloud

```bash
# Login
gcloud auth login
gcloud auth application-default login

# Set project
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Set region
export REGION="us-central1"
gcloud config set compute/region $REGION
```

### 2. Enable APIs

```bash
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com \
  servicenetworking.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Create Service Account for Terraform

```bash
# Create service account
gcloud iam service-accounts create terraform-deployer \
  --display-name "Terraform Deployer"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:terraform-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/editor"

# Generate key
gcloud iam service-accounts keys create ~/terraform-key.json \
  --iam-account=terraform-deployer@${PROJECT_ID}.iam.gserviceaccount.com

# Export
export GOOGLE_APPLICATION_CREDENTIALS=~/terraform-key.json
```

---

## Infrastructure Deployment

### 1. Configure Terraform

```bash
cd terraform

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id   = "${PROJECT_ID}"
region       = "us-central1"
cluster_name = "ai-sre-cluster"
environment  = "production"

# Optional: customize these
node_pool_machine_type = "e2-standard-4"
ai_node_pool_machine_type = "n1-standard-8"
db_instance_tier = "db-g1-small"
EOF
```

### 2. Initialize and Deploy

```bash
# Initialize
terraform init

# Validate configuration
terraform validate

# Plan (review changes)
terraform plan -out=tfplan

# Apply (takes 15-20 minutes)
terraform apply tfplan
```

### 3. Capture Outputs

```bash
# Save outputs for later use
terraform output -json > ../outputs.json

# Key outputs:
# - cluster_name
# - cluster_endpoint
# - database_instance_name
# - database_connection_name
# - ingress_ip
# - service_account_emails
```

---

## Building Docker Images

### 1. Configure Docker Registry

```bash
# Authenticate
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Terraform creates the repository automatically
# Repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent
```

### 2. Build Images

Create a build script:

```bash
cat > ../scripts/build-images.sh <<'EOF'
#!/bin/bash
set -e

PROJECT_ID=${1:-$PROJECT_ID}
REGION=${2:-us-central1}
VERSION=${3:-latest}

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent"

echo "Building images for project: $PROJECT_ID"
echo "Registry: $REGISTRY"

# Backend
echo "Building backend..."
docker build -t ${REGISTRY}/backend:${VERSION} ../backend/
docker push ${REGISTRY}/backend:${VERSION}

# AI Engine
echo "Building ai-engine..."
docker build -t ${REGISTRY}/ai-engine:${VERSION} ../ai-engine/
docker push ${REGISTRY}/ai-engine:${VERSION}

# Collector
echo "Building collector..."
docker build -t ${REGISTRY}/collector:${VERSION} ../collector/
docker push ${REGISTRY}/collector:${VERSION}

# Executor
echo "Building executor..."
docker build -t ${REGISTRY}/executor:${VERSION} ../executor/
docker push ${REGISTRY}/executor:${VERSION}

echo "All images built and pushed successfully!"
EOF

chmod +x ../scripts/build-images.sh
```

### 3. Execute Build

```bash
cd ..
./scripts/build-images.sh $PROJECT_ID $REGION v1.0.0
```

---

## Helm Installation

### 1. Configure kubectl

```bash
# Get cluster credentials
gcloud container clusters get-credentials ai-sre-cluster \
  --region us-central1 \
  --project $PROJECT_ID

# Verify connection
kubectl cluster-info
kubectl get nodes
```

### 2. Create Production Values

```bash
cd helm

# Get Terraform outputs
INGRESS_IP=$(cd ../terraform && terraform output -raw ingress_ip)
DB_CONNECTION=$(cd ../terraform && terraform output -raw database_connection_name)

# Create values file
cat > values-production.yaml <<EOF
global:
  projectId: ${PROJECT_ID}
  region: ${REGION}
  ingressIP: ${INGRESS_IP}

backend:
  enabled: true
  replicaCount: 2
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/backend
    tag: v1.0.0
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: backend@${PROJECT_ID}.iam.gserviceaccount.com
  env:
    DATABASE_URL: "postgresql+asyncpg://postgres:CHANGE_ME@localhost:5432/ai_sre"
    LLM_PROVIDER: "ollama"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10

aiEngine:
  enabled: true
  replicaCount: 2
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/ai-engine
    tag: v1.0.0
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: ai-engine@${PROJECT_ID}.iam.gserviceaccount.com
  persistence:
    enabled: true
    size: 10Gi

collector:
  enabled: true
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/collector
    tag: v1.0.0
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: collector@${PROJECT_ID}.iam.gserviceaccount.com

executor:
  enabled: true
  image:
    repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/executor
    tag: v1.0.0
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: executor@${PROJECT_ID}.iam.gserviceaccount.com

ollama:
  enabled: true
  resources:
    requests:
      cpu: 2000m
      memory: 8Gi
    limits:
      cpu: 4000m
      memory: 16Gi
  persistence:
    enabled: true
    size: 50Gi
  nodeSelector:
    workload: ai  # Place on AI node pool

postgresql:
  cloudSql:
    instanceConnectionName: ${DB_CONNECTION}

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.yourdomain.com
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
        - api.yourdomain.com
EOF
```

### 3. Install Nginx Ingress Controller

```bash
# Install ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.loadBalancerIP=${INGRESS_IP}

# Wait for ingress to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### 4. Install cert-manager (for TLS)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 5. Install AI SRE Agent

```bash
# Validate configuration
helm lint ./ai-sre-agent -f values-production.yaml

# Dry run
helm install ai-sre-agent ./ai-sre-agent \
  --namespace ai-sre-agent \
  --create-namespace \
  -f values-production.yaml \
  --dry-run --debug

# Install
helm install ai-sre-agent ./ai-sre-agent \
  --namespace ai-sre-agent \
  --create-namespace \
  -f values-production.yaml

# Check status
helm status ai-sre-agent -n ai-sre-agent
```

---

## Post-Installation Configuration

### 1. Wait for Pods

```bash
# Watch pods
kubectl get pods -n ai-sre-agent -w

# Wait for all pods to be ready (takes 5-10 minutes)
kubectl wait --for=condition=ready pod \
  --all \
  -n ai-sre-agent \
  --timeout=600s
```

### 2. Pull Ollama Models

```bash
# Get Ollama pod name
OLLAMA_POD=$(kubectl get pods -n ai-sre-agent \
  -l app.kubernetes.io/component=ollama \
  -o jsonpath='{.items[0].metadata.name}')

echo "Ollama pod: $OLLAMA_POD"

# Pull LLM model (takes 5-10 minutes, 4.7GB download)
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull llama3.1:8b

# Pull embedding model
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull nomic-embed-text

# Verify models
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama list
```

### 3. Configure Database

```bash
# Port-forward to backend
kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000 &

# Run migrations (if implemented)
curl http://localhost:8000/admin/migrate

# Or exec into pod
BACKEND_POD=$(kubectl get pods -n ai-sre-agent \
  -l app.kubernetes.io/component=backend \
  -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it -n ai-sre-agent $BACKEND_POD -- \
  python -m alembic upgrade head
```

### 4. Create Initial Data

```bash
# Seed vector store with common runbooks
kubectl exec -it -n ai-sre-agent $BACKEND_POD -- \
  python scripts/seed_runbooks.py
```

### 5. Configure DNS

```bash
# Point your domain to the ingress IP
echo "Add this A record to your DNS:"
echo "api.yourdomain.com -> ${INGRESS_IP}"

# Verify after DNS propagates
nslookup api.yourdomain.com
```

---

## Verification

### 1. Health Checks

```bash
# All pods should be Running
kubectl get pods -n ai-sre-agent

# Check logs
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-backend
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-ollama
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-ai-engine
```

### 2. Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","timestamp":"2024-01-15T10:30:00Z"}

# Test AI endpoint
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the current cluster health?"}'
```

### 3. Test K8s Integration

```bash
# Check collector can read K8s
COLLECTOR_POD=$(kubectl get pods -n ai-sre-agent \
  -l app.kubernetes.io/component=collector \
  -o jsonpath='{.items[0].metadata.name}')

kubectl logs -n ai-sre-agent $COLLECTOR_POD

# Test executor permissions
EXECUTOR_POD=$(kubectl get pods -n ai-sre-agent \
  -l app.kubernetes.io/component=executor \
  -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n ai-sre-agent $EXECUTOR_POD -- \
  kubectl get pods -n default
```

### 4. Verify Monitoring

```bash
# Check ServiceMonitors
kubectl get servicemonitor -n ai-sre-agent

# Check metrics endpoints
kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000 &
curl http://localhost:8000/metrics
```

---

## Troubleshooting

### Ollama Out of Memory

**Symptoms**: Ollama pod crashes or restarts frequently

**Solution**:
```bash
# Increase memory limit
helm upgrade ai-sre-agent ./ai-sre-agent \
  -n ai-sre-agent \
  --set ollama.resources.limits.memory=16Gi \
  --reuse-values
```

### Cloud SQL Connection Failed

**Symptoms**: Backend can't connect to database

**Solution**:
```bash
# Check Cloud SQL Proxy
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-backend -c cloud-sql-proxy

# Verify Workload Identity binding
gcloud iam service-accounts get-iam-policy \
  backend@${PROJECT_ID}.iam.gserviceaccount.com

# Re-bind if needed
gcloud iam service-accounts add-iam-policy-binding \
  backend@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[ai-sre-agent/backend]"
```

### RBAC Permission Denied

**Symptoms**: Collector or Executor can't access K8s resources

**Solution**:
```bash
# Check ClusterRole
kubectl get clusterrole ai-sre-agent-collector -o yaml
kubectl get clusterrole ai-sre-agent-executor -o yaml

# Check bindings
kubectl get clusterrolebinding ai-sre-agent-collector -o yaml

# Reapply RBAC
helm upgrade ai-sre-agent ./ai-sre-agent \
  -n ai-sre-agent \
  --reuse-values
```

### Image Pull Errors

**Symptoms**: Pods stuck in ImagePullBackOff

**Solution**:
```bash
# Verify images exist
gcloud artifacts docker images list \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent

# Check node service account permissions
kubectl describe pod -n ai-sre-agent <pod-name>

# Grant Artifact Registry Reader to node pool SA
NODE_POOL_SA=$(gcloud container clusters describe ai-sre-cluster \
  --region=${REGION} \
  --format="value(nodeConfig.serviceAccount)")

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${NODE_POOL_SA}" \
  --role="roles/artifactregistry.reader"
```

### Ingress Not Working

**Symptoms**: Can't access via domain

**Solution**:
```bash
# Check ingress status
kubectl get ingress -n ai-sre-agent
kubectl describe ingress -n ai-sre-agent

# Check nginx controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Verify DNS
dig api.yourdomain.com +short  # Should return ingress IP
```

---

## Cleanup

### Uninstall Helm Release

```bash
# Delete release
helm uninstall ai-sre-agent -n ai-sre-agent

# Delete namespace
kubectl delete namespace ai-sre-agent
```

### Destroy Infrastructure

```bash
cd terraform

# Destroy (takes 10-15 minutes)
terraform destroy

# Confirm deletion
```

### Delete Project Resources

```bash
# Delete service account key
rm ~/terraform-key.json

# Revoke service account (optional)
gcloud iam service-accounts delete \
  terraform-deployer@${PROJECT_ID}.iam.gserviceaccount.com
```

---

## Next Steps

1. **Configure Observability**: Set up Grafana dashboards
2. **Add Runbooks**: Seed the vector store with your team's runbooks
3. **Create Users**: Set up authentication and user management
4. **Enable GitOps**: Use ArgoCD or Flux for deployments
5. **Set up Backups**: Configure Cloud SQL backups and volume snapshots

See the main [README](../README.md) for usage documentation.
