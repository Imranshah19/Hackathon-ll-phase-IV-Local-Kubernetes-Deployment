# Phase IV – Local Kubernetes Deployment

## Project: Evolution of Todo
### Phase: IV – Local Kubernetes Deployment
### Link: Phase I → Phase IV
### Objective:
Deploy the AI-powered Todo Chatbot (Phase III) on a **local Kubernetes cluster** using **Minikube**, preserving **Phase I core logic**, using **Spec-Driven Development** and **Agentic Dev Stack workflow**.

---

## 1. Constitution

- Deploy Phase III AI Todo Chatbot on **local Kubernetes (Minikube)**.
- Preserve **Phase I CLI commands**: Add, Delete, Update, View, Mark Complete.
- Use **Spec-Driven Development only**; no manual coding.
- AI DevOps via **kubectl-ai**, **kagent**, **Docker AI (Gordon)**.
- Deliverables:
  - ✅ Markdown Constitution
  - ✅ Task Plan
  - ✅ Phase IV Spec
  - ✅ Dockerfiles & Helm Charts
  - ✅ Deployment scripts
  - ✅ Verification of Todo features
  - ✅ GitHub Repo link

---

## 2. Development Plan

**Workflow:**
1. Review Phase III Chatbot architecture
2. Containerize frontend (Next.js) and backend (FastAPI)
3. Generate Helm charts
4. Deploy on Minikube
5. Monitor & scale pods using kubectl-ai & kagent
6. Test Todo features via chatbot
7. Document deployment and record demo

**Tasks:**

| Task ID | Description | Tool/Tech | Status |
|---------|------------|-----------|--------|
| T1 | Review Phase III Chatbot code & architecture | Claude Code | ✅ Done |
| T2 | Generate Dockerfiles for frontend & backend | Claude Code, Gordon | ✅ Done |
| T3 | Build Docker images locally | Docker Desktop | ✅ Done |
| T4 | Create Helm Charts for deployment | Claude Code, kubectl-ai | ✅ Done |
| T5 | Deploy on Minikube | Helm, Minikube | ✅ Done |
| T6 | Monitor pods & scale replicas | kubectl-ai, kagent | ✅ Done |
| T7 | Test core Todo features | Phase III Chatbot | ✅ Done |
| T8 | Document deployment | Markdown | ✅ Done |

---

## 3. Phase IV Spec

```yaml
version: 1.0
project: Evolution of Todo
phase: IV
description: Local Kubernetes deployment of AI-powered Todo Chatbot
workflow:
  - step: Containerization
    description: Generate Dockerfiles for frontend and backend
    inputs:
      frontend_path: ./frontend
      backend_path: ./backend
    output: Docker images (todo-frontend:phase4, todo-backend:phase4)

  - step: Helm Chart Creation
    description: Generate Helm charts for deployment
    inputs:
      frontend_image: todo-frontend:phase4
      backend_image: todo-backend:phase4
      replicas: 2
    output: helm-chart/

  - step: Minikube Deployment
    description: Deploy using Helm on local Minikube cluster
    inputs:
      cluster_name: local-todo
      helm_chart_path: helm-chart/
    output: deployed services

  - step: AIOps
    description: Monitor and scale pods
    tools: [kubectl-ai, kagent]
    metrics: [CPU, Memory, Pod Health]

  - step: Verification
    description: Test Todo core features
    expected_behavior: "Add, Delete, Update, View, Mark Complete working via chatbot"
```

---

## 4. Deliverables

### 4.1 Dockerfiles

| File | Location | Description |
|------|----------|-------------|
| Backend Dockerfile | `backend/Dockerfile` | Multi-stage production build |
| Backend Dockerfile.dev | `backend/Dockerfile.dev` | Simple development build |
| Frontend Dockerfile | `frontend/Dockerfile` | Multi-stage production build |
| Frontend Dockerfile.dev | `frontend/Dockerfile.dev` | Simple development build |

### 4.2 Helm Charts

| Chart | Location | Description |
|-------|----------|-------------|
| Full Chart | `helm/todo-app/` | Production with Ingress, ConfigMaps, Secrets, HPA |
| Simple Chart | `helm-chart/` | Basic deployments & services |

### 4.3 Deployment Scripts

| Script | Usage |
|--------|-------|
| `deploy-minikube.sh` | Linux/macOS deployment |
| `deploy-minikube.ps1` | Windows deployment |
| `deploy.sh` | Full deployment with image build |
| `deploy.ps1` | Full deployment (Windows) |

### 4.4 Documentation

| Document | Location |
|----------|----------|
| AI-Ops Guide | `docs/ai-ops.md` |
| Troubleshooting | `docs/troubleshooting.md` |
| Deployment Guide | `docs/deployment.md` |

---

## 5. Quick Start

### Prerequisites
- Docker Desktop
- Minikube
- Helm
- kubectl

### Deploy

```bash
# Windows
.\deploy-minikube.ps1

# Linux/macOS
./deploy-minikube.sh
```

### AI-Ops Commands

```bash
# Monitor with kubectl-ai
kubectl-ai "analyze cluster health"
kubectl-ai "scale backend replicas to 3"

# Optimize with kagent
kagent "optimize resource allocation"
```

---

## 6. Todo Core Features (Phase I)

| Feature | Command | Status |
|---------|---------|--------|
| Add Task | "Add a task to buy groceries" | ✅ Preserved |
| Delete Task | "Delete task 1" | ✅ Preserved |
| Update Task | "Update task 1 title to Call mom" | ✅ Preserved |
| View Tasks | "Show my tasks" | ✅ Preserved |
| Mark Complete | "Mark task 1 as done" | ✅ Preserved |

---

## 7. GitHub Repository

**URL**: https://github.com/Imranshah19/Hackathon-ll-phase-IV-Local-Kubernetes-Deployment

---

## 8. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MINIKUBE CLUSTER                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              NGINX INGRESS CONTROLLER                 │  │
│  │                  http://todo.local                    │  │
│  └─────────────────────────┬─────────────────────────────┘  │
│                            │                                │
│              ┌─────────────┴─────────────┐                  │
│              │                           │                  │
│              ▼                           ▼                  │
│    ┌─────────────────┐         ┌─────────────────┐         │
│    │ Frontend Service│         │ Backend Service │         │
│    │   Port: 3000    │         │   Port: 8000    │         │
│    └────────┬────────┘         └────────┬────────┘         │
│             │                           │                   │
│    ┌────────▼────────┐         ┌────────▼────────┐         │
│    │  Frontend Pods  │         │  Backend Pods   │         │
│    │   (Next.js)     │         │   (FastAPI)     │         │
│    │   Replicas: 2   │         │   Replicas: 2   │         │
│    └─────────────────┘         └────────┬────────┘         │
│                                         │                   │
└─────────────────────────────────────────┼───────────────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │  Neon PostgreSQL    │
                               │    (External)       │
                               └─────────────────────┘
```

---

**Version**: 1.0.0
**Last Updated**: 2026-01-26
**Status**: Complete
