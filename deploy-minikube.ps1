# =============================================================================
# Todo App - Minikube Deployment Script (Windows PowerShell)
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Todo App - Minikube Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Start Minikube
Write-Host ""
Write-Host "[1/4] Starting Minikube..." -ForegroundColor Yellow
minikube start --driver=docker

# Load Docker images to Minikube
Write-Host ""
Write-Host "[2/4] Loading Docker images to Minikube..." -ForegroundColor Yellow
minikube image load todo-frontend:phase4
minikube image load todo-backend:phase4

# Deploy using Helm
Write-Host ""
Write-Host "[3/4] Deploying using Helm..." -ForegroundColor Yellow
helm install todo-app ./helm-chart

# Check pods
Write-Host ""
Write-Host "[4/4] Checking pods..." -ForegroundColor Yellow
kubectl get pods

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Monitor with kubectl-ai:" -ForegroundColor Cyan
Write-Host "  kubectl-ai 'analyze cluster health'" -ForegroundColor White
Write-Host "  kubectl-ai 'scale backend replicas to 3'" -ForegroundColor White
Write-Host ""
Write-Host "Optimize with kagent:" -ForegroundColor Cyan
Write-Host "  kagent 'optimize resource allocation'" -ForegroundColor White
Write-Host ""
