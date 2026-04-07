# Push to GitHub Instructions

Follow these steps to push your code to the synerax-cloud organization:

## 1. Create Repository on GitHub

1. Go to https://github.com/organizations/synerax-cloud/repositories/new
   (Or navigate to: GitHub → Your Organizations → synerax-cloud → Repositories → New)

2. Fill in the details:
   - **Repository name**: `iamsre-agent`
   - **Description**: AI-Powered Kubernetes SRE Agent for GKE with self-hosted LLM
   - **Visibility**: Public (or Private if you prefer)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

3. Click "Create repository"

## 2. Push Your Code

After creating the repository, run these commands:

```bash
cd /Users/shubham/Kubernetes-agent

# Add the remote repository
git remote add origin https://github.com/synerax-cloud/iamsre-agent.git

# Verify the remote
git remote -v

# Push to main branch
git push -u origin main
```

If you encounter authentication issues, you'll need to use a Personal Access Token:

### Generate GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. Select scopes: `repo` (Full control of private repositories)
3. Generate token and copy it
4. When prompted for password during `git push`, use the token instead

Alternatively, use SSH:

```bash
# Add SSH remote instead
git remote remove origin
git remote add origin git@github.com:synerax-cloud/iamsre-agent.git
git push -u origin main
```

## 3. Verify

After pushing, visit:
https://github.com/synerax-cloud/iamsre-agent

You should see all your files!

## 4. Add Repository Topics (Optional)

On GitHub, click the gear icon next to "About" and add topics:
- kubernetes
- sre
- ai
- llm
- ollama
- gke
- terraform
- fastapi
- observability
- automation

## 5. Enable GitHub Actions (Optional)

The repository is ready for CI/CD. You can add GitHub Actions workflows later for:
- Automated testing
- Docker image builds
- Terraform validation
- Security scanning

---

## Quick Reference

Repository: https://github.com/synerax-cloud/iamsre-agent
Clone URL: git@github.com:synerax-cloud/iamsre-agent.git
