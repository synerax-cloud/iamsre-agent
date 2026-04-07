# AI-Powered Kubernetes SRE Agent

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Kubernetes](https://img.shields.io/badge/kubernetes-1.24+-326CE5?logo=kubernetes)
![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python)
![Terraform](https://img.shields.io/badge/terraform-1.5+-7B42BC?logo=terraform)

A self-hosted, AI-powered Kubernetes SRE agent that provides intelligent cluster management, automated incident response, and AI-driven recommendations using LLMs and RAG.

[Architecture](#architecture) •
[Features](#features) •
[Quick Start](#quick-start) •
[Deployment](#deployment) •
[API Documentation](#api-documentation)

</div>

---

## 🚀 Overview

The AI-Powered Kubernetes SRE Agent is a production-ready system designed to assist Site Reliability Engineers in managing Kubernetes clusters. It combines observability, AI reasoning, and automated action execution to provide intelligent cluster management.

### Key Capabilities

- **AI-Powered Reasoning**: Uses Ollama (self-hosted LLM) with RAG for context-aware decision making
- **Cluster Observability**: Real-time metrics collection from Kubernetes API and Prometheus
- **Automated Actions**: Safe execution of common SRE tasks (pod restarts, scaling, rollbacks)
- **Incident Analysis**: AI-powered incident detection and resolution recommendations
- **Chat Interface**: Natural language interaction with your cluster
- **Audit Trail**: Complete logging of all actions and decisions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway (Backend)                    │
│                    FastAPI (Port 8000)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Chat API    │  │  Status API  │  │  Execute API │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   AI Engine     │  │   Collector     │  │    Executor     │
│  (Port 8001)    │  │  (Port 8002)    │  │  (Port 8003)    │
│                 │  │                 │  │                 │
│  • RAG Pipeline │  │  • K8s Metrics  │  │  • Pod Actions  │
│  • LLM Client   │  │  • Prometheus   │  │  • Scale/Restart│
│  • Vector Store │  │  • Events       │  │  • Rollbacks    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     Ollama      │  │  Kubernetes API │  │  Kubernetes API │
│  (Port 11434)   │  │                 │  │  (Write Access) │
│                 │  │  • Read Metrics │  │                 │
│  • llama3.1:8b  │  │  • Watch Events │  │  • Modify Pods  │
│  • Embeddings   │  │  • Query Logs   │  │  • Update Deps  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│  (Cloud SQL)    │
│                 │
│  • Incidents    │
│  • Actions      │
│  • Chat History │
└─────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams.

---

## ✨ Features

### 🤖 AI-Powered Intelligence

- **Self-Hosted LLM**: Uses Ollama with llama3.1:8b (no external API calls)
- **RAG Pipeline**: Context-aware responses using FAISS vector store
- **Incident Analysis**: Automatic pattern detection and recommendation
- **Natural Language**: Chat with your cluster in plain English

### 📊 Comprehensive Observability

- **Kubernetes Metrics**: Pod health, deployment status, node resources
- **Prometheus Integration**: Custom metrics and alerts
- **Event Monitoring**: Real-time Kubernetes event watching
- **Log Aggregation**: Centralized logging from all components

### ⚡ Automated Actions

- **Pod Management**: Restart, delete, drain nodes
- **Scaling**: Horizontal scaling of deployments
- **Rollbacks**: Automatic rollback to previous versions
- **ConfigMap Updates**: Dynamic configuration changes
- **Safety Mechanisms**: Approval workflows and audit logging

### 🔒 Security & Compliance

- **Workload Identity**: GCP service account integration
- **RBAC**: Fine-grained Kubernetes permissions
- **Audit Logs**: Complete action history
- **Secrets Management**: Google Secret Manager integration
- **JWT Authentication**: Secure API access

---

## 🚀 Quick Start

### Prerequisites

- **GCP Account** with billing enabled
- **gcloud CLI** ([Install](https://cloud.google.com/sdk/docs/install))
- **Terraform** 1.5+ ([Install](https://developer.hashicorp.com/terraform/downloads))
- **kubectl** ([Install](https://kubernetes.io/docs/tasks/tools/))
- **Helm** 3.8+ ([Install](https://helm.sh/docs/intro/install/))
- **Docker** (for building images)

### 1. Clone the Repository

```bash
git clone https://github.com/synerax-cloud/iamsre-agent.git
cd iamsre-agent
```

### 2. Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "your-gcp-project-id"
region     = "us-central1"
cluster_name = "ai-sre-cluster"
environment  = "production"
EOF

# Review the plan
terraform plan

# Deploy infrastructure (takes ~15 minutes)
terraform apply
```

This creates:
- GKE cluster with 3 node pools
- Cloud SQL (PostgreSQL) instance
- VPC network with Cloud NAT
- Service accounts with Workload Identity
- Secret Manager for credentials
- Static IP for ingress

### 3. Build and Push Docker Images

```bash
# Configure Docker for GCR
gcloud auth configure-docker us-central1-docker.pkg.dev

# Set your project ID
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1

# Build and push all images
cd ../backend
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/backend:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/backend:latest

cd ../ai-engine
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/ai-engine:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/ai-engine:latest

cd ../collector
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/collector:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/collector:latest

cd ../executor
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/executor:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-sre-agent/executor:latest
```

### 4. Configure kubectl

```bash
# Get cluster credentials
gcloud container clusters get-credentials ai-sre-cluster \
  --region us-central1 \
  --project your-gcp-project-id
```

### 5. Deploy with Helm

```bash
cd ../helm

# Create values-prod.yaml with your configuration
cat > values-prod.yaml <<EOF
global:
  projectId: your-gcp-project-id
  region: us-central1
  ingressIP: $(terraform output -raw ingress_ip)

backend:
  image:
    repository: us-central1-docker.pkg.dev/your-gcp-project-id/ai-sre-agent/backend
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: backend@your-gcp-project-id.iam.gserviceaccount.com

aiEngine:
  image:
    repository: us-central1-docker.pkg.dev/your-gcp-project-id/ai-sre-agent/ai-engine
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: ai-engine@your-gcp-project-id.iam.gserviceaccount.com

collector:
  image:
    repository: us-central1-docker.pkg.dev/your-gcp-project-id/ai-sre-agent/collector
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: collector@your-gcp-project-id.iam.gserviceaccount.com

executor:
  image:
    repository: us-central1-docker.pkg.dev/your-gcp-project-id/ai-sre-agent/executor
    tag: latest
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: executor@your-gcp-project-id.iam.gserviceaccount.com
EOF

# Install the chart
helm install ai-sre-agent ./ai-sre-agent \
  --namespace ai-sre-agent \
  --create-namespace \
  -f values-prod.yaml
```

### 6. Pull Ollama Models

```bash
# Get Ollama pod name
OLLAMA_POD=$(kubectl get pods -n ai-sre-agent -l app.kubernetes.io/component=ollama -o jsonpath='{.items[0].metadata.name}')

# Pull models (takes 5-10 minutes)
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull llama3.1:8b
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama pull nomic-embed-text

# Verify models
kubectl exec -n ai-sre-agent $OLLAMA_POD -- ollama list
```

### 7. Test the Deployment

```bash
# Check all pods are running
kubectl get pods -n ai-sre-agent

# Port-forward to backend
kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Test AI chat (example)
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the health of my cluster?"}'
```

---

## 📦 Project Structure

```
kubernetes-agent/
├── backend/                 # API Gateway (FastAPI)
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security, LLM client
│   │   ├── db/             # Database models
│   │   └── schemas/        # Pydantic schemas
│   ├── Dockerfile
│   └── requirements.txt
├── ai-engine/              # AI Reasoning Engine
│   ├── app/
│   │   ├── rag/            # RAG pipeline, vector store
│   │   └── core/           # LLM client
│   └── Dockerfile
├── collector/              # Observability Collector
│   ├── app/
│   │   └── collectors/     # K8s and Prometheus clients
│   └── Dockerfile
├── executor/               # Action Executor
│   ├── app/
│   │   ├── k8s/            # Kubernetes client
│   │   └── core/           # Audit logging
│   └── Dockerfile
├── terraform/              # Infrastructure as Code
│   ├── main.tf
│   ├── modules/            # VPC, GKE, Cloud SQL, IAM
│   └── variables.tf
├── helm/                   # Kubernetes deployments
│   └── ai-sre-agent/
│       ├── templates/      # K8s manifests
│       └── values.yaml
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   └── OLLAMA.md
└── scripts/                # Helper scripts
    └── setup-ollama-models.sh
```

---

## 🔧 Configuration

### Environment Variables

All services use environment variables for configuration. See `.env.example` files in each service directory.

**Backend:**
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
JWT_SECRET_KEY=your-secret-key
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
AI_ENGINE_URL=http://ai-engine:8001
COLLECTOR_URL=http://collector:8002
EXECUTOR_URL=http://executor:8003
```

**AI Engine:**
```env
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
VECTOR_STORE_PATH=/data/vector_store
```

**Collector:**
```env
PROMETHEUS_URL=http://prometheus:9090
KUBERNETES_IN_CLUSTER=true
```

**Executor:**
```env
KUBERNETES_IN_CLUSTER=true
AUDIT_LOG_ENABLED=true
```

### Helm Values

See [helm/ai-sre-agent/values.yaml](helm/ai-sre-agent/values.yaml) for all configuration options.

---

## 📚 API Documentation

### Backend API (Port 8000)

#### Health Endpoints
- `GET /health` - Overall health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

#### Chat API
```bash
POST /api/v1/ask
{
  "question": "What pods are failing in the production namespace?",
  "context": "optional context"
}
```

#### Cluster Status
```bash
GET /api/v1/status?namespace=default
```

#### Execute Actions
```bash
POST /api/v1/execute
{
  "action_type": "restart_deployment",
  "params": {
    "namespace": "production",
    "deployment": "backend"
  }
}
```

### AI Engine API (Port 8001)

- `POST /api/v1/query` - RAG query with context
- `POST /api/v1/analyze` - Analyze incidents
- `POST /api/v1/recommend` - Get recommendations

### Access via Ingress

Production deployments use Nginx Ingress:

```bash
# Chat
curl -X POST https://api.yourdomain.com/api/v1/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me unhealthy pods"}'

# Cluster Status
curl https://api.yourdomain.com/api/v1/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Local Development

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Pull Ollama models
docker exec ai-sre-ollama ollama pull llama3.1:8b
docker exec ai-sre-ollama ollama pull nomic-embed-text

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

Services available at:
- Backend: http://localhost:8000
- AI Engine: http://localhost:8001
- Collector: http://localhost:8002
- Executor: http://localhost:8003
- Ollama: http://localhost:11434
- PostgreSQL: localhost:5432

---

## 🔐 Security

### Authentication

The system uses JWT tokens for authentication:

```python
# Generate token
from app.core.security import create_access_token

token = create_access_token(data={"sub": "user@example.com"})
```

### RBAC Permissions

**Collector Service** (Read-only):
- Get/List/Watch: Pods, Nodes, Deployments, Events, Services

**Executor Service** (Write):
- Get/List/Patch/Delete: Pods, Deployments, ConfigMaps, Secrets

### Workload Identity

GCP service accounts are bound to Kubernetes service accounts:

```bash
# Example binding
gcloud iam service-accounts add-iam-policy-binding \
  backend@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[ai-sre-agent/backend]"
```

---

## 📊 Monitoring

### Prometheus Metrics

All services expose metrics at `/metrics`:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `llm_requests_total` - LLM API calls
- `k8s_actions_total` - Kubernetes actions executed

### Grafana Dashboards

Import the provided dashboards from `monitoring/grafana/`:

1. Cluster Overview
2. AI Engine Performance
3. Action Execution Audit
4. LLM Usage Statistics

---

## 🚧 Troubleshooting

### Ollama Fails to Start

```bash
# Check logs
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-ollama

# Verify PVC
kubectl get pvc -n ai-sre-agent

# Check resource limits
kubectl describe pod -n ai-sre-agent -l app.kubernetes.io/component=ollama
```

### Backend Can't Connect to Database

```bash
# Verify Cloud SQL Proxy (if using GCP)
kubectl logs -n ai-sre-agent deployment/ai-sre-agent-backend -c cloud-sql-proxy

# Check secrets
kubectl get secret -n ai-sre-agent

# Test connection
kubectl exec -it -n ai-sre-agent deployment/ai-sre-agent-backend -- \
  python -c "from app.db.database import engine; print(engine)"
```

### Permission Denied Errors

```bash
# Check RBAC
kubectl get clusterrole ai-sre-agent-executor -o yaml
kubectl describe clusterrolebinding ai-sre-agent-executor

# Verify service account
kubectl get sa -n ai-sre-agent ai-sre-agent-executor -o yaml
```

### High Memory Usage

```bash
# Check resource usage
kubectl top pods -n ai-sre-agent

# Increase Ollama memory limit
helm upgrade ai-sre-agent ./helm/ai-sre-agent \
  --namespace ai-sre-agent \
  --set ollama.resources.limits.memory=16Gi \
  --reuse-values
```

---

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# AI Engine tests
cd ai-engine
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint
pylint app/
mypy app/
```

### Adding New Actions

1. Add action to [executor/app/k8s/client.py](executor/app/k8s/client.py)
2. Add endpoint to [executor/app/api/v1/actions.py](executor/app/api/v1/actions.py)
3. Update RBAC rules in [helm values](helm/ai-sre-agent/values.yaml)
4. Add tests

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/synerax-cloud/iamsre-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/synerax-cloud/iamsre-agent/discussions)
- **Documentation**: [docs/](docs/)

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Self-hosted LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)

---

<div align="center">

**[⬆ back to top](#ai-powered-kubernetes-sre-agent)**

Made with ❤️ by SREs, for SREs

</div>
