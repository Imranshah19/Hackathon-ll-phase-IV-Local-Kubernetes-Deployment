# =============================================================================
# Minikube Setup Script (PowerShell)
# =============================================================================
# Initializes Minikube cluster with required resources and addons
# Usage: .\scripts\minikube-setup.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Todo App - Minikube Setup" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Configuration
$MINIKUBE_MEMORY = if ($env:MINIKUBE_MEMORY) { $env:MINIKUBE_MEMORY } else { "4096" }
$MINIKUBE_CPUS = if ($env:MINIKUBE_CPUS) { $env:MINIKUBE_CPUS } else { "2" }
$MINIKUBE_DRIVER = if ($env:MINIKUBE_DRIVER) { $env:MINIKUBE_DRIVER } else { "docker" }

# Check if minikube is installed
if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    Write-Host "Error: minikube is not installed" -ForegroundColor Red
    Write-Host "Please install minikube: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
}

# Check if kubectl is installed
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "Error: kubectl is not installed" -ForegroundColor Red
    Write-Host "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
}

# Check if helm is installed
if (-not (Get-Command helm -ErrorAction SilentlyContinue)) {
    Write-Host "Error: helm is not installed" -ForegroundColor Red
    Write-Host "Please install helm: https://helm.sh/docs/intro/install/"
    exit 1
}

# Check if minikube is already running
$minikubeStatus = minikube status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Minikube is already running" -ForegroundColor Yellow
    $response = Read-Host "Do you want to delete and recreate it? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Deleting existing minikube cluster..."
        minikube delete
    } else {
        Write-Host "Using existing minikube cluster"
    }
}

# Start minikube if not running
$minikubeStatus = minikube status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Starting Minikube..." -ForegroundColor Green
    Write-Host "  Memory: ${MINIKUBE_MEMORY}MB"
    Write-Host "  CPUs: ${MINIKUBE_CPUS}"
    Write-Host "  Driver: ${MINIKUBE_DRIVER}"

    minikube start --memory=$MINIKUBE_MEMORY --cpus=$MINIKUBE_CPUS --driver=$MINIKUBE_DRIVER
}

# Enable required addons
Write-Host "Enabling addons..." -ForegroundColor Green

Write-Host "  - Enabling ingress addon..."
minikube addons enable ingress

Write-Host "  - Enabling metrics-server addon..."
minikube addons enable metrics-server

Write-Host "  - Enabling dashboard addon (optional)..."
minikube addons enable dashboard 2>$null

# Wait for ingress controller
Write-Host "Waiting for ingress controller..." -ForegroundColor Green
kubectl wait --namespace ingress-nginx `
    --for=condition=ready pod `
    --selector=app.kubernetes.io/component=controller `
    --timeout=120s 2>$null

# Get Minikube IP
$MINIKUBE_IP = minikube ip

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Minikube Setup Complete!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Minikube IP: $MINIKUBE_IP"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Add to your hosts file (as Administrator):"
Write-Host "     $MINIKUBE_IP  todo.local"
Write-Host "     File: C:\Windows\System32\drivers\etc\hosts"
Write-Host ""
Write-Host "  2. Configure Docker to use Minikube's daemon:"
Write-Host "     & minikube -p minikube docker-env --shell powershell | Invoke-Expression"
Write-Host ""
Write-Host "  3. Run the deployment script:"
Write-Host "     .\scripts\deploy-local.ps1"
Write-Host ""
