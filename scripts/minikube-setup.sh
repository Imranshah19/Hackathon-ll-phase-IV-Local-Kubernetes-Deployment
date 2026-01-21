#!/bin/bash
# =============================================================================
# Minikube Setup Script
# =============================================================================
# Initializes Minikube cluster with required resources and addons
# Usage: ./scripts/minikube-setup.sh
# =============================================================================

set -e

echo "=============================================="
echo "  Todo App - Minikube Setup"
echo "=============================================="

# Configuration
MINIKUBE_MEMORY=${MINIKUBE_MEMORY:-4096}
MINIKUBE_CPUS=${MINIKUBE_CPUS:-2}
MINIKUBE_DRIVER=${MINIKUBE_DRIVER:-docker}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    echo -e "${RED}Error: minikube is not installed${NC}"
    echo "Please install minikube: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    echo "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm is not installed${NC}"
    echo "Please install helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

# Check if minikube is already running
if minikube status &> /dev/null; then
    echo -e "${YELLOW}Minikube is already running${NC}"
    read -p "Do you want to delete and recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing minikube cluster..."
        minikube delete
    else
        echo "Using existing minikube cluster"
    fi
fi

# Start minikube if not running
if ! minikube status &> /dev/null; then
    echo -e "${GREEN}Starting Minikube...${NC}"
    echo "  Memory: ${MINIKUBE_MEMORY}MB"
    echo "  CPUs: ${MINIKUBE_CPUS}"
    echo "  Driver: ${MINIKUBE_DRIVER}"

    minikube start \
        --memory=${MINIKUBE_MEMORY} \
        --cpus=${MINIKUBE_CPUS} \
        --driver=${MINIKUBE_DRIVER}
fi

# Enable required addons
echo -e "${GREEN}Enabling addons...${NC}"

echo "  - Enabling ingress addon..."
minikube addons enable ingress

echo "  - Enabling metrics-server addon..."
minikube addons enable metrics-server

echo "  - Enabling dashboard addon (optional)..."
minikube addons enable dashboard || true

# Wait for ingress controller to be ready
echo -e "${GREEN}Waiting for ingress controller...${NC}"
kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s || echo "Ingress controller not ready yet, continuing..."

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

echo ""
echo "=============================================="
echo -e "${GREEN}  Minikube Setup Complete!${NC}"
echo "=============================================="
echo ""
echo "Minikube IP: ${MINIKUBE_IP}"
echo ""
echo "Next steps:"
echo "  1. Add to your hosts file:"
echo "     ${MINIKUBE_IP}  todo.local"
echo ""
echo "  2. Configure Docker to use Minikube's daemon:"
echo "     eval \$(minikube docker-env)"
echo ""
echo "  3. Run the deployment script:"
echo "     ./scripts/deploy-local.sh"
echo ""
echo "Useful commands:"
echo "  minikube dashboard    # Open Kubernetes dashboard"
echo "  minikube ip           # Get Minikube IP"
echo "  kubectl get pods      # List pods"
echo ""
