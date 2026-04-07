# Makefile for AI SRE Agent Terraform Infrastructure
# Simplifies common Terraform operations

.PHONY: help init plan apply destroy validate format clean output

# Default target
help:
	@echo "AI SRE Agent Terraform - Available Commands:"
	@echo ""
	@echo "  make init        - Initialize Terraform"
	@echo "  make validate    - Validate Terraform configuration"
	@echo "  make format      - Format Terraform files"
	@echo "  make plan        - Create execution plan"
	@echo "  make apply       - Apply infrastructure changes"
	@echo "  make destroy     - Destroy infrastructure (be careful!)"
	@echo "  make output      - Show Terraform outputs"
	@echo "  make clean       - Clean Terraform files"
	@echo "  make kubeconfig  - Configure kubectl"
	@echo "  make push-images - Show Docker push commands"
	@echo "  make deploy-helm - Show Helm deployment commands"
	@echo ""

# Initialize Terraform
init:
	@echo "Initializing Terraform..."
	terraform init -upgrade

# Validate configuration
validate:
	@echo "Validating Terraform configuration..."
	terraform validate
	terraform fmt -check -recursive

# Format Terraform files
format:
	@echo "Formatting Terraform files..."
	terraform fmt -recursive

# Create execution plan
plan:
	@echo "Creating execution plan..."
	terraform plan -out=tfplan

# Apply changes
apply:
	@echo "Applying infrastructure changes..."
	terraform apply tfplan
	@rm -f tfplan

# Apply without saved plan (interactive)
apply-auto:
	@echo "Applying infrastructure changes (auto-approve)..."
	terraform apply -auto-approve

# Destroy infrastructure
destroy:
	@echo "WARNING: This will destroy all infrastructure!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read _
	terraform destroy

# Show outputs
output:
	@echo "Terraform outputs:"
	terraform output

# Clean Terraform files
clean:
	@echo "Cleaning Terraform files..."
	rm -rf .terraform .terraform.lock.hcl tfplan terraform.tfstate.backup

# Configure kubectl
kubeconfig:
	@echo "kubectl configuration command:"
	@terraform output -raw configure_kubectl

# Execute kubectl configuration
kubeconfig-exec:
	@echo "Configuring kubectl..."
	@eval "$$(terraform output -raw configure_kubectl)"
	@echo "kubectl configured successfully!"

# Show Docker push commands
push-images:
	@echo "Docker image push commands:"
	@terraform output -raw docker_push_commands

# Show Helm deployment commands
deploy-helm:
	@echo "Helm deployment commands:"
	@terraform output -raw helm_deploy_commands

# Show deployment summary
summary:
	@terraform output -raw deployment_summary

# Refresh state
refresh:
	@echo "Refreshing Terraform state..."
	terraform refresh

# Import existing resource (example)
import:
	@echo "Import existing GCP resources:"
	@echo "  terraform import module.gke.google_container_cluster.primary projects/PROJECT/locations/REGION/clusters/NAME"

# List workspaces
workspaces:
	@echo "Terraform workspaces:"
	terraform workspace list

# Create new workspace
workspace-new:
	@read -p "Enter workspace name: " name; \
	terraform workspace new $$name

# Switch workspace
workspace-select:
	@read -p "Enter workspace name: " name; \
	terraform workspace select $$name

# Show state list
state-list:
	@terraform state list

# Pull state
state-pull:
	@terraform state pull

# Graph visualization (requires graphviz)
graph:
	@echo "Generating dependency graph..."
	terraform graph | dot -Tpng > graph.png
	@echo "Graph saved to graph.png"

# Check formatting
fmt-check:
	@terraform fmt -check -recursive

# Security scan (requires tfsec)
security-scan:
	@echo "Running security scan..."
	@if command -v tfsec >/dev/null 2>&1; then \
		tfsec .; \
	else \
		echo "tfsec not installed. Install with: brew install tfsec"; \
	fi

# Cost estimation (requires infracost)
cost-estimate:
	@echo "Estimating infrastructure costs..."
	@if command -v infracost >/dev/null 2>&1; then \
		infracost breakdown --path .; \
	else \
		echo "infracost not installed. Visit: https://www.infracost.io/docs/"; \
	fi

# Upgrade providers
upgrade-providers:
	@echo "Upgrading Terraform providers..."
	terraform init -upgrade

# Lock providers
lock-providers:
	@echo "Locking provider versions..."
	terraform providers lock \
		-platform=darwin_amd64 \
		-platform=darwin_arm64 \
		-platform=linux_amd64 \
		-platform=linux_arm64

# Complete setup workflow
setup: init validate plan
	@echo "Setup complete! Review the plan and run 'make apply' to deploy."

# Complete deployment workflow
deploy: init validate apply kubeconfig-exec
	@echo "Deployment complete!"
	@echo ""
	@make summary

# Backup state
backup-state:
	@echo "Backing up Terraform state..."
	@terraform state pull > terraform.tfstate.backup.$$(date +%Y%m%d_%H%M%S)
	@echo "State backed up successfully!"

# Show resource list
resources:
	@echo "Deployed resources:"
	@terraform state list | sort
