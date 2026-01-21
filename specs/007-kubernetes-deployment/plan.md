# Implementation Plan: Phase 4 — Local Kubernetes Deployment

**Feature**: 007-kubernetes-deployment
**Created**: 2026-01-21
**Status**: Draft
**Spec Reference**: [spec.md](./spec.md)

---

## 1. Architecture Overview

### Deployment Model

Phase 4 transforms the Phase 3 application into a cloud-native, containerized deployment without modifying business logic. The architecture follows the **stateless compute + external state** pattern.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MINIKUBE CLUSTER                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 INGRESS CONTROLLER                        │  │
│  │                 (NGINX - todo.local)                      │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│           ┌───────────────┴───────────────┐                    │
│           │                               │                    │
│           ▼                               ▼                    │
│  ┌─────────────────┐           ┌─────────────────┐            │
│  │ Frontend Service│           │ Backend Service │            │
│  │   (ClusterIP)   │           │   (ClusterIP)   │            │
│  │    Port 3000    │           │    Port 8000    │            │
│  └────────┬────────┘           └────────┬────────┘            │
│           │                             │                      │
│  ┌────────▼────────┐           ┌────────▼────────┐            │
│  │Frontend Deployment          │Backend Deployment│            │
│  │  ┌─────┐ ┌─────┐│           │  ┌─────┐ ┌─────┐│            │
│  │  │Pod 1│ │Pod 2││           │  │Pod 1│ │Pod 2││            │
│  │  │Next │ │Next ││           │  │Fast │ │Fast ││            │
│  │  │.js  │ │.js  ││           │  │API  │ │API  ││            │
│  │  └─────┘ └─────┘│           │  └─────┘ └─────┘│            │
│  └──────────────────┘           └────────┬────────┘            │
│                                          │                      │
│  ┌──────────────┐  ┌──────────────┐      │                     │
│  │  ConfigMap   │  │   Secrets    │      │                     │
│  │  (app-config)│  │ (app-secrets)│      │                     │
│  └──────────────┘  └──────────────┘      │                     │
│                                          │                      │
└──────────────────────────────────────────┼──────────────────────┘
                                           │
                                           ▼
                               ┌─────────────────────┐
                               │  NEON PostgreSQL    │
                               │  (External Cloud)   │
                               │  *.neon.tech        │
                               └─────────────────────┘
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Local Cluster | Minikube | Widely supported, easy setup, production-like |
| Package Manager | Helm 3 | Industry standard, supports templating and values |
| Ingress Controller | NGINX | Default for Minikube, well documented |
| Database Location | External (Neon) | Stateless compute, no PVC complexity |
| Image Registry | Local | Minikube's built-in Docker daemon |
| Replica Count | 2 per service | Basic HA, demonstrates scaling |

---

## 2. Component Breakdown

### 2.1 Docker Images

#### Backend Dockerfile Strategy

```dockerfile
# Multi-stage build for smaller image
# Stage 1: Dependencies
FROM python:3.11-slim as builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ ./src/
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Points**:
- Multi-stage build reduces final image size
- Only production dependencies included
- Health endpoint at `/health` for Kubernetes probes
- Environment variables for all configuration

#### Frontend Dockerfile Strategy

```dockerfile
# Multi-stage build
# Stage 1: Build
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
EXPOSE 3000
CMD ["npm", "start"]
```

**Key Points**:
- Build-time dependencies excluded from runtime
- Static assets pre-built
- API URL configured via environment variable

### 2.2 Helm Chart Structure

```
helm/todo-app/
├── Chart.yaml              # name, version, appVersion
├── values.yaml             # Default configuration
├── values-dev.yaml         # Development overrides
├── templates/
│   ├── _helpers.tpl        # Common labels, names
│   ├── namespace.yaml      # Optional: dedicated namespace
│   ├── configmap.yaml      # Non-sensitive config
│   ├── secrets.yaml        # Sensitive config (base64)
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   └── ingress.yaml
└── .helmignore
```

### 2.3 Kubernetes Resources

#### Deployments

**Backend Deployment**:
- Image: `todo-backend:latest`
- Replicas: 2 (configurable)
- Resources: 256Mi memory, 200m CPU (requests)
- Probes:
  - Liveness: `GET /health` every 10s
  - Readiness: `GET /health` every 5s
- Environment from ConfigMap + Secrets

**Frontend Deployment**:
- Image: `todo-frontend:latest`
- Replicas: 2 (configurable)
- Resources: 128Mi memory, 100m CPU (requests)
- Probes:
  - Liveness: `GET /` every 10s
  - Readiness: `GET /` every 5s
- Environment: `NEXT_PUBLIC_API_URL`

#### Services

| Service | Type | Port | Target |
|---------|------|------|--------|
| backend-svc | ClusterIP | 8000 | backend pods |
| frontend-svc | ClusterIP | 3000 | frontend pods |

#### Ingress Rules

```yaml
rules:
  - host: todo.local
    http:
      paths:
        - path: /api
          pathType: Prefix
          backend:
            service:
              name: backend-svc
              port: 8000
        - path: /
          pathType: Prefix
          backend:
            service:
              name: frontend-svc
              port: 3000
