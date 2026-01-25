# =============================================================================
# Todo App - Full Kubernetes Deployment Script (Windows PowerShell)
# =============================================================================
# Usage: .\deploy.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Todo App - Kubernetes Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Start Minikube
Write-Host ""
Write-Host "[1/7] Starting Minikube..." -ForegroundColor Yellow
minikube start --memory=4096 --cpus=2

# Step 2: Enable Ingress
Write-Host ""
Write-Host "[2/7] Enabling Ingress addon..." -ForegroundColor Yellow
minikube addons enable ingress

# Step 3: Configure Docker environment
Write-Host ""
Write-Host "[3/7] Configuring Docker environment..." -ForegroundColor Yellow
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Step 4: Build Backend Image
Write-Host ""
Write-Host "[4/7] Building Backend image..." -ForegroundColor Yellow
docker build -t todo-backend:phase4 ./backend

# Step 5: Build Frontend Image
Write-Host ""
Write-Host "[5/7] Building Frontend image..." -ForegroundColor Yellow
docker build -t todo-frontend:phase4 ./frontend

# Step 6: Deploy with Helm
Write-Host ""
Write-Host "[6/7] Deploying with Helm..." -ForegroundColor Yellow
helm upgrade --install todo-app ./helm/todo-app

# Step 7: Wait for pods
Write-Host ""
Write-Host "[7/7] Waiting for pods to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=todo-backend --timeout=120s
kubectl wait --for=condition=ready pod -l app=todo-frontend --timeout=120s

# Get Minikube IP
$MINIKUBE_IP = minikube ip

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Pods:" -ForegroundColor Cyan
kubectl get pods
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
kubectl get svc
Write-Host ""
Write-Host "Ingress:" -ForegroundColor Cyan
kubectl get ingress
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Next Steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Add to C:\Windows\System32\drivers\etc\hosts:" -ForegroundColor White
Write-Host "   $MINIKUBE_IP todo.local" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Access the app:" -ForegroundColor White
Write-Host "   http://todo.local" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Useful commands:" -ForegroundColor White
Write-Host "   kubectl get pods                      # Check pods" -ForegroundColor Gray
Write-Host "   kubectl logs -l app=todo-backend      # Backend logs" -ForegroundColor Gray
Write-Host "   kubectl logs -l app=todo-frontend     # Frontend logs" -ForegroundColor Gray
Write-Host ""
