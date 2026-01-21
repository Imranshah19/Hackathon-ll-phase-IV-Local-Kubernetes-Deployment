# Feature Specification: Phase 4 — Local Kubernetes Deployment

**Feature Branch**: `007-kubernetes-deployment`
**Created**: 2026-01-21
**Status**: Draft
**Input**: User description: "Phase 4 Local Kubernetes Deployment with Minikube, Helm, and AI Ops"

## Phase Objective

Evolve Phase-III Todo AI Chatbot into a locally deployed, scalable, cloud-native, containerized system using Kubernetes, Minikube, Helm, and kubectl-ai/kagent for AI-assisted operations.

**Core Motivation**:
- Decouple state from compute
- Enable container portability
- Enable zero-state servers
- Enable operational AI tooling
- Align with cloud-native micro-oriented blueprinting

The system must run fully locally via Minikube and externally talk to NEON serverless PostgreSQL.

---

## 1. System Overview

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | ChatKit + Next.js | Web UI container |
| Backend API | FastAPI + SQLModel | API container |
| AI Layer | OpenAI Agents SDK + MCP Server | AI interpretation (from Phase 3) |
| DB | Neon Serverless PostgreSQL | External managed database |
| Auth | Better Auth + JWT | Token-based authentication |
| Orchestration | Kubernetes (Minikube) | Local container orchestration |
| Packaging | Docker + Helm | Containerization and deployment |
| AI-Ops | kubectl-ai + kagent | AI-assisted Kubernetes operations |
| Traffic | Ingress + Service + Deployment | Traffic routing and load balancing |
| Config | ConfigMaps + Secrets | Configuration management |
| Logging | stdout structured logs | Centralized log aggregation |
| Storage State | DB only | Stateless compute nodes |

---

## 2. User Scenarios & Testing *(mandatory)*

### User Story 1 - Local Kubernetes Deployment (Priority: P1)

As a developer, I want to deploy the entire Todo AI Chatbot application to a local Minikube cluster using `helm install` so that I can run the full system in a production-like environment locally.

**Why this priority**: This is the core value proposition of Phase 4 - enabling cloud-native local deployment without cloud costs.

**Independent Test**: Can be fully tested by running `helm install` and verifying all pods are running and the application is accessible via ingress.

**Acceptance Scenarios**:

1. **Given** Minikube is running, **When** user runs `helm install todo-app ./helm/todo-app`, **Then** all pods (frontend, backend) start and reach Ready state within 2 minutes
2. **Given** the application is deployed, **When** user accesses `http://todo.local`, **Then** the frontend loads and connects to the backend API
3. **Given** the application is deployed, **When** user performs CRUD operations via chat, **Then** data persists to Neon PostgreSQL

---

### User Story 2 - Containerized Backend Deployment (Priority: P2)

As a developer, I want the FastAPI backend to run as a stateless container that connects to external Neon PostgreSQL so that I can scale the API independently.

**Why this priority**: Backend containerization is the foundation for Kubernetes deployment.

**Independent Test**: Can be fully tested by building the Docker image, running it locally, and verifying API endpoints respond correctly.

**Acceptance Scenarios**:

1. **Given** the Dockerfile exists, **When** user runs `docker build -t todo-backend .`, **Then** the image builds successfully with all dependencies
2. **Given** the backend container is running, **When** user calls `/health` endpoint, **Then** system returns 200 OK with database connection status
3. **Given** Neon DB credentials are provided via secrets, **When** backend starts, **Then** it connects to Neon PostgreSQL within 5 seconds

---

### User Story 3 - Containerized Frontend Deployment (Priority: P3)

As a developer, I want the Next.js frontend to run as a container that connects to the backend API service so that the UI is independently deployable.

**Why this priority**: Frontend containerization enables independent scaling and deployment.

**Independent Test**: Can be fully tested by building the Docker image, running it, and verifying the UI loads and connects to the backend.

**Acceptance Scenarios**:

1. **Given** the Dockerfile exists, **When** user runs `docker build -t todo-frontend .`, **Then** the image builds successfully
2. **Given** the frontend container is running, **When** user accesses the root URL, **Then** the chat interface loads
3. **Given** backend URL is configured via env, **When** frontend makes API calls, **Then** requests route to the backend service

---

### User Story 4 - Helm Chart Packaging (Priority: P4)

As a developer, I want all Kubernetes manifests packaged as a Helm chart so that I can deploy, upgrade, and rollback the application with single commands.

**Why this priority**: Helm provides the deployment abstraction layer for production-like operations.

**Independent Test**: Can be fully tested by running `helm lint` and `helm template` to validate chart structure.

**Acceptance Scenarios**:

