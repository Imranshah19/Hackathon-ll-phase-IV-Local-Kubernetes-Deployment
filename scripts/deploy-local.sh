#!/bin/bash
# =============================================================================
# Local Deployment Script
# =============================================================================
# Builds Docker images and deploys to Minikube using Helm
# Usage: ./scripts/deploy-local.sh
# =============================================================================

set -e

echo "=============================================="
echo "  Todo App - Local Deployment"
echo "=============================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RELEASE_NAME=${RELEASE_NAME:-todo-app}
NAMESPACE=${NAMESPACE:-default}

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo -e "${RED}Error: Minikube is not running${NC}"
    echo "Please run: ./scripts/minikube-setup.sh"
    exit 1
fi

# Check for required environment variables
if [ -z "$NEON_DB_URL" ] && [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}Warning: NEON_DB_URL is not set${NC}"
    echo "Set it with: export NEON_DB_URL='postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require'"
    echo "Note: Database must be in Neon cloud, NOT in Minikube"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Use NEON_DB_URL if set, otherwise fall back to DATABASE_URL
DB_URL="${NEON_DB_URL:-$DATABASE_URL}"

# Configure Docker to use Minikube's daemon
echo -e "${GREEN}Configuring Docker environment...${NC}"
eval $(minikube docker-env)

# Build backend image
echo -e "${GREEN}Building backend image...${NC}"
docker build -t todo-backend:latest "${PROJECT_ROOT}/backend"

# Build frontend image
echo -e "${GREEN}Building frontend image...${NC}"
docker build -t todo-frontend:latest "${PROJECT_ROOT}/frontend"

# Deploy with Helm
echo -e "${GREEN}Deploying with Helm...${NC}"

# Prepare helm values
HELM_SET_FLAGS=""

# Database (Neon - external cloud)
if [ -n "$DB_URL" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.neonDbUrl=${DB_URL}"
fi

# Authentication
if [ -n "$AUTH_SECRET" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.authSecret=${AUTH_SECRET}"
elif [ -n "$JWT_SECRET_KEY" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.authSecret=${JWT_SECRET_KEY}"
else
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.authSecret=development-auth-secret-key-min-32-chars"
fi

# Next.js domain key
if [ -n "$NEXT_DOMAIN_KEY" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.nextDomainKey=${NEXT_DOMAIN_KEY}"
fi

# OpenAI
if [ -n "$OPENAI_API_KEY" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.openaiApiKey=${OPENAI_API_KEY}"
fi

# AI Configuration (optional)
if [ -n "$OPENAI_MODEL" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set config.openaiModel=${OPENAI_MODEL}"
fi

if [ -n "$AGENT_NAME" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set config.agentName=${AGENT_NAME}"
fi

# Run helm upgrade --install
helm upgrade --install ${RELEASE_NAME} "${PROJECT_ROOT}/helm/todo-app" \
    --namespace ${NAMESPACE} \
    ${HELM_SET_FLAGS}

# Wait for pods to be ready
echo -e "${GREEN}Waiting for pods to be ready...${NC}"

echo "  Waiting for backend pods..."
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/component=backend \
    --timeout=120s \
    --namespace ${NAMESPACE} || true

echo "  Waiting for frontend pods..."
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/component=frontend \
    --timeout=120s \
    --namespace ${NAMESPACE} || true

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

echo ""
echo "=============================================="
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "=============================================="
echo ""
echo "Application URL: http://todo.local"
echo ""
echo "Add this to your hosts file (if not already added):"
echo "  ${MINIKUBE_IP}  todo.local"
echo ""
echo "On Windows: C:\\Windows\\System32\\drivers\\etc\\hosts"
echo "On Linux/Mac: /etc/hosts"
echo ""
echo "Useful commands:"
echo "  kubectl get pods              # List all pods"
echo "  kubectl get svc               # List all services"
echo "  kubectl get ingress           # List ingress rules"
echo "  kubectl logs -l app.kubernetes.io/component=backend   # Backend logs"
echo "  kubectl logs -l app.kubernetes.io/component=frontend  # Frontend logs"
echo ""
echo "To scale:"
echo "  helm upgrade ${RELEASE_NAME} ./helm/todo-app --set backend.replicas=3"
echo ""
