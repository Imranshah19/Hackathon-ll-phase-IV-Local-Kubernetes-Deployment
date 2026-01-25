# Troubleshooting Guide

**Phase**: 4.5
**Last Updated**: 2026-01-26

---

## Overview

This guide provides solutions for common issues encountered when deploying and running the Todo application on Minikube.

---

## Quick Diagnostic Commands

```bash
# Overall cluster status
kubectl get all

# Pod status with details
kubectl get pods -o wide

# Recent events (sorted by time)
kubectl get events --sort-by='.lastTimestamp'

# Resource usage
kubectl top pods

# Using kubectl-ai
kubectl ai "diagnose any issues with todo-app"
```

---

## 1. Pod Startup Issues

### Problem: Pod stuck in `Pending` state

**Symptoms:**
```
NAME                            READY   STATUS    RESTARTS   AGE
todo-backend-xxx                0/1     Pending   0          5m
```

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Insufficient resources | Increase Minikube resources: `minikube stop && minikube start --memory=4096 --cpus=2` |
| Node not ready | Check node: `kubectl get nodes` and `kubectl describe node minikube` |
| PVC not bound | Check PVC: `kubectl get pvc` |

**Diagnostic:**
```bash
kubectl describe pod <pod-name>
# Look for "Events" section at the bottom
```

---

### Problem: Pod stuck in `ContainerCreating`

**Symptoms:**
```
NAME                            READY   STATUS              RESTARTS   AGE
todo-backend-xxx                0/1     ContainerCreating   0          5m
```

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Image pull failure | Check image name and tag in deployment |
| ImagePullBackOff | Verify Minikube Docker env: `eval $(minikube docker-env)` |
| ConfigMap/Secret missing | Verify: `kubectl get configmap` and `kubectl get secrets` |

**Diagnostic:**
```bash
kubectl describe pod <pod-name>
kubectl get events --field-selector involvedObject.name=<pod-name>
```

---

### Problem: Pod in `CrashLoopBackOff`

**Symptoms:**
```
NAME                            READY   STATUS             RESTARTS   AGE
todo-backend-xxx                0/1     CrashLoopBackOff   5          10m
```

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Application error | Check logs: `kubectl logs <pod-name>` |
| Missing environment variable | Verify ConfigMap/Secret values |
| Database connection failed | Check DATABASE_URL and network connectivity |
| Port already in use | Check for port conflicts |

**Diagnostic:**
```bash
# Get logs from current container
kubectl logs <pod-name>

# Get logs from previous crashed container
kubectl logs <pod-name> --previous

# Check container exit code
kubectl describe pod <pod-name> | grep -A5 "Last State"
```

---

### Problem: Pod in `ImagePullBackOff`

**Symptoms:**
```
NAME                            READY   STATUS             RESTARTS   AGE
todo-backend-xxx                0/1     ImagePullBackOff   0          5m
```

**Solutions:**

1. **Verify Minikube Docker environment:**
   ```bash
   # Linux/macOS
   eval $(minikube docker-env)

   # Windows PowerShell
   & minikube -p minikube docker-env --shell powershell | Invoke-Expression
   ```

2. **Rebuild images in Minikube context:**
   ```bash
   docker build -t todo-backend:phase4 ./backend
   docker build -t todo-frontend:phase4 ./frontend
   ```

3. **Verify image exists:**
   ```bash
   docker images | grep todo
   ```

4. **Check image pull policy:**
   ```bash
   kubectl get deployment todo-backend -o jsonpath='{.spec.template.spec.containers[0].imagePullPolicy}'
   # Should be "Never" or "IfNotPresent" for local images
   ```

---

## 2. Database Connection Issues

### Problem: Backend cannot connect to database

**Symptoms:**
- Backend pod crashes or restarts
- Logs show: `Connection refused` or `timeout`
- Health endpoint returns `503`

**Diagnostic:**
```bash
# Check backend logs
kubectl logs -l app=todo-backend

# Check DATABASE_URL secret
kubectl get secret todo-app-secrets -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Test connectivity from pod
kubectl exec -it <backend-pod> -- python -c "import asyncpg; print('OK')"
```

**Solutions:**

1. **Verify DATABASE_URL format:**
   ```
   postgresql://user:password@host:5432/database?sslmode=require
   ```

2. **Check Neon database status:**
   - Log into Neon dashboard
   - Verify database is active (not suspended)
   - Check connection limits

3. **Update secret if needed:**
   ```bash
   kubectl delete secret todo-app-secrets
   helm upgrade todo-app ./helm/todo-app --set secrets.databaseUrl="<new-url>"
   ```

