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
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}Warning: DATABASE_URL is not set${NC}"
    echo "Set it with: export DATABASE_URL='your-neon-connection-string'"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

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

if [ -n "$DATABASE_URL" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.databaseUrl=${DATABASE_URL}"
fi

if [ -n "$JWT_SECRET_KEY" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.jwtSecret=${JWT_SECRET_KEY}"
else
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.jwtSecret=development-jwt-secret-key-min-32-chars"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    HELM_SET_FLAGS="${HELM_SET_FLAGS} --set secrets.openaiApiKey=${OPENAI_API_KEY}"
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
