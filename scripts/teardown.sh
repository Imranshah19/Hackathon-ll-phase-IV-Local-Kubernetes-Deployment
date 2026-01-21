#!/bin/bash
# =============================================================================
# Teardown Script
# =============================================================================
# Cleans up the Todo App deployment from Minikube
# Usage: ./scripts/teardown.sh [--stop-minikube]
# =============================================================================

set -e

echo "=============================================="
echo "  Todo App - Teardown"
echo "=============================================="

# Configuration
RELEASE_NAME=${RELEASE_NAME:-todo-app}
NAMESPACE=${NAMESPACE:-default}
STOP_MINIKUBE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stop-minikube)
            STOP_MINIKUBE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--stop-minikube]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if helm release exists
if helm status ${RELEASE_NAME} --namespace ${NAMESPACE} &> /dev/null; then
    echo -e "${GREEN}Uninstalling Helm release: ${RELEASE_NAME}${NC}"
    helm uninstall ${RELEASE_NAME} --namespace ${NAMESPACE}
else
    echo -e "${YELLOW}Helm release ${RELEASE_NAME} not found${NC}"
fi

# Clean up Docker images from Minikube
if minikube status &> /dev/null; then
    echo -e "${GREEN}Cleaning up Docker images...${NC}"
    eval $(minikube docker-env)

    # Remove images if they exist
    docker rmi todo-backend:latest 2>/dev/null || true
    docker rmi todo-frontend:latest 2>/dev/null || true
fi

# Stop Minikube if requested
if [ "$STOP_MINIKUBE" = true ]; then
    if minikube status &> /dev/null; then
        echo -e "${GREEN}Stopping Minikube...${NC}"
        minikube stop
    else
        echo -e "${YELLOW}Minikube is not running${NC}"
    fi
fi

echo ""
echo "=============================================="
echo -e "${GREEN}  Teardown Complete!${NC}"
echo "=============================================="
echo ""

if [ "$STOP_MINIKUBE" = false ]; then
    echo "Minikube is still running."
    echo "To stop it: minikube stop"
    echo "To delete it: minikube delete"
fi
echo ""