4. **Restart backend pods:**
   ```bash
   kubectl rollout restart deployment/todo-backend
   ```

---

### Problem: Database connection pool exhausted

**Symptoms:**
- Intermittent 500 errors
- Logs show: `too many connections`

**Solutions:**

1. Reduce connection pool size in backend configuration
2. Scale down replicas temporarily
3. Check for connection leaks in application code

---

## 3. Ingress Issues

### Problem: Ingress not routing traffic

**Symptoms:**
- `curl http://todo.local` returns connection refused or timeout
- Ingress shows no ADDRESS

**Diagnostic:**
```bash
# Check ingress status
kubectl get ingress

# Check ingress controller
kubectl get pods -n ingress-nginx

# Describe ingress
kubectl describe ingress todo-app-ingress
```

**Solutions:**

1. **Enable ingress addon:**
   ```bash
   minikube addons enable ingress

   # Wait for controller to start
   kubectl wait --namespace ingress-nginx \
     --for=condition=ready pod \
     --selector=app.kubernetes.io/component=controller \
     --timeout=90s
   ```

2. **Verify /etc/hosts entry:**
   ```bash
   # Get Minikube IP
   minikube ip

   # Add to hosts file
   # Linux/macOS: /etc/hosts
   # Windows: C:\Windows\System32\drivers\etc\hosts

   # Add line:
   <minikube-ip> todo.local
   ```

3. **Check service endpoints:**
   ```bash
   kubectl get endpoints
   # Ensure services have endpoints (pod IPs)
   ```

---

### Problem: 404 Not Found from Ingress

**Symptoms:**
- Ingress responds but returns 404
- Some paths work, others don't

**Solutions:**

1. **Check path configuration:**
   ```bash
   kubectl get ingress todo-app-ingress -o yaml
   ```

2. **Verify backend service is running:**
   ```bash
   kubectl get svc todo-backend
   kubectl get endpoints todo-backend
   ```

3. **Test direct service access:**
   ```bash
   kubectl port-forward svc/todo-backend 8000:8000
   curl http://localhost:8000/health
   ```

---

### Problem: SSL/TLS certificate errors

**Symptoms:**
- Browser shows certificate warning
- `curl` fails with SSL error

**Solutions:**

1. **For local development, use HTTP:**
   ```bash
   curl http://todo.local
   ```

2. **Or ignore certificate (dev only):**
   ```bash
   curl -k https://todo.local
   ```

---

## 4. Resource Constraint Issues

### Problem: Pods being OOMKilled

**Symptoms:**
```
NAME                            READY   STATUS      RESTARTS   AGE
todo-backend-xxx                0/1     OOMKilled   3          10m
```

**Solutions:**

1. **Increase memory limits:**
   ```bash
   helm upgrade todo-app ./helm/todo-app \
     --set backend.resources.limits.memory=1Gi
   ```

2. **Check actual usage:**
   ```bash
   kubectl top pods
   ```

3. **Increase Minikube memory:**
   ```bash
   minikube stop
   minikube start --memory=6144
   ```

---

### Problem: Pods being CPU throttled

**Symptoms:**
- Slow response times
- High latency
- `kubectl top pods` shows high CPU

**Solutions:**

1. **Increase CPU limits:**
   ```bash
   helm upgrade todo-app ./helm/todo-app \
     --set backend.resources.limits.cpu=1000m
   ```

2. **Scale horizontally:**
   ```bash
   helm upgrade todo-app ./helm/todo-app \
     --set backend.replicas=3
   ```

---

### Problem: Minikube running out of disk space

**Symptoms:**
- Image builds fail
- Pods fail to start
- `No space left on device` errors

**Solutions:**

1. **Clean up unused images:**
   ```bash
   eval $(minikube docker-env)
   docker system prune -a
   ```

2. **Increase Minikube disk:**
   ```bash
   minikube delete
   minikube start --disk-size=40g
   ```

---

## 5. Service Discovery Issues

### Problem: Frontend cannot reach backend

**Symptoms:**
- Frontend shows "Network Error"
- API calls timeout
- CORS errors in browser console

**Diagnostic:**
```bash
# Check services
kubectl get svc

# Test internal DNS
kubectl exec -it <frontend-pod> -- nslookup todo-backend

# Test connectivity
kubectl exec -it <frontend-pod> -- curl http://todo-backend:8000/health
```

**Solutions:**

1. **Verify NEXT_PUBLIC_API_URL:**
   ```bash
   kubectl get deployment todo-frontend -o jsonpath='{.spec.template.spec.containers[0].env}'
   ```