1. **Given** Helm chart exists at `helm/todo-app`, **When** user runs `helm lint`, **Then** no errors are reported
2. **Given** custom values are provided, **When** user runs `helm install --set backend.replicas=3`, **Then** 3 backend pods are created
3. **Given** application is deployed, **When** user runs `helm upgrade`, **Then** pods are rolled out with zero downtime

---

### User Story 5 - AI-Assisted Kubernetes Operations (Priority: P5)

As a developer, I want to use kubectl-ai or kagent to manage the Kubernetes cluster using natural language commands so that I can operate the cluster without memorizing kubectl syntax.

**Why this priority**: AI-ops tooling aligns with the project's AI-first philosophy.

**Independent Test**: Can be fully tested by running kubectl-ai commands and verifying correct kubectl operations are executed.

**Acceptance Scenarios**:

1. **Given** kubectl-ai is installed, **When** user types "show all pods in todo namespace", **Then** kubectl-ai runs `kubectl get pods -n todo` and displays results
2. **Given** kagent is configured, **When** user asks "why is the backend pod failing?", **Then** kagent analyzes pod logs and events to provide diagnosis
3. **Given** AI-ops tools are available, **When** user says "scale backend to 5 replicas", **Then** the tool executes appropriate kubectl scale command

---

### User Story 6 - Ingress Traffic Routing (Priority: P6)

As a developer, I want ingress rules to route traffic to frontend and backend services so that I can access the application via a single domain.

**Why this priority**: Ingress provides the external access point for the application.

**Independent Test**: Can be fully tested by deploying ingress and verifying URL routing works correctly.

**Acceptance Scenarios**:

1. **Given** ingress is deployed, **When** user accesses `http://todo.local/`, **Then** traffic routes to frontend service
2. **Given** ingress is deployed, **When** user accesses `http://todo.local/api/`, **Then** traffic routes to backend service
3. **Given** Minikube ingress addon is enabled, **When** ingress resources are applied, **Then** external access is available

---

### User Story 7 - Secret Management (Priority: P7)

As a developer, I want sensitive configuration (database URL, API keys) stored as Kubernetes Secrets so that credentials are not exposed in manifests or images.

**Why this priority**: Security is essential for any production-like deployment.

**Independent Test**: Can be fully tested by verifying secrets are mounted correctly and not logged.

**Acceptance Scenarios**:

1. **Given** secrets are created, **When** pods start, **Then** environment variables are populated from secrets
2. **Given** DATABASE_URL is in secrets, **When** backend reads the variable, **Then** it connects to Neon without exposing credentials
3. **Given** secrets template exists, **When** user runs helm install with values, **Then** secrets are created from values

---

### Edge Cases

- What happens when Minikube runs out of resources? Pods enter Pending state with clear resource error messages.
- What happens when Neon PostgreSQL is unreachable? Backend pod fails health check and is marked unhealthy, but restarts automatically.
- What happens when frontend cannot reach backend? Frontend displays connection error with retry option.
- What happens when helm upgrade fails? Helm rolls back to previous release automatically.
- What happens when kubectl-ai gives incorrect command? User can review command before execution.

---

## 3. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide Dockerfiles for both frontend and backend services
- **FR-002**: System MUST provide a Helm chart for deploying all components to Kubernetes
- **FR-003**: System MUST support deployment to Minikube for local development
- **FR-004**: System MUST connect to external Neon PostgreSQL for data persistence
- **FR-005**: System MUST use Kubernetes Secrets for sensitive configuration
- **FR-006**: System MUST use ConfigMaps for non-sensitive configuration
- **FR-007**: System MUST provide Ingress resources for external traffic routing
- **FR-008**: System MUST support horizontal scaling of backend pods
- **FR-009**: System MUST maintain all Phase 3 functionality (AI chat, task CRUD)
- **FR-010**: System MUST provide health check endpoints for Kubernetes probes
- **FR-011**: System MUST output structured logs to stdout for container logging
- **FR-012**: System MUST support kubectl-ai or kagent for AI-assisted operations
- **FR-013**: System MUST be deployable with a single `helm install` command
- **FR-014**: System MUST support zero-downtime deployments via rolling updates

### Non-Functional Requirements

- **NFR-001**: Backend container MUST start and pass health check within 30 seconds
- **NFR-002**: Frontend container MUST start within 30 seconds
- **NFR-003**: Full deployment MUST complete within 2 minutes on a standard laptop
- **NFR-004**: Container images MUST be under 500MB each
- **NFR-005**: System MUST support 10 concurrent users locally
- **NFR-006**: System MUST gracefully handle Neon PostgreSQL connection failures
- **NFR-007**: System MUST have zero hardcoded secrets in images or manifests

---

## 4. Key Entities / Kubernetes Resources

### Docker Images

- **todo-backend**: FastAPI application image
  - Base: `python:3.11-slim`
  - Exposes: Port 8000
  - Health endpoint: `/health`

