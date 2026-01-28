# Quickstart: Phase 5 Advanced Features

**Feature**: 008-phase5-advanced-features
**Date**: 2026-01-28

---

## Prerequisites

- Docker Desktop installed
- Minikube running (from Phase 4)
- Dapr CLI installed: `brew install dapr/tap/dapr-cli` or `winget install Dapr.CLI`
- Helm 3.x installed
- Access to Neon PostgreSQL database
- OpenAI API key (for AI chat)

## Local Development Setup

### 1. Initialize Dapr

```bash
# Initialize Dapr (one-time)
dapr init

# Verify Dapr is running
dapr --version
docker ps | grep dapr
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values:
# DATABASE_URL=postgresql://...@neon.tech/todo
# OPENAI_API_KEY=sk-...
# JWT_SECRET=your-secret-key
```

### 3. Run Database Migrations

```bash
cd backend

# Create new tables (Phase 5)
alembic upgrade head

# Verify tables created
# - tag, task_tag, reminder, recurrence_rule, task_event
# - task table has new columns: priority, recurrence_rule_id, parent_task_id
```

### 4. Start Backend with Dapr

```bash
cd backend

# Run with Dapr sidecar
dapr run --app-id todo-backend \
         --app-port 8000 \
         --dapr-http-port 3500 \
         --resources-path ../dapr/components \
         -- uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 6. Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

---

## Kubernetes Deployment (Minikube)

### 1. Start Minikube with Dapr

```bash
# Start Minikube (if not running)
minikube start --memory=4096 --cpus=4

# Install Dapr on Kubernetes
dapr init -k

# Verify Dapr pods
kubectl get pods -n dapr-system
```

### 2. Deploy Kafka (Local Dev)

```bash
# Add Bitnami repo
helm repo add bitnami https://charts.bitnami.com/bitnami

# Install Kafka
helm install kafka bitnami/kafka \
  --set replicaCount=1 \
  --set persistence.size=1Gi \
  --namespace todo-app \
  --create-namespace

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kafka -n todo-app --timeout=300s
```

### 3. Deploy Application

```bash
# Configure Minikube Docker environment
eval $(minikube docker-env)

# Build images
docker build -t todo-backend:phase5 ./backend
docker build -t todo-frontend:phase5 ./frontend

# Deploy with Helm
helm upgrade --install todo-app ./helm/todo-app \
  --namespace todo-app \
  --set backend.image.tag=phase5 \
  --set frontend.image.tag=phase5 \
  --set dapr.enabled=true \
  -f ./helm/todo-app/values-phase5.yaml
```

### 4. Configure Local DNS

```bash
# Get Minikube IP
minikube ip

# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
# <minikube-ip> todo.local
```

### 5. Access Application

```bash
# Open in browser
minikube service todo-frontend -n todo-app --url
```

---

## DigitalOcean Deployment

### 1. Create DOKS Cluster

```bash
# Install doctl
brew install doctl  # or appropriate package manager

# Authenticate
doctl auth init

# Create cluster
doctl kubernetes cluster create todo-cluster \
  --region nyc1 \
  --node-pool "name=default;size=s-2vcpu-4gb;count=3"

# Get kubeconfig
doctl kubernetes cluster kubeconfig save todo-cluster
```

### 2. Install Dapr on DOKS

```bash
# Install Dapr
dapr init -k --wait

# Verify
kubectl get pods -n dapr-system
```

### 3. Deploy Kafka (Production)

```bash
# Install Kafka with replication
helm install kafka bitnami/kafka \
  --set replicaCount=3 \
  --set persistence.size=10Gi \
  --set zookeeper.replicaCount=3 \
  --namespace todo-app \
  --create-namespace
```

### 4. Create Container Registry

```bash
# Create registry
doctl registry create todo-registry

# Login to registry
doctl registry login

# Tag and push images
docker tag todo-backend:phase5 registry.digitalocean.com/todo-registry/backend:phase5
docker tag todo-frontend:phase5 registry.digitalocean.com/todo-registry/frontend:phase5
docker push registry.digitalocean.com/todo-registry/backend:phase5
docker push registry.digitalocean.com/todo-registry/frontend:phase5
```

### 5. Deploy to DOKS

```bash
# Create image pull secret
kubectl create secret docker-registry do-registry \
  --docker-server=registry.digitalocean.com \
  --docker-username=<token> \
  --docker-password=<token> \
  -n todo-app

# Deploy
helm upgrade --install todo-app ./helm/todo-app \
  --namespace todo-app \
  --set backend.image.repository=registry.digitalocean.com/todo-registry/backend \
  --set backend.image.tag=phase5 \
  --set frontend.image.repository=registry.digitalocean.com/todo-registry/frontend \
  --set frontend.image.tag=phase5 \
  --set ingress.hosts[0].host=todo.yourdomain.com \
  --set dapr.enabled=true \
  -f ./helm/todo-app/values-production.yaml
```

---

## Testing Phase 5 Features

### Test Priority and Tags

```bash
# Create task with priority
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Urgent task", "priority": 1}'

# Create tag
curl -X POST http://localhost:8000/api/v1/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "work", "color": "#EF4444"}'

# Filter by priority
curl "http://localhost:8000/api/v1/tasks?priority=1-2&sort_by=priority" \
  -H "Authorization: Bearer $TOKEN"
```

### Test Recurring Tasks

```bash
# Create recurring task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Daily standup",
    "recurrence": {
      "frequency": "daily",
      "interval": 1,
      "end_type": "never"
    }
  }'

# Complete (should create next instance)
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/complete \
  -H "Authorization: Bearer $TOKEN"
```

### Test Reminders

```bash
# Add reminder
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/reminders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"remind_at": "2026-01-28T15:00:00Z"}'

# Listen for notifications (SSE)
curl -N http://localhost:8000/api/v1/reminders/stream \
  -H "Authorization: Bearer $TOKEN"
```

### Test Urdu Chat

```bash
# Send Urdu command
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "نیا کام شامل کرو: دودھ خریدنا"}'

# Expected: Task created with Urdu response
```

### Verify Events

```bash
# Check Kafka topic (if Kafka CLI available)
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic todo.task.events --from-beginning

# Or check task_event table
psql $DATABASE_URL -c "SELECT * FROM task_event ORDER BY created_at DESC LIMIT 5;"
```

---

## Troubleshooting

### Dapr Issues

```bash
# Check Dapr sidecar logs
kubectl logs <pod-name> -c daprd -n todo-app

# Verify Dapr components
dapr components -k -n todo-app
```

### Kafka Issues

```bash
# Check Kafka logs
kubectl logs kafka-0 -n todo-app

# Verify topic exists
kubectl exec -it kafka-0 -n todo-app -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list
```

### Database Issues

```bash
# Verify connection from pod
kubectl exec -it <backend-pod> -n todo-app -- \
  python -c "from src.db import engine; print(engine.url)"

# Check migrations
kubectl exec -it <backend-pod> -n todo-app -- \
  alembic current
```
