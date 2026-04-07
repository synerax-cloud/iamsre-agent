# Deployment Checklist

## ✅ Completed
- [x] All code implemented (middleware, API endpoints, configuration)
- [x] Cloud Build configuration created (no Docker needed!)
- [x] Automated deployment script ready
- [x] Pushed to GitHub: https://github.com/synerax-cloud/iamsre-agent

## 📋 Deployment Steps (Run these now)

### Step 1: Verify Prerequisites
```bash
# Check gcloud is installed and authenticated
gcloud auth list
gcloud projects list

# Check terraform
terraform version  # Should be 1.5+

# Check helm
helm version  # Should be 3.8+
```

### Step 2: Run Automated Deployment

**Option A: Automated (Recommended)**
```bash
cd /Users/shubham/Kubernetes-agent
./scripts/deploy-gke.sh
```

The script will prompt you for:
- GCP Project ID
- Region (default: us-central1)
- Image Version (default: v1.0.0)

Then it automatically:
1. Deploys Terraform infrastructure (~15 min)
2. Builds Docker images with Cloud Build (~8-10 min)
3. Deploys with Helm (~5 min)
4. Pulls Ollama models (~5-10 min)

**Total Time: ~30-40 minutes**

**Option B: Manual (Step-by-Step)**

See [QUICKSTART.md](QUICKSTART.md) for detailed manual steps.

### Step 3: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n ai-sre-agent

# All should be Running/Ready:
# - ai-sre-agent-backend
# - ai-sre-agent-ai-engine
# - ai-sre-agent-collector
# - ai-sre-agent-executor
# - ai-sre-agent-ollama

# Port-forward and test
kubectl port-forward -n ai-sre-agent svc/ai-sre-agent-backend 8000:8000

# In another terminal:
curl http://localhost:8000/health
```

### Step 4: Test Functionality

```bash
# Test cluster status
curl http://localhost:8000/api/v1/status/cluster

# Test AI chat (POST request)
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the current cluster health?"}'
```

---

## 💰 Cost Management (Free Tier)

### GCP Free Tier Limits
- **Cloud Build**: 120 build-minutes/day (FREE)
- **GKE**: $74.40/month for cluster (use preemptible nodes to reduce)
- **Cloud SQL**: ~$15-25/month for db-g1-small
- **Compute**: First $300 credit (new accounts)

### Cost Optimization Tips

1. **Use Spot Instances** (already configured in Terraform)
2. **Scale down when not using**:
   ```bash
   kubectl scale deployment --all --replicas=0 -n ai-sre-agent
   ```

3. **Delete when done testing**:
   ```bash
   helm uninstall ai-sre-agent -n ai-sre-agent
   cd terraform && terraform destroy
   ```

4. **Use smaller machines** (edit terraform/terraform.tfvars):
   ```hcl
   node_pool_machine_type = "e2-medium"  # Smaller/cheaper
   ai_node_pool_machine_type = "n1-standard-4"  # For Ollama
   db_instance_tier = "db-f1-micro"  # Smallest DB
   ```

---

## 🔍 Monitoring Costs

```bash
# Check current costs
gcloud billing accounts list
gcloud alpha billing budgets list

# View resource usage
kubectl top nodes
kubectl top pods -n ai-sre-agent
```

---

## 🚨 Troubleshooting

### Cloud Build Permission Denied
```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Grant Cloud Build service account permissions
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/container.developer
```

### Terraform State Lock
```bash
cd terraform
terraform force-unlock <LOCK_ID>
```

### Ollama OOM (Out of Memory)
```bash
# Increase memory limit
helm upgrade ai-sre-agent ./helm/ai-sre-agent \
  -n ai-sre-agent \
  --set ollama.resources.limits.memory=16Gi \
  --reuse-values
```

---

## 📚 Next Steps After Deployment

1. **Configure DNS** - Point domain to ingress IP
2. **Add TLS Certificates** - Use cert-manager
3. **Set Up Monitoring** - Import Grafana dashboards
4. **Add Runbooks** - Seed vector store with your documentation
5. **Enable Authentication** - Configure JWT properly

---

## 📞 Need Help?

- Check logs: `kubectl logs -n ai-sre-agent deployment/ai-sre-agent-backend -f`
- See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed troubleshooting
- GitHub Issues: https://github.com/synerax-cloud/iamsre-agent/issues

---

## ✅ Checklist Summary

- [ ] Run `./scripts/deploy-gke.sh`
- [ ] Wait for deployment (~30-40 min)
- [ ] Verify pods are running
- [ ] Test health endpoint
- [ ] Test AI chat endpoint
- [ ] Monitor costs in GCP Console
- [ ] Scale down or destroy when done testing

**Ready to deploy? Run:** `./scripts/deploy-gke.sh`
