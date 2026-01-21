# Data Model: Phase 4 — Kubernetes Resources

**Feature**: 007-kubernetes-deployment
**Created**: 2026-01-21
**Status**: Draft

---

## Overview

Phase 4 introduces Kubernetes resources for container orchestration. This document defines the structure and relationships of all Kubernetes objects used in the deployment.

---

## 1. Docker Images

### todo-backend

```yaml
Image: todo-backend:latest
Base: python:3.11-slim
Size Target: < 300MB
Ports: 8000
Labels:
  app: todo-backend
  version: "1.0.0"
  phase: "4"
Environment:
  - DATABASE_URL (from Secret)
  - JWT_SECRET (from Secret)
  - OPENAI_API_KEY (from Secret)
  - LOG_LEVEL (from ConfigMap)
  - ENVIRONMENT (from ConfigMap)
Health:
  - Endpoint: GET /health
  - Expected: {"status": "healthy", "database": "connected"}
```

### todo-frontend

```yaml
Image: todo-frontend:latest
Base: node:20-alpine
Size Target: < 200MB
Ports: 3000
Labels:
  app: todo-frontend
  version: "1.0.0"
  phase: "4"
Environment:
  - NEXT_PUBLIC_API_URL
Health:
  - Endpoint: GET /
  - Expected: HTTP 200 with HTML
```

---

## 2. Kubernetes Resources

### 2.1 Namespace (Optional)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/part-of: todo-system
```

### 2.2 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: todo-config
  namespace: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/component: config
data:
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "development"
  API_VERSION: "v1"
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| LOG_LEVEL | string | INFO | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| ENVIRONMENT | string | development | Runtime environment identifier |
| API_VERSION | string | v1 | API version string |

### 2.3 Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: todo-secrets
  namespace: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/component: secrets
type: Opaque
data:
  DATABASE_URL: <base64-encoded>
  JWT_SECRET: <base64-encoded>
  OPENAI_API_KEY: <base64-encoded>
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| DATABASE_URL | string | Yes | Neon PostgreSQL connection string |
| JWT_SECRET | string | Yes | JWT signing secret (min 32 chars) |
| OPENAI_API_KEY | string | Yes | OpenAI API key for AI features |

### 2.4 Backend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-backend
  namespace: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/component: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: todo-backend
  template:
    metadata:
      labels:
        app: todo-backend
        app.kubernetes.io/name: todo-app
        app.kubernetes.io/component: backend
    spec:
      containers:
        - name: backend
          image: todo-backend:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
              name: http
              protocol: TCP
          resources:
            requests:
              memory: "256Mi"
              cpu: "200m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          envFrom:
            - configMapRef:
                name: todo-config
            - secretRef:
                name: todo-secrets
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| replicas | int | 2 | Number of pod instances |
| image | string | todo-backend:latest | Container image |
| resources.requests.memory | string | 256Mi | Memory request |
| resources.requests.cpu | string | 200m | CPU request |
| resources.limits.memory | string | 512Mi | Memory limit |
| resources.limits.cpu | string | 500m | CPU limit |

### 2.5 Backend Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: todo-backend-svc
  namespace: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/component: backend
spec:
  type: ClusterIP
  selector:
    app: todo-backend
  ports:
    - name: http
      port: 8000
      targetPort: 8000
      protocol: TCP
```

| Field | Type | Value | Description |
|-------|------|-------|-------------|
| type | string | ClusterIP | Internal-only service |
| port | int | 8000 | Service port |
| targetPort | int | 8000 | Container port |

### 2.6 Frontend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-frontend
  namespace: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/component: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: todo-frontend
  template:
    metadata:
      labels:
        app: todo-frontend
        app.kubernetes.io/name: todo-app
        app.kubernetes.io/component: frontend
    spec:
      containers:
        - name: frontend
          image: todo-frontend:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 3000
              name: http
              protocol: TCP
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "250m"
          env:
            - name: NEXT_PUBLIC_API_URL
              value: "http://todo-backend-svc:8000"
          livenessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| replicas | int | 2 | Number of pod instances |
| image | string | todo-frontend:latest | Container image |
| resources.requests.memory | string | 128Mi | Memory request |
| resources.requests.cpu | string | 100m | CPU request |
| resources.limits.memory | string | 256Mi | Memory limit |
| resources.limits.cpu | string | 250m | CPU limit |

### 2.7 Frontend Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: todo-frontend-svc
  namespace: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/component: frontend
spec:
  type: ClusterIP
  selector:
    app: todo-frontend
  ports:
    - name: http
      port: 3000
      targetPort: 3000
      protocol: TCP
```

### 2.8 Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-ingress
  namespace: todo
  labels:
    app.kubernetes.io/name: todo-app
    app.kubernetes.io/component: ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - host: todo.local
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: todo-backend-svc
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: todo-frontend-svc
                port:
                  number: 3000
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| host | string | todo.local | Ingress hostname |
| paths[0].path | string | /api | Backend API path prefix |
| paths[1].path | string | / | Frontend catch-all path |

---

## 3. Helm Values Schema

```yaml
# values.yaml schema

# Global settings
namespace: todo                          # Kubernetes namespace

