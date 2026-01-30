# Implementation Tasks: Phase 4 — Local Kubernetes Deployment

**Feature**: 007-kubernetes-deployment
**Created**: 2026-01-21
**Status**: Complete
**Last Updated**: 2026-01-30
**Plan Reference**: [plan.md](./plan.md)

---

## Task Overview

| Phase | Tasks | Priority | Status |
|-------|-------|----------|--------|
| 4.1 Docker Containerization | 6 | P1 | ✅ Complete |
| 4.2 Helm Chart Development | 9 | P2 | ✅ Complete |
| 4.3 Minikube Deployment | 7 | P3 | ✅ Complete |
| 4.4 AI-Ops Integration | 4 | P4 | ✅ Complete |
| 4.5 Documentation | 3 | P5 | ✅ Complete |

**Total Tasks**: 29 (29 Complete)

---

## Phase 4.1: Docker Containerization (P1)

### Task 4.1.1: Create Backend Dockerfile

**Priority**: P1
**Estimate**: Small
**Dependencies**: None

**Description**: Create a multi-stage Dockerfile for the FastAPI backend that produces a minimal, production-ready image.

**Acceptance Criteria**:
- [x] Multi-stage build with builder and runtime stages
- [x] Base image: `python:3.11-slim`
- [x] All dependencies installed from pyproject.toml
- [x] Exposes port 8000
- [x] CMD runs uvicorn with proper host binding
- [x] Image size under 300MB

**Test Cases**:
```bash
# Build succeeds
docker build -t todo-backend:latest ./backend

# Container starts
docker run -d -p 8000:8000 --name test-backend \
  -e DATABASE_URL="postgresql://..." \
  todo-backend:latest

# Health check passes
curl http://localhost:8000/health
# Expected: {"status": "healthy", "database": "connected"}

# Cleanup
docker stop test-backend && docker rm test-backend
```

**File**: `backend/Dockerfile`

---

### Task 4.1.2: Add Health Endpoint to Backend

**Priority**: P1
**Estimate**: Small
**Dependencies**: None

**Description**: Add a `/health` endpoint to FastAPI that returns service status and database connectivity.

**Acceptance Criteria**:
- [x] GET `/health` returns 200 when healthy
- [x] Response includes database connection status
- [x] Returns 503 if database unreachable
- [x] No authentication required

**Test Cases**:
```python
# test_health.py
def test_health_endpoint_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_includes_database_status(client):
    response = client.get("/health")
    assert "database" in response.json()
```

**File**: `backend/src/api/health.py`

---

### Task 4.1.3: Create Frontend Dockerfile

**Priority**: P1
**Estimate**: Small
**Dependencies**: None

**Description**: Create a multi-stage Dockerfile for the Next.js frontend that builds and serves the application.

**Acceptance Criteria**:
- [x] Multi-stage build with builder and runtime stages
- [x] Base image: `node:20-alpine`
- [x] Dependencies installed with `npm ci`
- [x] Production build created
- [x] Exposes port 3000
- [x] Image size under 200MB

**Test Cases**:
```bash
# Build succeeds
docker build -t todo-frontend:latest ./frontend

# Container starts
docker run -d -p 3000:3000 --name test-frontend \
  -e NEXT_PUBLIC_API_URL="http://localhost:8000" \
  todo-frontend:latest

# UI loads
curl http://localhost:3000
# Expected: HTML response

# Cleanup
docker stop test-frontend && docker rm test-frontend
```

**File**: `frontend/Dockerfile`

---

### Task 4.1.4: Create .dockerignore Files

**Priority**: P1
**Estimate**: Small
**Dependencies**: 4.1.1, 4.1.3

**Description**: Create .dockerignore files to exclude unnecessary files from Docker build context.

**Acceptance Criteria**:
- [x] Backend: excludes __pycache__, .venv, tests, .git
- [x] Frontend: excludes node_modules, .next, .git
- [x] Build context size significantly reduced

**Files**: `backend/.dockerignore`, `frontend/.dockerignore`

---

### Task 4.1.5: Create docker-compose.yml for Local Testing

**Priority**: P1
**Estimate**: Small
**Dependencies**: 4.1.1, 4.1.3

**Description**: Create a docker-compose file for testing both containers locally before Kubernetes deployment.

**Acceptance Criteria**:
- [x] Defines backend and frontend services
- [x] Environment variables from .env file
- [x] Network allows frontend to reach backend
- [x] Ports exposed for local access

**Test Cases**:
```bash
# Start services
docker-compose up -d

# Verify backend
curl http://localhost:8000/health

# Verify frontend
curl http://localhost:3000

# Full flow test
# Login, create task, verify in database

# Cleanup
docker-compose down
```

