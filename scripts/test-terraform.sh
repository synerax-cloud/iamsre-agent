#!/bin/bash
# Test Terraform configuration without deploying

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║      Testing Terraform Configuration                 ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

cd terraform

echo "[1/3] Validating Terraform syntax..."
terraform validate

echo ""
echo "[2/3] Formatting check..."
terraform fmt -check -recursive || {
    echo "Auto-formatting files..."
    terraform fmt -recursive
}

echo ""
echo "[3/3] Running terraform plan..."
terraform plan

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║          Terraform Configuration is Valid!           ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "Ready to deploy with: terraform apply"
