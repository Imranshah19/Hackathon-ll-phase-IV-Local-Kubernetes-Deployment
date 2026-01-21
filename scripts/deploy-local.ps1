# =============================================================================
# Local Deployment Script (PowerShell)
# =============================================================================
# Builds Docker images and deploys to Minikube using Helm
# Usage: .\scripts\deploy-local.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Todo App - Local Deployment" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

# Configuration
$RELEASE_NAME = if ($env:RELEASE_NAME) { $env:RELEASE_NAME } else { "todo-app" }
$NAMESPACE = if ($env:NAMESPACE) { $env:NAMESPACE } else { "default" }

# Check if minikube is running
$minikubeStatus = minikube status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Minikube is not running" -ForegroundColor Red
    Write-Host "Please run: .\scripts\minikube-setup.ps1"
    exit 1
}

# Check for required environment variables
if (-not $env:NEON_DB_URL -and -not $env:DATABASE_URL) {
    Write-Host "Warning: NEON_DB_URL is not set" -ForegroundColor Yellow
    Write-Host "Set it with: `$env:NEON_DB_URL = 'postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require'"
    Write-Host "Note: Database must be in Neon cloud, NOT in Minikube"
    $response = Read-Host "Continue anyway? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        exit 1
    }
}

# Use NEON_DB_URL if set, otherwise fall back to DATABASE_URL
$DB_URL = if ($env:NEON_DB_URL) { $env:NEON_DB_URL } else { $env:DATABASE_URL }

# Configure Docker to use Minikube's daemon
Write-Host "Configuring Docker environment..." -ForegroundColor Green
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Build backend image
Write-Host "Building backend image..." -ForegroundColor Green
docker build -t todo-backend:latest "$PROJECT_ROOT\backend"

# Build frontend image
Write-Host "Building frontend image..." -ForegroundColor Green
docker build -t todo-frontend:latest "$PROJECT_ROOT\frontend"

# Deploy with Helm
Write-Host "Deploying with Helm..." -ForegroundColor Green

# Prepare helm values
$helmSetFlags = @()

# Database (Neon - external cloud)
if ($DB_URL) {
    $helmSetFlags += "--set", "secrets.neonDbUrl=$DB_URL"
}

# Authentication
if ($env:AUTH_SECRET) {
    $helmSetFlags += "--set", "secrets.authSecret=$($env:AUTH_SECRET)"
} elseif ($env:JWT_SECRET_KEY) {
    $helmSetFlags += "--set", "secrets.authSecret=$($env:JWT_SECRET_KEY)"
} else {
    $helmSetFlags += "--set", "secrets.authSecret=development-auth-secret-key-min-32-chars"
}

# Next.js domain key
if ($env:NEXT_DOMAIN_KEY) {
    $helmSetFlags += "--set", "secrets.nextDomainKey=$($env:NEXT_DOMAIN_KEY)"
}

# OpenAI
if ($env:OPENAI_API_KEY) {
    $helmSetFlags += "--set", "secrets.openaiApiKey=$($env:OPENAI_API_KEY)"
}

# AI Configuration (optional)
if ($env:OPENAI_MODEL) {
    $helmSetFlags += "--set", "config.openaiModel=$($env:OPENAI_MODEL)"
}

if ($env:AGENT_NAME) {
    $helmSetFlags += "--set", "config.agentName=$($env:AGENT_NAME)"
}

# Run helm upgrade --install
helm upgrade --install $RELEASE_NAME "$PROJECT_ROOT\helm\todo-app" `
    --namespace $NAMESPACE `
    @helmSetFlags

# Wait for pods to be ready
Write-Host "Waiting for pods to be ready..." -ForegroundColor Green

Write-Host "  Waiting for backend pods..."
kubectl wait --for=condition=ready pod `
    -l app.kubernetes.io/component=backend `
    --timeout=120s `
    --namespace $NAMESPACE 2>$null

Write-Host "  Waiting for frontend pods..."
kubectl wait --for=condition=ready pod `
    -l app.kubernetes.io/component=frontend `
    --timeout=120s `
    --namespace $NAMESPACE 2>$null

# Get Minikube IP
$MINIKUBE_IP = minikube ip

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application URL: http://todo.local"
Write-Host ""
Write-Host "Add this to your hosts file (if not already added):"
Write-Host "  $MINIKUBE_IP  todo.local"
Write-Host "  File: C:\Windows\System32\drivers\etc\hosts"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  kubectl get pods              # List all pods"
Write-Host "  kubectl get svc               # List all services"
Write-Host "  kubectl get ingress           # List ingress rules"
Write-Host ""
