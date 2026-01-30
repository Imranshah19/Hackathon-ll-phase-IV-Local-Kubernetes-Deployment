# Phase 4 - Todo Features Test Checklist

## Pre-Deployment Checklist

- [x] Minikube installed
- [x] Docker Desktop running
- [x] Helm installed
- [x] kubectl configured
- [x] .env file created with valid credentials

---

## Deployment Verification

### 1. Minikube Cluster
```bash
minikube status
```
- [x] Minikube is running
- [x] Docker driver active

### 2. Pods Running
```bash
kubectl get pods
```
- [x] todo-frontend pod: Running (Ready 1/1)
- [x] todo-backend pod: Running (Ready 1/1)
- [x] No CrashLoopBackOff errors

### 3. Services Active
```bash
kubectl get svc
```
- [x] todo-frontend service: ClusterIP on port 3000
- [x] todo-backend service: ClusterIP on port 8000

### 4. Ingress Configured
```bash
kubectl get ingress
```
- [x] Ingress has ADDRESS assigned
- [x] Host: todo.local configured

### 5. Hosts File Updated
- [x] Added: `<minikube-ip> todo.local` to hosts file

---

## Todo Core Features (Phase I)

### Feature 1: Add Task
**Test:** "Add a task to buy groceries"

- [x] Chat sends request successfully
- [x] Task created in database
- [x] Response confirms task added
- [x] Task appears in task list

### Feature 2: View Tasks
**Test:** "Show my tasks" or "List all tasks"

- [x] Chat displays task list
- [x] All tasks visible with correct details
- [x] Task IDs shown correctly

### Feature 3: Update Task
**Test:** "Update task 1 title to Call mom"

- [x] Chat sends update request
- [x] Task updated in database
- [x] Response confirms update
- [x] Changed task visible in list

### Feature 4: Mark Complete
**Test:** "Mark task 1 as done" or "Complete task 1"

- [x] Chat sends completion request
- [x] Task status changed to completed
- [x] Response confirms completion
- [x] Task shows as completed in list

### Feature 5: Delete Task
**Test:** "Delete task 1" or "Remove task 1"

- [x] Chat sends delete request
- [x] Task removed from database
- [x] Response confirms deletion
- [x] Task no longer in list

---

## AI Chat Features (Phase III)

### Natural Language Understanding
- [x] "Add buy milk to my list" -> Creates task
- [x] "What do I need to do?" -> Shows tasks
- [x] "I finished the grocery task" -> Marks complete
- [x] "Remove the first task" -> Deletes task

### Conversation History
- [x] Previous messages visible
- [x] Context maintained across messages
- [x] Can reference previous tasks

### Error Handling
- [x] Invalid commands show helpful message
- [x] Low confidence triggers CLI fallback
- [x] Network errors handled gracefully

---

## Kubernetes Features (Phase IV)

### Scaling
```bash
kubectl scale deployment todo-backend --replicas=3
kubectl get pods
```
- [x] New pods created
- [x] All pods reach Ready state
- [x] App continues working during scale

### Pod Restart Recovery
```bash
kubectl delete pod <pod-name>
kubectl get pods
```
- [x] New pod automatically created
- [x] App recovers without data loss
- [x] No manual intervention needed

### Logs Accessible
```bash
kubectl logs -l app=todo-backend
kubectl logs -l app=todo-frontend
```
- [x] Backend logs visible
- [x] Frontend logs visible
- [x] No critical errors in logs

---

## AI-Ops Commands (kubectl-ai)

```bash
kubectl-ai "show all pods"
kubectl-ai "analyze cluster health"
kubectl-ai "scale backend to 3 replicas"
kubectl-ai "get backend logs"
```
- [x] Commands translate correctly
- [x] Actions execute successfully

---

## Performance Checks

- [x] Frontend loads in < 3 seconds
- [x] API responses in < 500ms
- [x] No memory leaks (check with `kubectl top pods`)
- [x] CPU usage reasonable

---

## Final Sign-Off

| Check | Status | Tester | Date |
|-------|--------|--------|------|
| Deployment works | PASS | Auto | 2026-01-30 |
| Add task works | PASS | Auto | 2026-01-30 |
| View tasks works | PASS | Auto | 2026-01-30 |
| Update task works | PASS | Auto | 2026-01-30 |
| Complete task works | PASS | Auto | 2026-01-30 |
| Delete task works | PASS | Auto | 2026-01-30 |
| Scaling works | PASS | Auto | 2026-01-30 |
| AI-Ops works | PASS | Auto | 2026-01-30 |

---

**Phase 4 Test Complete:** [x] Yes

**Notes:**
Phase 4 Local Kubernetes Deployment completed successfully.
All 29 tasks implemented and verified.
Ready for production deployment.
