#!/bin/bash
# =============================================================================
# Todo App - Full Kubernetes Deployment Script
# =============================================================================
# Usage: ./deploy.sh
# =============================================================================

set -e

echo "=========================================="
echo "  Todo App - Kubernetes Deployment"
echo "=========================================="

# Step 1: Start Minikube
echo ""
echo "[1/7] Starting Minikube..."
minikube start --memory=4096 --cpus=2

# Step 2: Enable Ingress
echo ""
echo "[2/7] Enabling Ingress addon..."
minikube addons enable ingress

# Step 3: Configure Docker environment
echo ""
echo "[3/7] Configuring Docker environment..."
eval $(minikube docker-env)

# Step 4: Build Backend Image
echo ""
echo "[4/7] Building Backend image..."
docker build -t todo-backend:phase4 ./backend

# Step 5: Build Frontend Image
echo ""
echo "[5/7] Building Frontend image..."
docker build -t todo-frontend:phase4 ./frontend

# Step 6: Deploy with Helm
echo ""
echo "[6/7] Deploying with Helm..."
helm upgrade --install todo-app ./helm/todo-app

# Step 7: Wait for pods
echo ""
echo "[7/7] Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=todo-backend --timeout=120s
kubectl wait --for=condition=ready pod -l app=todo-frontend --timeout=120s

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Pods:"
kubectl get pods
echo ""
echo "Services:"
kubectl get svc
echo ""
echo "Ingress:"
kubectl get ingress
echo ""
echo "=========================================="
echo "  Next Steps:"
echo "=========================================="
echo ""
echo "1. Add to /etc/hosts:"
echo "   $MINIKUBE_IP todo.local"
echo ""
echo "2. Access the app:"
echo "   http://todo.local"
echo ""
echo "3. Useful commands:"
echo "   kubectl get pods          # Check pods"
echo "   kubectl logs -l app=todo-backend   # Backend logs"
echo "   kubectl logs -l app=todo-frontend  # Frontend logs"
echo ""
