# AI SRE Agent Helm Chart

This Helm chart deploys the AI-Powered Kubernetes SRE Agent on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PV provisioner support in the underlying infrastructure
- GKE cluster with Workload Identity (for GCP deployment)

## Installation

### Quick Start

```bash
# Add repository (if published)
helm repo add ai-sre https://charts.example.com
helm repo update

# Install with default values
helm install ai-sre-agent ai-sre/ai-sre-agent \
  --namespace ai-sre-agent \
  --create-namespace

# Or install from local chart
cd helm/ai-sre-agent
helm install ai-sre-agent . \
  --namespace ai-sre-agent \
  --create-namespace
```

### Production Installation on GKE

```bash
helm upgrade --install ai-sre-agent ./helm/ai-sre-agent \
  --namespace ai-sre-agent \
  --create-namespace \
  --set global.projectId=YOUR_PROJECT_ID \
  --set global.region=us-central1 \
  --set global.ingressIP=YOUR_STATIC_IP \
  --set backend.image.repository=us-central1-docker.pkg.dev/YOUR_PROJECT/ai-sre-agent/backend \
  --set aiEngine.image.repository=us-central1-docker.pkg.dev/YOUR_PROJECT/ai-sre-agent/ai-engine \
  --set collector.image.repository=us-central1-docker.pkg.dev/YOUR_PROJECT/ai-sre-agent/collector \
  --set executor.image.repository=us-central1-docker.pkg.dev/YOUR_PROJECT/ai-sre-agent/executor \
  --set backend.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"=BACKEND_SA@PROJECT.iam.gserviceaccount.com \
  --set aiEngine.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"=AI_ENGINE_SA@PROJECT.iam.gserviceaccount.com \
  --set collector.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"=COLLECTOR_SA@PROJECT.iam.gserviceaccount.com \
  --set executor.serviceAccount.annotations."iam\.gke\.io/gcp-service-account"=EXECUTOR_SA@PROJECT.iam.gserviceaccount.com
```

### Using a values file

Create a `values-prod.yaml` file:

```yaml
global:
  projectId: my-project-123
  region: us-central1
  ingressIP: 34.123.456.789

backend:
  image:
    repository: us-central1-docker.pkg.dev/my-project/ai-sre-agent/backend
    tag: v1.0.0
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: backend@my-project.iam.gserviceaccount.com

# ... other overrides
```

Install with values file:

```bash
helm install ai-sre-agent ./helm/ai-sre-agent \
  --namespace ai-sre-agent \
  --create-namespace \
  -f values-prod.yaml
```

## Configuration

The following table lists the configurable parameters and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.projectId` | GCP Project ID | `""` |
| `global.region` | GCP Region | `us-central1` |
| `global.ingressIP` | Static IP for Ingress | `""` |

### Backend Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.enabled` | Enable backend service | `true` |
| `backend.replicaCount` | Number of replicas | `2` |
| `backend.image.repository` | Image repository | `""` |
| `backend.image.tag` | Image tag | `latest` |
| `backend.resources.requests.cpu` | CPU request | `250m` |
| `backend.resources.requests.memory` | Memory request | `512Mi` |
| `backend.autoscaling.enabled` | Enable HPA | `true` |
| `backend.autoscaling.minReplicas` | Min replicas | `2` |
| `backend.autoscaling.maxReplicas` | Max replicas | `10` |

### Ollama Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ollama.enabled` | Enable Ollama | `true` |
| `ollama.replicaCount` | Number of replicas | `1` |
| `ollama.resources.requests.cpu` | CPU request | `1000m` |
| `ollama.resources.requests.memory` | Memory request | `4Gi` |
| `ollama.persistence.enabled` | Enable persistent storage | `true` |
| `ollama.persistence.size` | Storage size | `50Gi` |

See [values.yaml](values.yaml) for all configuration options.

## Post-Installation

### 1. Pull Ollama Models

After installation, pull the required Ollama models:

```bash
# Get Ollama pod name
OLLAMA_POD=$(kubectl get pods -n ai-sre-agent -l app.kubernetes.io/component=ollama -o jsonpath='{.items[0].metadata.name}')

# Pull models
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull llama3.1:8b
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull nomic-embed-text
```

### 2. Verify Installation

```bash
# Check all pods are running
kubectl get pods -n ai-sre-agent

# Check services
kubectl get svc -n ai-sre-agent

# Test backend health
kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000
curl http://localhost:8000/health
```

### 3. Access the API

```bash
# Via port-forward (development)
kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000

# Via Ingress (production)
curl https://api.yourdomain.com/health
```

## Upgrading

```bash
helm upgrade ai-sre-agent ./helm/ai-sre-agent \
  --namespace ai-sre-agent \
  -f values-prod.yaml
```

## Uninstallation

```bash
# Delete the release
helm uninstall ai-sre-agent --namespace ai-sre-agent

# Delete the namespace (optional)
kubectl delete namespace ai-sre-agent

# Delete PVCs (optional, if you want to remove data)
kubectl delete pvc -n ai-sre-agent --all
```

## Troubleshooting

### Ollama Models Not Loading

```bash
# Check Ollama logs
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-ollama

# Manually pull models
kubectl exec -it -n ai-sre-agent deployment/ai-sre-agent-ollama -- ollama pull llama3.1:8b
```

### Backend Can't Connect to Database

```bash
# Check CloudSQL Proxy logs (if using GCP)
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-backend -c cloud-sql-proxy

# Verify connection string
kubectl get cm -n ai-sre-agent ai-sre-agent-backend-config -o yaml
```

### Executor Permission Issues

```bash
# Check RBAC
kubectl get clusterrole ai-sre-agent-executor -o yaml
kubectl describe clusterrolebinding ai-sre-agent-executor

# Check service account
kubectl get sa -n ai-sre-agent
```

## License

Copyright (c) 2026. See LICENSE file for details.