- **todo-frontend**: Next.js application image
  - Base: `node:20-alpine`
  - Exposes: Port 3000
  - Environment: `NEXT_PUBLIC_API_URL`

### Kubernetes Resources

- **Deployment: backend**
  - Replicas: 2 (configurable)
  - Resources: 256Mi memory, 200m CPU
  - Probes: liveness, readiness

- **Deployment: frontend**
  - Replicas: 2 (configurable)
  - Resources: 128Mi memory, 100m CPU
  - Probes: liveness, readiness

- **Service: backend-svc**
  - Type: ClusterIP
  - Port: 8000

- **Service: frontend-svc**
  - Type: ClusterIP
  - Port: 3000

- **Ingress: todo-ingress**
  - Host: todo.local
  - Rules: `/api/*` → backend, `/` → frontend

- **ConfigMap: app-config**
  - LOG_LEVEL, ENVIRONMENT, API_VERSION

- **Secret: app-secrets**
  - DATABASE_URL, JWT_SECRET, OPENAI_API_KEY

---

## 5. Architecture

### Deployment Architecture

```
                         ┌─────────────────────────────────────────┐
                         │            Minikube Cluster             │
                         │                                          │
┌──────────┐            │  ┌─────────────────────────────────┐    │
│  User    │────────────┼──│         Ingress Controller       │    │
│ Browser  │            │  │         (todo.local)             │    │
└──────────┘            │  └─────────────┬───────────────────┘    │
                         │                │                         │
                         │    ┌───────────┴───────────┐            │
                         │    │                       │            │
                         │    ▼                       ▼            │
                         │  ┌──────────┐        ┌──────────┐       │
                         │  │ Frontend │        │ Backend  │       │
                         │  │ Service  │        │ Service  │       │
                         │  └────┬─────┘        └────┬─────┘       │
                         │       │                   │              │
                         │  ┌────▼─────┐        ┌────▼─────┐       │
                         │  │ Frontend │        │ Backend  │       │
                         │  │ Pods (2) │        │ Pods (2) │       │
                         │  │ Next.js  │        │ FastAPI  │       │
                         │  └──────────┘        └────┬─────┘       │
                         │                           │              │
                         └───────────────────────────┼──────────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────┐
                                          │  Neon PostgreSQL │
                                          │  (External)      │
                                          └──────────────────┘
```

### Directory Structure (Phase 4 Additions)

```
├── backend/
│   └── Dockerfile                    # Backend container definition
├── frontend/
│   └── Dockerfile                    # Frontend container definition
├── helm/
│   └── todo-app/
│       ├── Chart.yaml               # Helm chart metadata
│       ├── values.yaml              # Default configuration values
│       └── templates/
│           ├── _helpers.tpl         # Template helpers
│           ├── backend-deployment.yaml
│           ├── backend-service.yaml
│           ├── frontend-deployment.yaml
│           ├── frontend-service.yaml
│           ├── ingress.yaml
│           ├── configmap.yaml
│           └── secrets.yaml
├── k8s/                              # Raw manifests (optional)
│   ├── namespace.yaml
│   ├── backend/
│   └── frontend/
└── scripts/
    ├── minikube-setup.sh            # Minikube initialization
    ├── deploy-local.sh              # Local deployment script
    └── teardown.sh                  # Cleanup script
```

---

## 6. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Full application deploys to Minikube within 2 minutes via `helm install`
- **SC-002**: All pods reach Ready state and pass health checks
- **SC-003**: Users can access the application at `http://todo.local`
- **SC-004**: All Phase 3 AI chat functionality works in containerized environment
- **SC-005**: Backend connects to Neon PostgreSQL successfully
- **SC-006**: Zero secrets exposed in container images or manifests
- **SC-007**: kubectl-ai/kagent can perform basic cluster operations
- **SC-008**: Rolling updates complete with zero downtime

---

## 7. Assumptions

- Developer has Docker Desktop or Docker Engine installed
- Developer has Minikube installed and configured
- Developer has Helm 3.x installed
- Developer has kubectl installed and configured
- Neon PostgreSQL account exists with database provisioned
- OpenAI API key is available for AI features
- Minimum 8GB RAM available for Minikube
- Minimum 4 CPU cores available

---

## 8. Out of Scope

- Production cloud deployment (AWS EKS, GKE, AKS)
- SSL/TLS termination (HTTPS)
- Horizontal Pod Autoscaler (HPA)
- Persistent Volume Claims (PVC) - using external DB
- Service Mesh (Istio, Linkerd)
- Monitoring stack (Prometheus, Grafana)
- CI/CD pipeline integration
- Multi-cluster deployment

---

## 9. Dependencies

- Phase 3 completion (AI Chat Layer)
- Neon PostgreSQL connection string
- OpenAI API key for AI features
- Local development machine with sufficient resources
