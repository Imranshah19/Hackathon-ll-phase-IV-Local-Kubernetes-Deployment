#!/bin/bash
# =============================================================================
# Todo App - Minikube Deployment Script
# =============================================================================

set -e

echo "=========================================="
echo "  Todo App - Minikube Deployment"
echo "=========================================="

# Start Minikube
echo ""
echo "[1/4] Starting Minikube..."
minikube start --driver=docker

# Load Docker images to Minikube
echo ""
echo "[2/4] Loading Docker images to Minikube..."
minikube image load todo-frontend:phase4
minikube image load todo-backend:phase4

# Deploy using Helm
echo ""
echo "[3/4] Deploying using Helm..."
helm install todo-app ./helm-chart

# Check pods
echo ""
echo "[4/4] Checking pods..."
kubectl get pods

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Monitor with kubectl-ai:"
echo "  kubectl-ai \"analyze cluster health\""
echo "  kubectl-ai \"scale backend replicas to 3\""
echo ""
echo "Optimize with kagent:"
echo "  kagent \"optimize resource allocation\""
echo ""