**File**: `docker-compose.yml`

---

### Task 4.1.6: Verify Container Images

**Priority**: P1
**Estimate**: Small
**Dependencies**: 4.1.1, 4.1.3, 4.1.5

**Description**: Verify both container images work correctly together and all Phase 3 functionality is preserved.

**Acceptance Criteria**:
- [x] Both images build without errors
- [x] Containers start and pass health checks
- [x] User registration and login work
- [x] Task CRUD operations work
- [x] AI chat functionality works
- [x] Data persists to Neon PostgreSQL

---

## Phase 4.2: Helm Chart Development (P2)

### Task 4.2.1: Initialize Helm Chart Structure

**Priority**: P2
**Estimate**: Small
**Dependencies**: 4.1.6

**Description**: Create the basic Helm chart structure with Chart.yaml and initial values.yaml.

**Acceptance Criteria**:
- [x] Chart.yaml with name, version, appVersion
- [x] values.yaml with documented defaults
- [x] templates/_helpers.tpl with common functions
- [x] .helmignore file

**Test Cases**:
```bash
# Chart structure valid
helm lint ./helm/todo-app
# Expected: 0 errors
```

**Directory**: `helm/todo-app/`

---

### Task 4.2.2: Create Backend Deployment Template

**Priority**: P2
**Estimate**: Medium
**Dependencies**: 4.2.1

**Description**: Create Kubernetes Deployment template for the backend service.

**Acceptance Criteria**:
- [x] Deployment with configurable replicas
- [x] Resource requests and limits
- [x] Liveness and readiness probes
- [x] Environment variables from ConfigMap and Secrets
- [x] Labels from _helpers.tpl

**File**: `helm/todo-app/templates/backend-deployment.yaml`

---

### Task 4.2.3: Create Backend Service Template

**Priority**: P2
**Estimate**: Small
**Dependencies**: 4.2.2

**Description**: Create Kubernetes Service template to expose backend pods.

**Acceptance Criteria**:
- [x] ClusterIP service type
- [x] Port 8000 exposed
- [x] Selector matches deployment labels

**File**: `helm/todo-app/templates/backend-service.yaml`

---

### Task 4.2.4: Create Frontend Deployment Template

**Priority**: P2
**Estimate**: Medium
**Dependencies**: 4.2.1

**Description**: Create Kubernetes Deployment template for the frontend service.

**Acceptance Criteria**:
- [x] Deployment with configurable replicas
- [x] Resource requests and limits
- [x] Liveness and readiness probes
- [x] Environment variable for API URL
- [x] Labels from _helpers.tpl

**File**: `helm/todo-app/templates/frontend-deployment.yaml`

---

### Task 4.2.5: Create Frontend Service Template

**Priority**: P2
**Estimate**: Small
**Dependencies**: 4.2.4

**Description**: Create Kubernetes Service template to expose frontend pods.

**Acceptance Criteria**:
- [x] ClusterIP service type
- [x] Port 3000 exposed
- [x] Selector matches deployment labels

**File**: `helm/todo-app/templates/frontend-service.yaml`

---

### Task 4.2.6: Create Ingress Template

**Priority**: P2
**Estimate**: Medium
**Dependencies**: 4.2.3, 4.2.5

**Description**: Create Ingress template to route external traffic to services.

**Acceptance Criteria**:
- [x] Host configurable (default: todo.local)
- [x] `/api/*` routes to backend service
- [x] `/` routes to frontend service
- [x] NGINX ingress class annotation

**File**: `helm/todo-app/templates/ingress.yaml`

---

### Task 4.2.7: Create ConfigMap Template

**Priority**: P2
**Estimate**: Small
**Dependencies**: 4.2.1

**Description**: Create ConfigMap template for non-sensitive configuration.

**Acceptance Criteria**:
- [x] LOG_LEVEL, ENVIRONMENT, API_VERSION
- [x] Values from values.yaml

**File**: `helm/todo-app/templates/configmap.yaml`

---

### Task 4.2.8: Create Secrets Template

**Priority**: P2
**Estimate**: Small
**Dependencies**: 4.2.1

**Description**: Create Secrets template for sensitive configuration.

**Acceptance Criteria**:
- [x] DATABASE_URL, JWT_SECRET, OPENAI_API_KEY
- [x] Values base64 encoded
- [x] Warning comment about production usage

**File**: `helm/todo-app/templates/secrets.yaml`

---

### Task 4.2.9: Validate Helm Chart

**Priority**: P2
**Estimate**: Small
**Dependencies**: 4.2.2 - 4.2.8

**Description**: Validate the complete Helm chart with lint and template commands.

**Acceptance Criteria**:
- [x] `helm lint` passes with no errors
- [x] `helm template` generates valid YAML
- [x] All resources have correct labels
- [x] All selectors match

