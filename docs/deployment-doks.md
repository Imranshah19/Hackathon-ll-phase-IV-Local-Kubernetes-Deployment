# Deploying Todo App to DigitalOcean Kubernetes (DOKS)

This guide covers deploying the AI-Powered Todo Chatbot to DigitalOcean Kubernetes Service (DOKS) with CI/CD via GitHub Actions.

## Prerequisites

- DigitalOcean account with billing enabled
- GitHub repository with Actions enabled
- Domain name (optional, for custom domain)
- `doctl` CLI installed locally

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DigitalOcean Cloud                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────────────────────────┐    │
│  │   DOCR      │    │         DOKS Cluster                │    │
│  │  Registry   │───▶│  ┌──────────┐    ┌──────────┐      │    │
│  │             │    │  │ Backend  │    │ Frontend │      │    │
│  │ - backend   │    │  │ (3 pods) │    │ (2 pods) │      │    │
│  │ - frontend  │    │  └────┬─────┘    └────┬─────┘      │    │
│  └─────────────┘    │       │               │            │    │
│                     │       └───────┬───────┘            │    │
│                     │               │                    │    │
│                     │        ┌──────▼──────┐             │    │
│                     │        │   Ingress   │             │    │
│                     │        │ (nginx/LB)  │             │    │
│                     │        └──────┬──────┘             │    │
│                     └───────────────┼────────────────────┘    │
│                                     │                          │
└─────────────────────────────────────┼──────────────────────────┘
                                      │
                              ┌───────▼───────┐
                              │   Internet    │
                              │  (Users)      │
                              └───────────────┘

External Services:
  - Neon PostgreSQL (managed database)
  - OpenAI API (AI features)
```

## Step 1: Create DigitalOcean Resources

### 1.1 Create Kubernetes Cluster

```bash
# Create a DOKS cluster
doctl kubernetes cluster create todo-cluster \
  --region nyc1 \
  --node-pool "name=default;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=2;max-nodes=5" \
  --version latest

# Save kubeconfig
doctl kubernetes cluster kubeconfig save todo-cluster
```

### 1.2 Create Container Registry

```bash
# Create DOCR registry
doctl registry create todo-app-registry

# Login to registry
doctl registry login
```

### 1.3 Install NGINX Ingress Controller

```bash
# Install via Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.publishService.enabled=true
```

### 1.4 Install Cert-Manager (Optional - for TLS)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 1.5 Install Dapr (Optional - for Event-Driven Features)

```bash
# Install Dapr CLI
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash

# Initialize Dapr on the cluster
dapr init -k
```

## Step 2: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Description |
|-------------|-------------|
| `DIGITALOCEAN_ACCESS_TOKEN` | DO API token with read/write access |
| `DOKS_CLUSTER_NAME` | Kubernetes cluster name (e.g., `todo-cluster`) |
| `DOCR_REGISTRY` | Container registry name (e.g., `todo-app-registry`) |
| `NEON_DB_URL` | Neon PostgreSQL connection string |
| `OPENAI_API_KEY` | OpenAI API key |
| `AUTH_SECRET` | JWT signing secret (min 32 characters) |
| `NEXT_DOMAIN_KEY` | Next.js domain key |

### Generate Secrets

```bash
# Generate AUTH_SECRET (32+ characters)
openssl rand -base64 32

# Get Neon connection string from Neon dashboard
# Format: postgresql://user:password@host/database?sslmode=require
```

## Step 3: Configure Domain (Optional)

### 3.1 Get Load Balancer IP

```bash
# After deploying, get the external IP
kubectl get svc -n ingress-nginx nginx-ingress-ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### 3.2 Configure DNS

Add an A record pointing to the Load Balancer IP:
- **Type**: A
- **Name**: todo (or @ for root)
- **Value**: [Load Balancer IP]
- **TTL**: 300

### 3.3 Update values-production.yaml

```yaml
ingress:
  host: todo.yourdomain.com
  tls:
    - secretName: todo-app-tls
      hosts:
        - todo.yourdomain.com
```

## Step 4: Deploy

### Automatic Deployment (CI/CD)

Push to `main` branch to trigger automatic deployment:

```bash
git push origin main
```

The GitHub Actions workflow will:
1. Build Docker images
2. Push to DOCR
3. Deploy to DOKS via Helm
4. Run smoke tests

### Manual Deployment

```bash
# Build and push images manually
docker build -t registry.digitalocean.com/todo-app-registry/todo-backend:latest ./backend
docker build -t registry.digitalocean.com/todo-app-registry/todo-frontend:latest ./frontend

doctl registry login
docker push registry.digitalocean.com/todo-app-registry/todo-backend:latest
docker push registry.digitalocean.com/todo-app-registry/todo-frontend:latest

# Deploy with Helm
helm upgrade --install todo-app ./helm/todo-app \
  --namespace todo-app \
  --create-namespace \
  --values ./helm/todo-app/values-production.yaml \
  --set secrets.neonDbUrl="$NEON_DB_URL" \
  --set secrets.openaiApiKey="$OPENAI_API_KEY" \
  --set secrets.authSecret="$AUTH_SECRET" \
  --set ingress.host="todo.yourdomain.com"
```

## Step 5: Verify Deployment

### Check Pod Status

```bash
kubectl get pods -n todo-app
kubectl get svc -n todo-app
kubectl get ingress -n todo-app
```

### View Logs

```bash
# Backend logs
kubectl logs -f -l app.kubernetes.io/component=backend -n todo-app

# Frontend logs
kubectl logs -f -l app.kubernetes.io/component=frontend -n todo-app
```

### Run Smoke Tests

```bash
./scripts/smoke-test.sh https://todo.yourdomain.com
```

## Step 6: Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment todo-app-backend --replicas=5 -n todo-app

# Scale frontend
kubectl scale deployment todo-app-frontend --replicas=3 -n todo-app
```

### HPA (Automatic Scaling)

HPA is enabled in production values. View status:

```bash
kubectl get hpa -n todo-app
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n todo-app

# Check secrets are created
kubectl get secrets -n todo-app
```

### Database Connection Issues

```bash
# Verify DATABASE_URL secret
kubectl get secret todo-app-secret -n todo-app -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Check backend logs for connection errors
kubectl logs -l app.kubernetes.io/component=backend -n todo-app | grep -i database
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress todo-app-ingress -n todo-app

# Verify nginx ingress controller
kubectl get pods -n ingress-nginx
```

### Rollback

```bash
# Rollback to previous release
helm rollback todo-app -n todo-app

# View release history
helm history todo-app -n todo-app
```

## Cost Estimation

| Resource | Size | Monthly Cost (approx) |
|----------|------|----------------------|
| DOKS Cluster (3 nodes) | s-2vcpu-4gb | $36 × 3 = $108 |
| Load Balancer | Standard | $12 |
| Container Registry | Basic | $5 |
| **Total** | | **~$125/month** |

Note: Neon PostgreSQL and OpenAI API costs are separate.

## Security Checklist

- [ ] Secrets stored in GitHub Secrets (not in code)
- [ ] TLS enabled via cert-manager
- [ ] Network policies configured
- [ ] RBAC configured for service account
- [ ] Pod security policies enabled
- [ ] Image scanning enabled in DOCR
- [ ] Audit logging enabled

## Next Steps

1. Set up monitoring with DigitalOcean Monitoring or Prometheus
2. Configure backup strategy for Neon database
3. Set up alerting for critical metrics
4. Implement blue-green deployments
5. Add custom domain and SSL certificate
