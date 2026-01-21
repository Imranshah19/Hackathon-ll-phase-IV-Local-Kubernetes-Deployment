# Phase 4: Local Kubernetes Deployment Guide

This guide covers deploying the Todo AI Chatbot to a local Kubernetes cluster using Minikube and Helm.

## Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Version | Installation |
|------|---------|--------------|
| Docker | 20.x+ | [Install Docker](https://docs.docker.com/get-docker/) |
| Minikube | 1.30+ | [Install Minikube](https://minikube.sigs.k8s.io/docs/start/) |
| kubectl | 1.28+ | [Install kubectl](https://kubernetes.io/docs/tasks/tools/) |
| Helm | 3.x | [Install Helm](https://helm.sh/docs/intro/install/) |

### System Requirements

- **RAM**: Minimum 8GB (4GB allocated to Minikube)
- **CPU**: Minimum 4 cores (2 allocated to Minikube)
- **Disk**: 20GB free space

## Quick Start

### 1. Setup Minikube

**Linux/macOS:**
```bash
./scripts/minikube-setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\minikube-setup.ps1
```

This will:
- Start Minikube with 4GB RAM and 2 CPUs
- Enable the ingress and metrics-server addons
- Display the Minikube IP for hosts file configuration

### 2. Configure Environment Variables

Create a `.env` file or export the following variables:

```bash
# Required: Neon PostgreSQL connection string
export DATABASE_URL="postgresql://user:password@your-host.neon.tech/dbname?sslmode=require"

# Required: JWT signing secret (min 32 characters)
export JWT_SECRET_KEY="your-super-secret-jwt-key-min-32-chars"

# Optional: OpenAI API key for AI chat features
export OPENAI_API_KEY="sk-your-openai-api-key"
```

### 3. Update Hosts File

Add the Minikube IP to your hosts file:

**Linux/macOS:** `/etc/hosts`
```
<minikube-ip>  todo.local
```

**Windows:** `C:\Windows\System32\drivers\etc\hosts` (edit as Administrator)
```
<minikube-ip>  todo.local
```

Get the Minikube IP with: `minikube ip`

### 4. Deploy the Application

**Linux/macOS:**
```bash
./scripts/deploy-local.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy-local.ps1
```

This will:
- Configure Docker to use Minikube's daemon
- Build the backend and frontend Docker images
- Deploy using Helm
- Wait for pods to be ready

### 5. Access the Application

Open your browser and navigate to:
```
http://todo.local
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MINIKUBE CLUSTER                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              NGINX INGRESS CONTROLLER                  │ │
│  │                   http://todo.local                    │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│           ┌────────────┴────────────┐                       │
│           │                         │                       │
│           ▼                         ▼                       │
│  ┌─────────────────┐     ┌─────────────────┐               │
│  │ Frontend Service│     │ Backend Service │               │
│  │   Port: 3000    │     │   Port: 8000    │               │
│  └────────┬────────┘     └────────┬────────┘               │
│           │                       │                         │
│  ┌────────▼────────┐     ┌────────▼────────┐               │
│  │  Frontend Pods  │     │  Backend Pods   │               │
│  │   (Next.js)     │     │   (FastAPI)     │               │
│  │   Replicas: 2   │     │   Replicas: 2   │               │
│  └─────────────────┘     └────────┬────────┘               │
│                                   │                         │
└───────────────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Neon PostgreSQL    │
                         │    (External)       │
                         └─────────────────────┘
```

## Configuration

### Helm Values

Override default values using `--set` or a custom values file:

```bash
# Scale replicas
helm upgrade todo-app ./helm/todo-app --set backend.replicas=3

# Use custom values file
helm upgrade todo-app ./helm/todo-app -f custom-values.yaml
```

### Available Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `backend.replicas` | 2 | Number of backend pod replicas |
| `backend.resources.requests.memory` | 256Mi | Backend memory request |
| `backend.resources.requests.cpu` | 200m | Backend CPU request |
| `frontend.replicas` | 2 | Number of frontend pod replicas |
| `frontend.resources.requests.memory` | 128Mi | Frontend memory request |
| `frontend.resources.requests.cpu` | 100m | Frontend CPU request |
| `ingress.host` | todo.local | Ingress hostname |
| `config.logLevel` | INFO | Application log level |

## Useful Commands

### Kubernetes Operations

```bash
# List all pods
kubectl get pods

# List all services
kubectl get svc

# List ingress rules
kubectl get ingress

# View backend logs
kubectl logs -l app.kubernetes.io/component=backend -f

# View frontend logs
kubectl logs -l app.kubernetes.io/component=frontend -f

# Describe a pod
kubectl describe pod <pod-name>

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/sh
```

### Helm Operations

```bash
# List releases
helm list

# View release status
helm status todo-app

# View release history
helm history todo-app

# Rollback to previous version
helm rollback todo-app 1

# Uninstall release
helm uninstall todo-app
```

### Minikube Operations

```bash
# Get Minikube IP
minikube ip

# Open Kubernetes dashboard
minikube dashboard

# SSH into Minikube VM
minikube ssh

# View Minikube logs
minikube logs

# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
```

## Scaling

### Manual Scaling

```bash
# Scale backend to 3 replicas
helm upgrade todo-app ./helm/todo-app --set backend.replicas=3

# Or use kubectl
kubectl scale deployment todo-app-backend --replicas=3
```

### Resource Monitoring

```bash
# View pod resource usage
kubectl top pods

# View node resource usage
kubectl top nodes
```

## Teardown

To remove the deployment:

**Linux/macOS:**
```bash
./scripts/teardown.sh

# To also stop Minikube:
./scripts/teardown.sh --stop-minikube
```

**Windows:**
```powershell
helm uninstall todo-app
minikube stop  # Optional
```

## Troubleshooting

### Pods Not Starting

1. Check pod status:
   ```bash
   kubectl get pods
   kubectl describe pod <pod-name>
   ```

2. Check pod logs:
   ```bash
   kubectl logs <pod-name>
   ```

3. Common issues:
   - **ImagePullBackOff**: Image not found in Minikube's Docker
   - **CrashLoopBackOff**: Application crashing (check logs)
   - **Pending**: Insufficient resources

### Ingress Not Working

1. Verify ingress addon is enabled:
   ```bash
   minikube addons list | grep ingress
   ```

2. Check ingress resource:
   ```bash
   kubectl get ingress
   kubectl describe ingress todo-app
   ```

3. Verify hosts file entry points to correct IP

### Database Connection Issues

1. Check backend logs for connection errors:
   ```bash
   kubectl logs -l app.kubernetes.io/component=backend
   ```

2. Verify DATABASE_URL secret:
   ```bash
   kubectl get secret todo-app-secrets -o yaml
   ```

3. Test database connectivity from pod:
   ```bash
   kubectl exec -it <backend-pod> -- python -c "from src.db import engine; print(engine.url)"
   ```

### Resource Constraints

If pods are being evicted or not scheduling:

1. Check Minikube resources:
   ```bash
   minikube ssh -- free -m
   ```

2. Increase Minikube resources:
   ```bash
   minikube stop
   minikube start --memory=8192 --cpus=4
   ```

## Next Steps

- [AI-Ops Guide](./ai-ops.md) - Using kubectl-ai for natural language cluster management
- [Troubleshooting Guide](./troubleshooting.md) - Detailed troubleshooting steps