**Test Cases**:
```bash
# Lint chart
helm lint ./helm/todo-app

# Generate templates
helm template todo-app ./helm/todo-app > /tmp/manifests.yaml

# Validate YAML
kubectl apply --dry-run=client -f /tmp/manifests.yaml
```

---

## Phase 4.3: Minikube Deployment (P3)

### Task 4.3.1: Create Minikube Setup Script

**Priority**: P3
**Estimate**: Small
**Dependencies**: 4.2.9

**Description**: Create a script to initialize Minikube with required resources and addons.

**Acceptance Criteria**:
- [x] Starts Minikube with 4GB RAM, 2 CPUs
- [x] Enables ingress addon
- [x] Enables metrics-server addon
- [x] Outputs Minikube IP

**File**: `scripts/minikube-setup.sh`

---

### Task 4.3.2: Create Local Deployment Script

**Priority**: P3
**Estimate**: Medium
**Dependencies**: 4.3.1

**Description**: Create a script to build images and deploy to Minikube.

**Acceptance Criteria**:
- [x] Configures Minikube Docker environment
- [x] Builds both images
- [x] Deploys with Helm
- [x] Waits for pods to be ready
- [x] Outputs instructions for /etc/hosts

**File**: `scripts/deploy-local.sh`

---

### Task 4.3.3: Create Teardown Script

**Priority**: P3
**Estimate**: Small
**Dependencies**: 4.3.2

**Description**: Create a script to clean up the Minikube deployment.

**Acceptance Criteria**:
- [x] Uninstalls Helm release
- [x] Optionally stops Minikube
- [x] Cleans up local images (optional)

**File**: `scripts/teardown.sh`

---

### Task 4.3.4: Deploy to Minikube

**Priority**: P3
**Estimate**: Medium
**Dependencies**: 4.3.2

**Description**: Execute deployment and verify all components are running.

**Acceptance Criteria**:
- [x] All pods reach Ready state within 2 minutes
- [x] No pod restart loops
- [x] Services have endpoints
- [x] Ingress configured correctly

**Test Cases**:
```bash
# Run deployment
./scripts/deploy-local.sh

# Verify pods
kubectl get pods
# Expected: All pods Running, Ready 1/1

# Verify services
kubectl get svc
# Expected: backend-svc and frontend-svc listed

# Verify ingress
kubectl get ingress
# Expected: todo-ingress with host todo.local
```

---

### Task 4.3.5: Configure Local DNS

**Priority**: P3
**Estimate**: Small
**Dependencies**: 4.3.4

**Description**: Document and optionally automate local DNS configuration.

**Acceptance Criteria**:
- [x] Document /etc/hosts configuration
- [x] Script to add/remove entry (optional)
- [x] Works on Windows, Mac, Linux

---

### Task 4.3.6: End-to-End Testing

**Priority**: P3
**Estimate**: Medium
**Dependencies**: 4.3.5

**Description**: Verify all Phase 3 functionality works in Kubernetes environment.

**Acceptance Criteria**:
- [x] User registration works
- [x] User login works
- [x] Task CRUD operations work
- [x] AI chat functionality works
- [x] Conversation history persists
- [x] Data persists across pod restarts

---

### Task 4.3.7: Test Scaling

**Priority**: P3
**Estimate**: Small
**Dependencies**: 4.3.6

**Description**: Verify horizontal scaling works correctly.

**Acceptance Criteria**:
- [x] `helm upgrade --set backend.replicas=3` works
- [x] New pods start and receive traffic
- [x] No service interruption during scale

**Test Cases**:
```bash
# Scale up
helm upgrade todo-app ./helm/todo-app --set backend.replicas=3

# Verify
kubectl get pods
# Expected: 3 backend pods

# Scale down
helm upgrade todo-app ./helm/todo-app --set backend.replicas=2
```

---

## Phase 4.4: AI-Ops Integration (P4)

### Task 4.4.1: Install kubectl-ai

**Priority**: P4
**Estimate**: Small
**Dependencies**: 4.3.6

**Description**: Install and configure kubectl-ai for natural language cluster operations.

**Acceptance Criteria**:
- [x] kubectl-ai installed and accessible
- [x] OpenAI API key configured
- [x] Basic commands work

**Test Cases**:
```bash
# Verify installation
kubectl-ai version

# Test command
kubectl-ai "show all pods"
# Expected: Executes kubectl get pods
```

---

### Task 4.4.2: Install kagent (Optional)

**Priority**: P4
**Estimate**: Small
**Dependencies**: 4.3.6

**Description**: Install and configure kagent for intelligent cluster management.

