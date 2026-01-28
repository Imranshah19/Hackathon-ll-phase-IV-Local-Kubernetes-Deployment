# =============================================================================
# Minikube Local Deployment Script (PowerShell)
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
#   .\scripts\minikube-deploy.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "=============================================="
Write-Host "Todo App - Minikube Deployment"
Write-Host "=============================================="

# Step 1: Start Minikube
Write-Host ""
Write-Host "[1/6] Starting Minikube..."
$minikubeStatus = minikube status 2>&1
if ($minikubeStatus -match "Running") {
    Write-Host "  [OK] Minikube is already running" -ForegroundColor Green
} else {
    minikube start --cpus=4 --memory=4096 --driver=docker
    Write-Host "  [OK] Minikube started" -ForegroundColor Green
}

# Step 2: Initialize Dapr on Kubernetes
Write-Host ""
Write-Host "[2/6] Initializing Dapr..."
$daprNs = kubectl get namespace dapr-system 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Dapr is already installed" -ForegroundColor Green
} else {
    dapr init -k --wait
    Write-Host "  [OK] Dapr initialized on Kubernetes" -ForegroundColor Green
}

# Step 3: Deploy Kafka cluster
Write-Host ""
Write-Host "[3/6] Deploying Kafka cluster..."
kubectl apply -f "$ProjectRoot\k8s\kafka-cluster.yaml"
Write-Host "  Waiting for Kafka to be ready..."
Start-Sleep -Seconds 30
kubectl wait --for=condition=available --timeout=120s deployment/zookeeper -n kafka 2>&1 | Out-Null
kubectl wait --for=condition=available --timeout=120s deployment/kafka -n kafka 2>&1 | Out-Null
Write-Host "  [OK] Kafka cluster deployed" -ForegroundColor Green

# Step 4: Deploy Dapr components
Write-Host ""
Write-Host "[4/6] Deploying Dapr pub/sub component..."
kubectl apply -f "$ProjectRoot\k8s\dapr-pubsub-kafka.yaml"
Write-Host "  [OK] Dapr components configured" -ForegroundColor Green

# Step 5: Build and load backend image
Write-Host ""
Write-Host "[5/6] Building backend image..."
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t todo-backend:latest "$ProjectRoot\backend"
Write-Host "  [OK] Backend image built" -ForegroundColor Green

# Step 6: Deploy backend
Write-Host ""
Write-Host "[6/6] Deploying backend..."
kubectl apply -f "$ProjectRoot\k8s\backend-deployment.yaml"
Write-Host "  Waiting for backend to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/todo-backend 2>&1 | Out-Null
Write-Host "  [OK] Backend deployed" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "=============================================="
Write-Host "Deployment Complete!"
Write-Host "=============================================="
Write-Host ""
Write-Host "Services:"
Write-Host "  - Backend: kubectl port-forward svc/todo-backend 8000:8000"
Write-Host "  - Kafka UI: minikube service kafka-ui -n kafka"
Write-Host ""
Write-Host "Verify Dapr:"
Write-Host "  dapr components -k"
Write-Host "  dapr dashboard -k"
Write-Host ""
Write-Host "View logs:"
Write-Host "  kubectl logs -l app=todo-backend -c backend -f"
Write-Host "  kubectl logs -l app=todo-backend -c daprd -f"
Write-Host ""
