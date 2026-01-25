# AI-Ops Integration Guide

**Phase**: 4.4
**Status**: Implementation Guide
**Last Updated**: 2026-01-26

---

## Overview

This guide covers the integration of AI-powered Kubernetes operations tools for the Todo application. These tools enable natural language interactions with your Kubernetes cluster, simplifying common operations and troubleshooting.

### Tools Covered

| Tool | Description | Status |
|------|-------------|--------|
| **kubectl-ai** | Natural language to kubectl command translation | Required |
| **kagent** | AI-powered Kubernetes agent for diagnostics | Optional |
| **Gordon (Docker AI)** | Docker Desktop AI assistant | Optional |

---

## Prerequisites

Before installing AI-Ops tools, ensure you have:

- [ ] Minikube running with the Todo app deployed
- [ ] kubectl configured and working
- [ ] OpenAI API key (for kubectl-ai)
- [ ] Internet connection for API calls

---

## 1. kubectl-ai Installation

### What is kubectl-ai?

kubectl-ai is a kubectl plugin that translates natural language queries into kubectl commands. It uses OpenAI's GPT models to understand your intent and generate appropriate kubectl commands.

### Installation Methods

#### Method 1: Using Krew (Recommended)

```bash
# Install Krew plugin manager (if not installed)
# Linux/macOS
(
  set -x; cd "$(mktemp -d)" &&
  OS="$(uname | tr '[:upper:]' '[:lower:]')" &&
  ARCH="$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/')" &&
  KREW="krew-${OS}_${ARCH}" &&
  curl -fsSLO "https://github.com/kubernetes-sigs/krew/releases/latest/download/${KREW}.tar.gz" &&
  tar zxvf "${KREW}.tar.gz" &&
  ./"${KREW}" install krew
)

# Add to PATH
export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"

# Install kubectl-ai
kubectl krew install ai
```

#### Method 2: Direct Binary (Windows/Linux/macOS)

```bash
# Download from GitHub releases
# https://github.com/sozercan/kubectl-ai/releases

# Linux/macOS
curl -LO https://github.com/sozercan/kubectl-ai/releases/latest/download/kubectl-ai_linux_amd64.tar.gz
tar -xzf kubectl-ai_linux_amd64.tar.gz
sudo mv kubectl-ai /usr/local/bin/

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/sozercan/kubectl-ai/releases/latest/download/kubectl-ai_windows_amd64.zip" -OutFile "kubectl-ai.zip"
Expand-Archive -Path "kubectl-ai.zip" -DestinationPath "."
Move-Item -Path "kubectl-ai.exe" -Destination "$env:USERPROFILE\bin\"
```

#### Method 3: Using Go

```bash
go install github.com/sozercan/kubectl-ai@latest
```

### Configuration

Set your OpenAI API key:

```bash
# Linux/macOS
export OPENAI_API_KEY="your-api-key-here"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc

# Windows (PowerShell)
$env:OPENAI_API_KEY = "your-api-key-here"

# Windows (permanent)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-api-key-here", "User")
```

### Verify Installation

```bash
# Check version
kubectl ai --version

# Test basic command
kubectl ai "list all namespaces"
```

---

## 2. kagent Installation (Optional)

### What is kagent?

kagent is an AI-powered Kubernetes agent that provides intelligent diagnostics, automated troubleshooting, and cluster insights.

### Installation

```bash
# Using Helm
helm repo add kagent https://kagent-dev.github.io/kagent/
helm repo update

# Install kagent
helm install kagent kagent/kagent \
  --namespace kagent-system \
  --create-namespace \
  --set openai.apiKey=$OPENAI_API_KEY
```

### Alternative: Local Installation

```bash
# Clone repository
git clone https://github.com/kagent-dev/kagent.git
cd kagent

# Install locally
make install
```

### Verify Installation

```bash
# Check kagent status
kubectl get pods -n kagent-system

# Run diagnostic
kagent diagnose
```

---

## 3. Gordon (Docker AI) - Optional

### What is Gordon?

Gordon is Docker Desktop's built-in AI assistant that helps with container and Docker-related tasks.