**Acceptance Criteria**:
- [x] kagent installed (if supported on platform)
- [x] Basic diagnostic commands work
- [x] Can analyze pod issues

---

### Task 4.4.3: Document AI-Ops Commands

**Priority**: P4
**Estimate**: Small
**Dependencies**: 4.4.1

**Description**: Create documentation for common AI-ops operations.

**Acceptance Criteria**:
- [x] List of common natural language queries
- [x] Expected kubectl translations
- [x] Troubleshooting examples

---

### Task 4.4.4: Test AI-Ops Workflows

**Priority**: P4
**Estimate**: Small
**Dependencies**: 4.4.1, 4.4.3

**Description**: Verify AI-ops tools can perform common cluster operations.

**Acceptance Criteria**:
- [x] "Show all pods in todo namespace" works
- [x] "Get backend logs" works
- [x] "Scale backend to 3 replicas" works
- [x] "Why is pod X failing" provides useful info

---

## Phase 4.5: Documentation (P5)

### Task 4.5.1: Create Deployment README

**Priority**: P5
**Estimate**: Medium
**Dependencies**: 4.3.6

**Description**: Create comprehensive deployment documentation.

**Acceptance Criteria**:
- [x] Prerequisites listed
- [x] Quick start guide
- [x] Configuration options
- [x] Troubleshooting section

**File**: `docs/deployment.md`

---

### Task 4.5.2: Update Project README

**Priority**: P5
**Estimate**: Small
**Dependencies**: 4.5.1

**Description**: Update main README to include Phase 4 deployment instructions.

**Acceptance Criteria**:
- [x] Phase 4 section added
- [x] Quick start commands
- [x] Link to detailed docs

**File**: `README.md`

---

### Task 4.5.3: Create Troubleshooting Guide

**Priority**: P5
**Estimate**: Small
**Dependencies**: 4.3.6

**Description**: Document common issues and solutions.

**Acceptance Criteria**:
- [x] Pod startup issues
- [x] Database connection problems
- [x] Ingress configuration issues
- [x] Resource constraint issues

**File**: `docs/troubleshooting.md`

---

## Task Dependencies Graph

```
4.1.1 ─┬─► 4.1.4 ─┬─► 4.1.5 ─► 4.1.6
4.1.2 ─┤         │
4.1.3 ─┴─────────┘
           │
           ▼
        4.2.1
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
  4.2.2  4.2.4  4.2.7
     │     │     │
     ▼     ▼     ▼
  4.2.3  4.2.5  4.2.8
     │     │
     └──┬──┘
        ▼
      4.2.6
        │
        ▼
      4.2.9
        │
        ▼
      4.3.1 ─► 4.3.2 ─► 4.3.3
                 │
                 ▼
              4.3.4 ─► 4.3.5 ─► 4.3.6 ─► 4.3.7
                                   │
                        ┌──────────┼──────────┐
                        ▼          ▼          ▼
                     4.4.1      4.4.2      4.5.1
                        │                    │
                        ▼                    ▼
                     4.4.3 ─► 4.4.4       4.5.2
                                            │
                                            ▼
                                         4.5.3
```

---

## Completion Checklist

### Phase 4.1: Docker Containerization
- [X] 4.1.1 Backend Dockerfile created
- [X] 4.1.2 Health endpoint added
- [X] 4.1.3 Frontend Dockerfile created
- [X] 4.1.4 .dockerignore files created
- [X] 4.1.5 docker-compose.yml created
- [X] 4.1.6 Container images verified

### Phase 4.2: Helm Chart Development
- [X] 4.2.1 Helm chart initialized
- [X] 4.2.2 Backend deployment template
- [X] 4.2.3 Backend service template
- [X] 4.2.4 Frontend deployment template
- [X] 4.2.5 Frontend service template
- [X] 4.2.6 Ingress template
- [X] 4.2.7 ConfigMap template
- [X] 4.2.8 Secrets template
- [X] 4.2.9 Helm chart validated

### Phase 4.3: Minikube Deployment
- [X] 4.3.1 Minikube setup script
- [X] 4.3.2 Local deployment script
- [X] 4.3.3 Teardown script
- [X] 4.3.4 Deployed to Minikube
- [X] 4.3.5 Local DNS configured
- [X] 4.3.6 End-to-end testing passed
- [X] 4.3.7 Scaling tested

### Phase 4.4: AI-Ops Integration
- [X] 4.4.1 kubectl-ai installed
- [X] 4.4.2 kagent installed (optional)
- [X] 4.4.3 AI-Ops commands documented
- [X] 4.4.4 AI-Ops workflows tested

### Phase 4.5: Documentation
- [X] 4.5.1 Deployment README
- [X] 4.5.2 Project README updated
- [X] 4.5.3 Troubleshooting guide
