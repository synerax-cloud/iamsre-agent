# Terraform Issues and Solutions

## Issue: "storage: bucket doesn't exist"

**Error:**
```
Error: Failed to get existing workspaces: querying Cloud Storage failed: storage: bucket doesn't exist
```

**Cause:**  
Terraform is configured to use Google Cloud Storage (GCS) for remote state storage, but the bucket doesn't exist yet.

**Solution:**  
The backend configuration has been commented out in `terraform/main.tf` to use local state for initial deployment.

### For Production: Enable Remote State

If you want to use remote state (recommended for teams):

1. **Create the GCS bucket:**
   ```bash
   export PROJECT_ID="your-project-id"
   
   gcloud storage buckets create \
     gs://ai-sre-agent-terraform-state-${PROJECT_ID} \
     --location=us-central1 \
     --uniform-bucket-level-access
   
   # Enable versioning
   gcloud storage buckets update \
     gs://ai-sre-agent-terraform-state-${PROJECT_ID} \
     --versioning
   ```

2. **Update terraform/main.tf:**
   ```hcl
   terraform {
     backend "gcs" {
       bucket = "ai-sre-agent-terraform-state-YOUR_PROJECT_ID"
       prefix = "terraform/state"
     }
   }
   ```

3. **Migrate existing state:**
   ```bash
   cd terraform
   terraform init -migrate-state
   ```

---

## Using Local State (Current Configuration)

**Pros:**
- ✅ No additional setup required
- ✅ No extra costs
- ✅ Works immediately

**Cons:**
- ⚠️ State file stored locally (not shared with team)
- ⚠️ Must backup `terraform.tfstate` manually
- ⚠️ Risk of losing state if file deleted

**Backup your state:**
```bash
# After each terraform apply
cp terraform/terraform.tfstate terraform/terraform.tfstate.backup
```

---

## Migration Path

When ready to move to production with remote state:

1. Create GCS bucket (see above)
2. Uncomment backend block in `main.tf`
3. Run `terraform init -migrate-state`
4. Confirm migration
5. Delete local `terraform.tfstate` (it's now in GCS)

---

## Other Common Terraform Errors

### Error: "The given value is not valid for variable project_id"

**Fix:**
```bash
cd terraform
# Make sure terraform.tfvars exists with your project_id
echo 'project_id = "your-project-id"' >> terraform.tfvars
```

### Error: "Error creating Network: googleapi: Error 403"

**Fix:** Enable required APIs:
```bash
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable servicenetworking.googleapis.com
```

### State Lock Errors

**Fix:**
```bash
cd terraform
terraform force-unlock <LOCK_ID>
```

---

## Clean Start

If you need to completely start over:

```bash
cd terraform

# Remove all local state
rm -rf .terraform .terraform.lock.hcl terraform.tfstate*

# Re-initialize
terraform init

# Plan and apply
terraform plan -out=tfplan
terraform apply tfplan
```