# Backend configuration
backend:
  enabled: true                          # Deploy backend
  image:
    repository: todo-backend             # Image name
    tag: latest                          # Image tag
    pullPolicy: IfNotPresent             # Pull policy
  replicas: 2                            # Pod replicas
  resources:
    requests:
      memory: "256Mi"
      cpu: "200m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  service:
    type: ClusterIP
    port: 8000
  probes:
    liveness:
      path: /health
      initialDelaySeconds: 15
      periodSeconds: 10
    readiness:
      path: /health
      initialDelaySeconds: 5
      periodSeconds: 5

# Frontend configuration
frontend:
  enabled: true                          # Deploy frontend
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
    type: ClusterIP
    port: 3000
  probes:
    liveness:
      path: /
      initialDelaySeconds: 15
      periodSeconds: 10
    readiness:
      path: /
      initialDelaySeconds: 5
      periodSeconds: 5

# Ingress configuration
ingress:
  enabled: true
  className: nginx
  host: todo.local
  annotations: {}
  tls: []

# Configuration
config:
  logLevel: INFO
  environment: development
  apiVersion: v1

# Secrets (provide via --set or external)
secrets:
  databaseUrl: ""                        # Required
  jwtSecret: ""                          # Required
  openaiApiKey: ""                       # Required
```

---

## 4. Resource Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                      KUBERNETES CLUSTER                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    NAMESPACE: todo                   │   │
│  │                                                      │   │
│  │  ┌──────────────┐      ┌──────────────┐            │   │
│  │  │  ConfigMap   │      │    Secret    │            │   │
│  │  │ (todo-config)│      │(todo-secrets)│            │   │
│  │  └──────┬───────┘      └──────┬───────┘            │   │
│  │         │                     │                     │   │
│  │         └─────────┬───────────┘                     │   │
│  │                   │                                  │   │
│  │                   ▼                                  │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │           BACKEND DEPLOYMENT               │    │   │
│  │  │  ┌─────────┐  ┌─────────┐                 │    │   │
│  │  │  │  Pod 1  │  │  Pod 2  │  (envFrom)     │    │   │
│  │  │  └────┬────┘  └────┬────┘                 │    │   │
│  │  └───────┼────────────┼──────────────────────┘    │   │
│  │          │            │                            │   │
│  │          └─────┬──────┘                            │   │
│  │                ▼                                   │   │
│  │  ┌────────────────────────┐                       │   │
│  │  │    BACKEND SERVICE     │                       │   │
│  │  │   (todo-backend-svc)   │                       │   │
│  │  │      ClusterIP:8000    │◄───────────┐         │   │
│  │  └────────────────────────┘            │         │   │
│  │                                         │         │   │
│  │  ┌────────────────────────────────┐    │         │   │
│  │  │       FRONTEND DEPLOYMENT      │    │         │   │
│  │  │  ┌─────────┐  ┌─────────┐     │    │         │   │
│  │  │  │  Pod 1  │  │  Pod 2  │     │    │         │   │
│  │  │  └────┬────┘  └────┬────┘     │    │         │   │
│  │  └───────┼────────────┼──────────┘    │         │   │
│  │          │            │                │         │   │
│  │          └─────┬──────┘                │         │   │
│  │                ▼                        │         │   │
│  │  ┌────────────────────────┐            │         │   │
│  │  │   FRONTEND SERVICE     │────────────┘         │   │
│  │  │  (todo-frontend-svc)   │  (env: API_URL)     │   │
│  │  │     ClusterIP:3000     │                      │   │
│  │  └───────────┬────────────┘                      │   │
│  │              │                                    │   │
│  │              └──────────────┐                     │   │
│  │                             │                     │   │
│  │  ┌──────────────────────────▼───────────────┐   │   │
│  │  │              INGRESS                      │   │   │
│  │  │           (todo-ingress)                  │   │   │
│  │  │  /api/* → backend-svc:8000               │   │   │
│  │  │  /*     → frontend-svc:3000              │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  │                                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                           │                              │
└───────────────────────────┼──────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   EXTERNAL: NEON DB     │
              │  (PostgreSQL Serverless) │
              └─────────────────────────┘
```

---

## 5. Label Standards

All resources follow Kubernetes recommended labels:

| Label | Purpose | Example |
|-------|---------|---------|
| `app.kubernetes.io/name` | Application name | `todo-app` |
| `app.kubernetes.io/component` | Component within app | `backend`, `frontend` |
| `app.kubernetes.io/version` | Application version | `1.0.0` |
| `app.kubernetes.io/part-of` | Higher-level application | `todo-system` |
| `app.kubernetes.io/managed-by` | Tool managing resource | `helm` |
| `app` | Simple selector label | `todo-backend` |

---

## 6. Port Mapping

| Service | Container Port | Service Port | Ingress Path |
|---------|---------------|--------------|--------------|
| Backend | 8000 | 8000 | /api/* |
| Frontend | 3000 | 3000 | /* |

---

## 7. Resource Limits Summary

| Component | Memory Request | Memory Limit | CPU Request | CPU Limit |
|-----------|---------------|--------------|-------------|-----------|
| Backend Pod | 256Mi | 512Mi | 200m | 500m |
| Frontend Pod | 128Mi | 256Mi | 100m | 250m |
| **Total (2 replicas each)** | **768Mi** | **1536Mi** | **600m** | **1500m** |

Minimum Minikube requirements: 4GB RAM, 2 CPUs