2. **Check service selector matches pod labels:**
   ```bash
   kubectl get svc todo-backend -o yaml
   kubectl get pods -l app=todo-backend --show-labels
   ```

3. **Restart pods to pick up new config:**
   ```bash
   kubectl rollout restart deployment/todo-frontend
   ```

---

## 6. Health Check Failures

### Problem: Liveness probe failing

**Symptoms:**
- Pod restarts frequently
- Events show `Liveness probe failed`

**Solutions:**

1. **Increase probe delays:**
   ```bash
   helm upgrade todo-app ./helm/todo-app \
     --set backend.livenessProbe.initialDelaySeconds=60
   ```

2. **Check health endpoint:**
   ```bash
   kubectl port-forward <pod> 8000:8000
   curl http://localhost:8000/health/live
   ```

---

### Problem: Readiness probe failing

**Symptoms:**
- Pod shows `Running` but `0/1 Ready`
- Service has no endpoints

**Solutions:**

1. **Check readiness endpoint:**
   ```bash
   kubectl exec -it <pod> -- curl http://localhost:8000/health/ready
   ```

2. **Verify database connectivity** (readiness often checks DB)

3. **Increase timeout:**
   ```bash
   helm upgrade todo-app ./helm/todo-app \
     --set backend.readinessProbe.timeoutSeconds=10
   ```

---

## 7. Helm/Deployment Issues

### Problem: Helm upgrade fails

**Symptoms:**
- `helm upgrade` returns error
- Deployment stuck in rollout

**Solutions:**

1. **Check Helm release status:**
   ```bash
   helm list
   helm status todo-app
   ```

2. **Rollback if needed:**
   ```bash
   helm rollback todo-app
   ```

3. **Force reinstall:**
   ```bash
   helm uninstall todo-app
   helm install todo-app ./helm/todo-app
   ```

---

### Problem: ConfigMap/Secret changes not applied

**Symptoms:**
- Updated values don't appear in pods
- Old configuration still active

**Solutions:**

1. **Restart deployment:**
   ```bash
   kubectl rollout restart deployment/todo-backend
   kubectl rollout restart deployment/todo-frontend
   ```

2. **Verify ConfigMap updated:**
   ```bash
   kubectl get configmap todo-app-config -o yaml
   ```

---

## 8. Minikube-Specific Issues

### Problem: Minikube won't start

**Solutions:**

1. **Delete and recreate:**
   ```bash
   minikube delete
   minikube start --memory=4096 --cpus=2
   ```

2. **Check driver:**
   ```bash
   # Use Docker driver
   minikube start --driver=docker

   # Or Hyper-V on Windows
   minikube start --driver=hyperv
   ```

3. **Check system resources** (ensure enough RAM/CPU available)

---

### Problem: Docker environment not working

**Symptoms:**
- Images not found after building
- `docker images` shows different images than expected

**Solutions:**

1. **Re-run docker-env:**
   ```bash
   # Linux/macOS
   eval $(minikube docker-env)

   # Windows PowerShell
   & minikube -p minikube docker-env --shell powershell | Invoke-Expression
   ```

2. **Verify context:**
   ```bash
   docker context ls
   docker images  # Should show Minikube's images
   ```

---

## 9. AI-Ops Troubleshooting

### Problem: kubectl-ai not working

**Solutions:**

1. **Check API key:**
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Test OpenAI connectivity:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. **Reinstall:**
   ```bash
   kubectl krew uninstall ai
   kubectl krew install ai
   ```

---

## Quick Fix Checklist

When something isn't working, try these in order:

- [ ] Check pod status: `kubectl get pods`
- [ ] Check pod logs: `kubectl logs <pod-name>`
- [ ] Check events: `kubectl get events --sort-by='.lastTimestamp'`
- [ ] Describe the resource: `kubectl describe pod/svc/ingress <name>`
- [ ] Verify Minikube Docker env is set
- [ ] Restart deployments: `kubectl rollout restart deployment --all`
- [ ] Check Minikube status: `minikube status`
- [ ] Restart Minikube: `minikube stop && minikube start`

---

## Getting Help

If issues persist:

1. **Collect diagnostics:**
   ```bash
   kubectl cluster-info dump > cluster-dump.txt
   ```

2. **Check Minikube logs:**
   ```bash
   minikube logs
   ```

3. **Review Helm values:**
   ```bash
   helm get values todo-app
   ```

4. **Use AI-Ops:**
   ```bash
   kubectl ai "diagnose all issues with my deployment"
   ```
