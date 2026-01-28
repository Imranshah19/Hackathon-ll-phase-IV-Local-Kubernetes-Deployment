#!/bin/bash
# =============================================================================
# Minikube Local Deployment Script
# =============================================================================
# Deploys the Todo App with Dapr and Kafka on Minikube
#
# Prerequisites:
#   - minikube installed
#   - kubectl installed
#   - dapr CLI installed
#   - Docker installed
#
# Usage:
#   chmod +x scripts/minikube-deploy.sh
#   ./scripts/minikube-deploy.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "Todo App - Minikube Deployment"
echo "=============================================="

# Step 1: Start Minikube
echo ""
echo "[1/6] Starting Minikube..."
if minikube status | grep -q "Running"; then
    echo "  ✓ Minikube is already running"
else
    minikube start --cpus=4 --memory=4096 --driver=docker
    echo "  ✓ Minikube started"
fi

# Step 2: Initialize Dapr on Kubernetes
echo ""
echo "[2/6] Initializing Dapr..."
if kubectl get namespace dapr-system &> /dev/null; then
    echo "  ✓ Dapr is already installed"
else
    dapr init -k --wait
    echo "  ✓ Dapr initialized on Kubernetes"
fi

# Step 3: Deploy Kafka cluster
echo ""
echo "[3/6] Deploying Kafka cluster..."
kubectl apply -f "$PROJECT_ROOT/k8s/kafka-cluster.yaml"
echo "  Waiting for Kafka to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/kafka -n kafka || true
kubectl wait --for=condition=available --timeout=120s deployment/zookeeper -n kafka || true
echo "  ✓ Kafka cluster deployed"

# Step 4: Deploy Dapr components
echo ""
echo "[4/6] Deploying Dapr pub/sub component..."
kubectl apply -f "$PROJECT_ROOT/k8s/dapr-pubsub-kafka.yaml"
echo "  ✓ Dapr components configured"

# Step 5: Build and load backend image
echo ""
echo "[5/6] Building backend image..."
eval $(minikube docker-env)
docker build -t todo-backend:latest "$PROJECT_ROOT/backend"
echo "  ✓ Backend image built"

# Step 6: Deploy backend
echo ""
echo "[6/6] Deploying backend..."
kubectl apply -f "$PROJECT_ROOT/k8s/backend-deployment.yaml"
echo "  Waiting for backend to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/todo-backend || true
echo "  ✓ Backend deployed"

# Summary
echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo ""
echo "Services:"
echo "  - Backend: kubectl port-forward svc/todo-backend 8000:8000"
echo "  - Kafka UI: minikube service kafka-ui -n kafka"
echo ""
echo "Verify Dapr:"
echo "  dapr components -k"
echo "  dapr dashboard -k"
echo ""
echo "View logs:"
echo "  kubectl logs -l app=todo-backend -c backend -f"
echo "  kubectl logs -l app=todo-backend -c daprd -f"
echo ""
