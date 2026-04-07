# Secret Management

## Overview

All secrets are automatically managed using **Google Secret Manager** (GSM) with secure auto-generation.

## Secrets in This Project

### 1. Database Password
- **Name**: `{cluster_name}-db-password`
- **Generation**: Auto-generated 32-character random password
- **Storage**: Google Secret Manager
- **Access**: Backend and AI Engine service accounts

### 2. JWT Secret
- **Name**: `{cluster_name}-jwt-secret`
- **Generation**: Auto-generated 64-character secure random string
- **Storage**: Google Secret Manager
- **Access**: Backend service account
- **Usage**: JWT token signing for API authentication

### 3. OpenAI API Key (Optional)
- **Name**: `{cluster_name}-openai-api-key`
- **Generation**: Manual (if using OpenAI instead of Ollama)
- **Storage**: Google Secret Manager (if provided)
- **Access**: AI Engine service account

## How It Works

### Auto-Generation
Terraform automatically generates secure secrets using the `random_password` provider:

```hcl
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}
```

### Storage in GSM
Secrets are stored in Google Secret Manager:

```hcl
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "ai-sre-cluster-jwt-secret"
  
  replication {
    auto {}  # Auto-replication across regions
  }
}
```

### Access Control
Service accounts are granted access via IAM:

```hcl
resource "google_secret_manager_secret_iam_member" "backend_jwt" {
  secret_id = google_secret_manager_secret.jwt_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:backend@project.iam.gserviceaccount.com"
}
```

## Accessing Secrets

### From Terraform Outputs
```bash
cd terraform

# View secret names (not values)
terraform output secrets

# Output:
# {
#   "db_password": "ai-sre-cluster-db-password"
#   "jwt_secret": "ai-sre-cluster-jwt-secret"
# }
```

### From gcloud CLI
```bash
# List all secrets
gcloud secrets list

# View specific secret value (requires permissions)
gcloud secrets versions access latest --secret="ai-sre-cluster-jwt-secret"

# View secret metadata
gcloud secrets describe ai-sre-cluster-jwt-secret
```

### From Kubernetes Pods
Secrets are accessed via Workload Identity:

```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
response = client.access_secret_version(request={"name": name})
secret_value = response.payload.data.decode("UTF-8")
```

## Rotating Secrets

### Rotate JWT Secret
```bash
# Generate new secret
NEW_SECRET=$(openssl rand -base64 48)

# Add new version
gcloud secrets versions add ai-sre-cluster-jwt-secret \
  --data-file=<(echo -n "$NEW_SECRET")

# Restart backend pods to pick up new secret
kubectl rollout restart deployment/ai-sre-agent-backend -n ai-sre-agent
```

### Rotate Database Password
```bash
# Update in Cloud SQL
gcloud sql users set-password postgres \
  --instance=ai-sre-db \
  --password=NEW_PASSWORD

# Update in Secret Manager
gcloud secrets versions add ai-sre-cluster-db-password \
  --data-file=<(echo -n "NEW_PASSWORD")

# Restart backend
kubectl rollout restart deployment/ai-sre-agent-backend -n ai-sre-agent
```

## Security Best Practices

### ✅ Enabled
- [x] Automatic secret rotation support
- [x] Secret versioning (keep previous 10 versions)
- [x] IAM-based access control
- [x] Workload Identity for pod access
- [x] Secrets never in Terraform state (using random provider)
- [x] Regional replication for HA

### 🔒 Recommendations
1. **Enable Secret Manager audit logs**:
   ```bash
   gcloud logging sinks create secret-audit-log \
     storage.googleapis.com/security-logs-bucket \
     --log-filter='resource.type="secretmanager.googleapis.com/Secret"'
   ```

2. **Set up automatic rotation**:
   - Schedule Cloud Function to rotate secrets monthly
   - Use Secret Manager rotation with Cloud Scheduler

3. **Backup secrets** (encrypted):
   ```bash
   # Export all secrets (encrypted)
   for secret in $(gcloud secrets list --format="value(name)"); do
     gcloud secrets versions access latest --secret="$secret" | \
       gpg -c > "backup-${secret}.gpg"
   done
   ```

## Troubleshooting

### Error: "Permission denied accessing secret"

**Fix**: Grant service account access:
```bash
gcloud secrets add-iam-policy-binding ai-sre-cluster-jwt-secret \
  --member="serviceAccount:backend@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Error: "Secret not found"

**Check if secret exists**:
```bash
gcloud secrets list | grep jwt-secret
```

**Create manually if needed**:
```bash
echo -n "your-secret-value" | gcloud secrets create ai-sre-cluster-jwt-secret --data-file=-
```

### View Secret Access Logs
```bash
gcloud logging read 'resource.type="secretmanager.googleapis.com/Secret"' \
  --limit=50 \
  --format=json
```

## Environment Variables

Secrets are exposed to pods as environment variables via ConfigMaps referencing GSM:

```yaml
env:
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: backend-secrets
        key: jwt_secret
```

## Cost

Google Secret Manager pricing (as of 2026):
- **Storage**: $0.06 per secret per month
- **Access**: $0.03 per 10,000 accesses
- **Versions**: First 6 versions free, then $0.06/version/month

**Estimated cost for this project**: ~$0.50/month
