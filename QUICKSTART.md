# Quick Start - Deploy to GKE

This guide gets your AI SRE Agent running on GKE in ~30 minutes without local Docker.

## Prerequisites

✅ GCP account with billing enabled  
✅ gcloud CLI installed ([Install](https://cloud.google.com/sdk/docs/install))  
✅ Terraform 1.5+ installed ([Install](https://developer.hashicorp.com/terraform/downloads))  
✅ kubectl installed (via `gcloud components install kubectl`)  
✅ Helm 3.8+ installed ([Install](https://helm.sh/docs/intro/install))  

## One-Command Deployment

We provide an automated deployment script that handles everything:

```bash
# Make sure you're in the project root
cd /path/to/iamsre-agent

# Run the deployment script
./scripts/deploy-gke.sh
```

The script will:
1. ✅ Create GKE cluster and infrastructure (Terraform)
2. ✅ Build Docker images using Cloud Build (no local Docker needed!)
3. ✅ Deploy with Helm
4. ✅ Pull Ollama models
5. ✅ Verify deployment

**Time:** ~20-30 minutes  
**Cost:** Free tier eligible (first $300 credit + always-free tier)

---

## Manual Step-by-Step Deployment

If you prefer to deploy manually or need more control:

### 1. Set up GCP Project

```bash
# Login and set project
gcloud auth login
gcloud auth application-default login

export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Deploy Infrastructure with Terraform

```bash
cd terraform

# Create configuration
cat > terraform.tfvars <<EOF
project_id   = "YOUR_PROJECT_ID"
region       = "us-central1"
cluster_name = "ai-sre-cluster"
environment  = "production"
EOF

# Initialize and apply
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Save outputs
terraform output -json > outputs.json
```

**Time:** ~15 minutes  
**Creates:** GKE cluster, Cloud SQL, VPC, IAM, Secret Manager

### 3. Build Images with Cloud Build

**No Docker required!** Google Cloud Build does it for you:

```bash
cd ..  # back to project root

# Build all images
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION=us-central1,_VERSION=v1.0.0
```

**Time:** ~8-10 minutes  
**Free Tier:** 120 build-minutes/day included  
**Builds:** 4 Docker images (backend, ai-engine, collector, executor)

### 4. Configure kubectl

```bash
gcloud container clusters get-credentials ai-sre-cluster \
  --region us-central1 \
  --project YOUR_PROJECT_ID
```

### 5. Install Prerequisites

```bash
# Get static IP from Terraform
INGRESS_IP=$(cd terraform && terraform output -raw ingress_ip)

# Install Nginx Ingress
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.loadBalancerIP=${INGRESS_IP} \
  --wait
```

### 6. Deploy AI SRE Agent

```bash
cd helm

# Get Terraform outputs
PROJECT_ID="your-project-id"
REGION="us-central1"
VERSION="v1.0.0"
INGRESS_IP=$(cd ../terraform && terraform output -raw ingress_ip)
DB_CONNECTION=$(cd ../terraform && terraform output -raw database_connection_name)

# Create production values
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

# Install
helm install ai-sre-agent ./ai-sre-agent \
  --namespace ai-sre-agent \
  --create-namespace \
  -f values-prod.yaml \
  --wait
```

### 7. Pull Ollama Models

```bash
# Wait for Ollama pod to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/component=ollama \
  -n ai-sre-agent \
  --timeout=600s

# Get pod name
OLLAMA_POD=$(kubectl get pods -n ai-sre-agent \
  -l app.kubernetes.io/component=ollama \
  -o jsonpath='{.items[0].metadata.name}')

# Pull models (takes 5-10 minutes)
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull llama3.1:8b
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull nomic-embed-text
```

---

## Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n ai-sre-agent

# Expected output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# ai-sre-agent-backend-xxx                1/1     Running   0          2m
# ai-sre-agent-ai-engine-xxx              1/1     Running   0          2m
# ai-sre-agent-collector-xxx              1/1     Running   0          2m
# ai-sre-agent-executor-xxx               1/1     Running   0          2m
# ai-sre-agent-ollama-xxx                 1/1     Running   0          2m

# Port-forward and test
kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000

# In another terminal
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"ai-sre-backend","version":"1.0.0"}

# Test cluster status
curl http://localhost:8000/api/v1/status/cluster
```

---

## Cost Optimization (Free Tier)

Keep within GCP free tier limits:

### 1. Use Minimal Resources
```bash
# Edit helm/ai-sre-agent/values.yaml
# Reduce resources:
ollama:
  resources:
    requests:
      cpu: 1000m
      memory: 4Gi
```

### 2. Use Spot Instances
Already configured in Terraform for AI workloads!

### 3. Stop When Not Using
```bash
# Scale down to save costs
kubectl scale deployment --all --replicas=0 -n ai-sre-agent

# Scale back up
kubectl scale deployment --all --replicas=1 -n ai-sre-agent
```

### 4. Delete Resources
```bash
# Helm uninstall
helm uninstall ai-sre-agent -n ai-sre-agent

# Terraform destroy
cd terraform
terraform destroy
```

---

## Troubleshooting

### Image Pull Errors
```bash
# Verify images exist
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/$PROJECT_ID/ai-sre-agent

# Check node pool has permissions
kubectl describe pod -n ai-sre-agent <pod-name>
```

### Ollama Out of Memory
```bash
# Increase memory
helm upgrade ai-sre-agent ./helm/ai-sre-agent \
  -n ai-sre-agent \
  --set ollama.resources.limits.memory=8Gi \
  --reuse-values
```

### Cloud SQL Connection Failed
```bash
# Check Workload Identity binding
gcloud iam service-accounts get-iam-policy \
  backend@${PROJECT_ID}.iam.gserviceaccount.com
```

---

## Next Steps

1. **Configure DNS** - Point your domain to `$INGRESS_IP`
2. **Add TLS** - Use cert-manager for Let's Encrypt certificates
3. **Set up Monitoring** - Import Grafana dashboards
4. **Seed Knowledge** - Add your runbooks to the vector store
5. **Test AI Features** - Try asking questions about your cluster

See [README.md](../README.md) for full documentation.

---

## Quick Reference

```bash
# View logs
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-backend -f

# Restart a service
kubectl rollout restart deployment/ai-sre-agent-backend -n ai-sre-agent

# Get ingress IP
kubectl get svc -n ingress-nginx

# Update configuration
helm upgrade ai-sre-agent ./helm/ai-sre-agent \
  -n ai-sre-agent \
  -f values-prod.yaml
```