### Enabling Gordon

1. Open Docker Desktop
2. Go to Settings > Features in development
3. Enable "Docker AI (Gordon)"
4. Restart Docker Desktop

### Usage

Gordon is accessible through:
- Docker Desktop UI (chat interface)
- Command line: `docker ai "your question"`

---

## 4. AI-Ops Commands for Todo App

### Common kubectl-ai Queries

#### Pod Operations

| Natural Language Query | Expected kubectl Command |
|------------------------|-------------------------|
| "Show all pods in default namespace" | `kubectl get pods -n default` |
| "Get backend pod logs" | `kubectl logs -l app=todo-backend` |
| "Describe the frontend deployment" | `kubectl describe deployment todo-frontend` |
| "Show pods that are not running" | `kubectl get pods --field-selector=status.phase!=Running` |
| "Get all pods with their IP addresses" | `kubectl get pods -o wide` |

#### Service Operations

| Natural Language Query | Expected kubectl Command |
|------------------------|-------------------------|
| "List all services" | `kubectl get svc` |
| "Show backend service endpoints" | `kubectl get endpoints todo-backend` |
| "Get service details for frontend" | `kubectl describe svc todo-frontend` |

#### Deployment Operations

| Natural Language Query | Expected kubectl Command |
|------------------------|-------------------------|
| "Scale backend to 3 replicas" | `kubectl scale deployment todo-backend --replicas=3` |
| "Show deployment status" | `kubectl rollout status deployment/todo-backend` |
| "Restart the backend deployment" | `kubectl rollout restart deployment/todo-backend` |
| "Show deployment history" | `kubectl rollout history deployment/todo-backend` |

#### Troubleshooting Queries

| Natural Language Query | Expected kubectl Command |
|------------------------|-------------------------|
| "Why is the backend pod failing?" | `kubectl describe pod <pod-name>` + `kubectl logs <pod-name>` |
| "Show events in the namespace" | `kubectl get events --sort-by='.lastTimestamp'` |
| "Check resource usage" | `kubectl top pods` |
| "Show pod resource limits" | `kubectl get pods -o jsonpath='{.items[*].spec.containers[*].resources}'` |

#### Configuration Queries

| Natural Language Query | Expected kubectl Command |
|------------------------|-------------------------|
| "Show all configmaps" | `kubectl get configmaps` |
| "Get secrets in default namespace" | `kubectl get secrets` |
| "Show ingress configuration" | `kubectl get ingress -o yaml` |
| "List all environment variables in backend" | `kubectl exec <pod> -- env` |

---

## 5. AI-Ops Workflows

### Workflow 1: Health Check

```bash
# Check overall cluster health
kubectl ai "show me the health status of all pods"

# Check specific component
kubectl ai "is the backend healthy?"

# View recent events
kubectl ai "show recent warning events"
```

### Workflow 2: Scaling Operations

```bash
# Check current replica count
kubectl ai "how many backend replicas are running?"

# Scale up
kubectl ai "scale backend deployment to 4 replicas"

# Verify scaling
kubectl ai "show backend pods and their status"

# Scale down
kubectl ai "reduce backend replicas to 2"
```

### Workflow 3: Log Analysis

```bash
# View recent logs
kubectl ai "show last 50 lines of backend logs"

# Search for errors
kubectl ai "find errors in backend logs"

# Follow logs
kubectl ai "stream backend pod logs"
```

### Workflow 4: Troubleshooting

```bash
# Diagnose failing pod
kubectl ai "why is pod todo-backend-xxx not starting?"

# Check resource constraints
kubectl ai "are any pods hitting memory limits?"

# Network debugging
kubectl ai "can frontend pods reach backend service?"

# Database connection issues
kubectl ai "check if backend can connect to external database"
```

### Workflow 5: Resource Management

```bash
# View resource usage
kubectl ai "show CPU and memory usage for all pods"

# Find resource-heavy pods
kubectl ai "which pods are using the most memory?"

# Check resource quotas
kubectl ai "show resource limits for backend deployment"
```

---