```

#### ConfigMap

```yaml
data:
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "development"
  API_VERSION: "v1"
```

#### Secrets

```yaml
data:
  DATABASE_URL: <base64>     # Neon connection string
  JWT_SECRET: <base64>       # Authentication secret
  OPENAI_API_KEY: <base64>   # AI features
```

---

## 3. Implementation Phases

### Phase 4.1: Docker Containerization

**Goal**: Create production-ready Docker images for both services.

**Tasks**:
1. Create backend Dockerfile with multi-stage build
2. Add health endpoint to FastAPI if not exists
3. Create frontend Dockerfile with multi-stage build
4. Test images locally with docker-compose
5. Document build and run commands

**Verification**:
- `docker build` succeeds for both images
- `docker run` starts containers correctly
- Health endpoints respond with 200

### Phase 4.2: Helm Chart Development

**Goal**: Package Kubernetes manifests as reusable Helm chart.

**Tasks**:
1. Initialize Helm chart structure
2. Create deployment templates for backend and frontend
3. Create service templates
4. Create ingress template
5. Create configmap and secrets templates
6. Add helper functions for common labels
7. Define values.yaml with sensible defaults
8. Run `helm lint` to validate

**Verification**:
- `helm lint` passes
- `helm template` generates valid YAML
- All resources have correct labels and selectors

### Phase 4.3: Minikube Deployment

**Goal**: Deploy and test full application on local Minikube cluster.

**Tasks**:
1. Create Minikube setup script
2. Enable ingress addon
3. Configure docker-env for local images
4. Build images in Minikube's Docker
5. Deploy with helm install
6. Add todo.local to /etc/hosts
7. Test all functionality

**Verification**:
- All pods reach Ready state
- Ingress routes traffic correctly
- Application functions as in Phase 3
- Data persists to Neon PostgreSQL

### Phase 4.4: AI-Ops Integration

**Goal**: Enable AI-assisted Kubernetes operations.

**Tasks**:
1. Install and configure kubectl-ai
2. Install and configure kagent (optional)
3. Document common AI-ops commands
4. Test natural language cluster operations

**Verification**:
- kubectl-ai responds to natural language queries
- Basic cluster operations work via AI commands

---

## 4. Configuration Management

### Environment Variables

| Variable | Location | Description |
|----------|----------|-------------|
| DATABASE_URL | Secret | Neon PostgreSQL connection |
| JWT_SECRET | Secret | Authentication signing key |
| OPENAI_API_KEY | Secret | AI features API key |
| LOG_LEVEL | ConfigMap | Logging verbosity |
| ENVIRONMENT | ConfigMap | Deployment environment |
| NEXT_PUBLIC_API_URL | Frontend env | Backend API URL |

### Values.yaml Structure

```yaml
# Global settings
namespace: todo

# Backend configuration
backend:
  image:
    repository: todo-backend
    tag: latest
    pullPolicy: IfNotPresent
  replicas: 2
  resources:
    requests:
      memory: "256Mi"
      cpu: "200m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  service:
    port: 8000

# Frontend configuration
frontend:
  image:
    repository: todo-frontend
    tag: latest
    pullPolicy: IfNotPresent
  replicas: 2
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "250m"
  service:
    port: 3000

# Ingress configuration
ingress:
  enabled: true
  host: todo.local
  annotations:
    kubernetes.io/ingress.class: nginx

# Secrets (provide via --set or separate values file)
secrets:
  databaseUrl: ""
  jwtSecret: ""
  openaiApiKey: ""
```

---

## 5. Deployment Scripts

### minikube-setup.sh

```bash
#!/bin/bash
# Initialize Minikube with required resources
minikube start --memory=4096 --cpus=2 --driver=docker
minikube addons enable ingress
minikube addons enable metrics-server

# Configure local Docker to use Minikube's daemon
eval $(minikube docker-env)

echo "Minikube ready. Run: minikube ip"
```

### deploy-local.sh

```bash
#!/bin/bash
# Build images and deploy to Minikube

# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build images
docker build -t todo-backend:latest ./backend
docker build -t todo-frontend:latest ./frontend

# Deploy with Helm
helm upgrade --install todo-app ./helm/todo-app \
  --set secrets.databaseUrl="$DATABASE_URL" \
  --set secrets.jwtSecret="$JWT_SECRET" \
  --set secrets.openaiApiKey="$OPENAI_API_KEY"

# Wait for pods
kubectl wait --for=condition=ready pod -l app=todo-backend --timeout=120s
kubectl wait --for=condition=ready pod -l app=todo-frontend --timeout=120s

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Add to /etc/hosts: $MINIKUBE_IP todo.local"
```

### teardown.sh

```bash
#!/bin/bash
# Clean up deployment
helm uninstall todo-app
minikube stop
```

---

## 6. Testing Strategy

### Local Testing (Pre-Kubernetes)

1. **Docker Compose Test**:
   ```yaml
   services:
     backend:
       build: ./backend
       ports: ["8000:8000"]
       environment:
         DATABASE_URL: ${DATABASE_URL}
     frontend:
       build: ./frontend
       ports: ["3000:3000"]
       environment:
         NEXT_PUBLIC_API_URL: http://localhost:8000
   ```

2. **Image Verification**:
   - Build succeeds
   - Container starts
   - Health endpoint responds
   - API endpoints work

### Kubernetes Testing

1. **Deployment Verification**:
   - All pods in Ready state
   - No restart loops
   - Resource limits respected

2. **Service Verification**:
   - Service endpoints populated
   - Port forwarding works
   - Inter-pod communication

3. **Ingress Verification**:
   - Host routing works
   - Path routing works
   - SSL termination (if configured)

4. **End-to-End Testing**:
   - User registration/login
   - Task CRUD via UI
   - AI chat functionality
   - Data persists across pod restarts

---

## 7. Rollback Strategy

### Helm Rollback

```bash
# List releases
helm history todo-app

# Rollback to previous
helm rollback todo-app 1

# Rollback to specific revision
helm rollback todo-app <revision>
```

### Manual Rollback

```bash
# Scale down new version
kubectl scale deployment backend --replicas=0

# Apply previous manifests
kubectl apply -f k8s/backend-deployment-v1.yaml
```

---

## 8. Monitoring & Observability

### Structured Logging

All containers output JSON logs to stdout:
```json
{
  "timestamp": "2026-01-21T10:00:00Z",
  "level": "INFO",
  "message": "Request processed",
  "path": "/api/tasks",
  "method": "GET",
  "duration_ms": 45
}
```

### Kubernetes Native Monitoring

```bash
# Pod logs
kubectl logs -l app=todo-backend -f

# Resource usage
kubectl top pods

# Events
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## 9. Security Considerations

1. **Secrets Management**:
   - All secrets in Kubernetes Secrets
   - Never in ConfigMaps or images
   - Consider external secrets operator for production

2. **Network Policies** (future):
   - Backend only accessible from frontend and ingress
   - No direct external access to backend

3. **Image Security**:
   - Minimal base images (slim/alpine)
   - No root user in containers
   - Regular security scans

---

## 10. Known Limitations

1. **Development Only**: This setup is for local development, not production
2. **No HTTPS**: TLS termination not configured
3. **No HPA**: Manual scaling only
4. **No PVC**: Relies on external database
5. **Single Cluster**: No multi-cluster support

---

## 11. Constitution Compliance

| Principle | Compliance |
|-----------|------------|
| I. Spec-First | Plan written before implementation |
| II. Layered Architecture | Containers maintain layer separation |
| III. Test-First | Testing strategy defined |
| IV. Secure by Design | Secrets managed securely |
| V. API-First | No API changes |
| VI. Minimal Viable Diff | Only packaging changes |
| VII. AI as Interpreter | AI-Ops for operations only |
| VIII. Backward Compatibility | Phase 3 code unchanged |
| IX. Intent Preservation | N/A (no AI interpretation) |
| X. Graceful Degradation | Pods restart on failure |

---

## 12. Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Minikube resource limits | Medium | Document minimum requirements |
| Neon connection failures | High | Health checks, retry logic |
| Image size too large | Low | Multi-stage builds |
| Ingress misconfiguration | Medium | Helm lint, testing |
| Secret exposure | High | Kubernetes Secrets, no hardcoding |

---

## Next Steps

After plan approval:
1. Generate tasks.md with implementation breakdown
2. Create backend Dockerfile
3. Create frontend Dockerfile
4. Initialize Helm chart
5. Create Kubernetes templates
6. Write deployment scripts
7. Test on Minikube
8. Document AI-Ops usage