## 6. Best Practices

### When to Use AI-Ops

| Use Case | Recommended |
|----------|-------------|
| Quick status checks | Yes |
| Learning kubectl | Yes |
| Troubleshooting | Yes |
| Complex queries | Yes |
| Production changes | With caution |
| Automated scripts | No (use direct kubectl) |

### Security Considerations

1. **API Key Protection**: Never commit API keys to version control
2. **Command Review**: Always review generated commands before executing
3. **Production Safety**: Use `--dry-run` flag for production clusters
4. **Audit Logging**: Log AI-generated commands for audit trails

### Tips for Effective Queries

1. **Be Specific**: "Show backend pod logs" is better than "show logs"
2. **Include Context**: "Scale todo-backend to 3" is clearer than "scale to 3"
3. **Use App Names**: Reference actual deployment/service names
4. **Ask Follow-ups**: Build on previous queries for complex operations

---

## 7. Troubleshooting AI-Ops Tools

### kubectl-ai Issues

| Problem | Solution |
|---------|----------|
| "API key not found" | Set `OPENAI_API_KEY` environment variable |
| "Rate limit exceeded" | Wait and retry, or upgrade OpenAI plan |
| "Command not found" | Ensure kubectl-ai is in PATH |
| "Invalid response" | Try rephrasing the query |

### kagent Issues

| Problem | Solution |
|---------|----------|
| Pod not starting | Check `kubectl logs -n kagent-system` |
| API connection failed | Verify OPENAI_API_KEY secret |
| Permission denied | Check RBAC configuration |

### Common Fixes

```bash
# Reinstall kubectl-ai
kubectl krew uninstall ai
kubectl krew install ai

# Verify API key
echo $OPENAI_API_KEY

# Test OpenAI connectivity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## 8. Quick Reference Card

### Essential Commands

```bash
# Pod status
kubectl ai "show all pods"

# Logs
kubectl ai "backend logs last 100 lines"

# Scale
kubectl ai "scale backend to N replicas"

# Restart
kubectl ai "restart backend deployment"

# Events
kubectl ai "show recent cluster events"

# Resources
kubectl ai "show pod resource usage"
```

### Todo App Specific

```bash
# Full status check
kubectl ai "show status of todo-app deployment"

# Check connectivity
kubectl ai "test backend health endpoint"

# View configuration
kubectl ai "show todo-app configmap values"

# Ingress status
kubectl ai "is ingress routing traffic correctly"
```

---

## 9. Integration with CI/CD

While AI-Ops tools are primarily for interactive use, you can integrate them for:

### Slack/Teams Notifications

```bash
# Generate status report
STATUS=$(kubectl ai "summarize cluster health" 2>&1)
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$STATUS\"}" \
  $SLACK_WEBHOOK_URL
```

### Monitoring Scripts

```bash
#!/bin/bash
# health-check.sh
HEALTH=$(kubectl ai "are all todo-app pods healthy?" 2>&1)
if [[ $HEALTH == *"unhealthy"* ]]; then
  echo "ALERT: Unhealthy pods detected"
  # Send alert
fi
```

---

## References

- [kubectl-ai GitHub](https://github.com/sozercan/kubectl-ai)
- [kagent Documentation](https://kagent.dev/docs)
- [Docker Gordon](https://docs.docker.com/desktop/features/gordon/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Kubernetes kubectl Reference](https://kubernetes.io/docs/reference/kubectl/)

---

## Appendix: Command Translation Examples

### Example Session

```
$ kubectl ai "show me pods that have restarted more than twice"
> kubectl get pods -o jsonpath='{range .items[?(@.status.containerStatuses[0].restartCount>2)]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'

$ kubectl ai "get the backend deployment and show its image"
> kubectl get deployment todo-backend -o jsonpath='{.spec.template.spec.containers[0].image}'

$ kubectl ai "create a port-forward to access backend locally"
> kubectl port-forward svc/todo-backend 8000:8000

$ kubectl ai "show me the last 5 events sorted by time"
> kubectl get events --sort-by='.lastTimestamp' | tail -5
```
