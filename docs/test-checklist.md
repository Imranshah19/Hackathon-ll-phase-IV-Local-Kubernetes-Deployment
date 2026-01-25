# Phase 4 - Todo Features Test Checklist

## Pre-Deployment Checklist

- [ ] Minikube installed
- [ ] Docker Desktop running
- [ ] Helm installed
- [ ] kubectl configured
- [ ] .env file created with valid credentials

---

## Deployment Verification

### 1. Minikube Cluster
```bash
minikube status
```
- [ ] Minikube is running
- [ ] Docker driver active

### 2. Pods Running
```bash
kubectl get pods
```
- [ ] todo-frontend pod: Running (Ready 1/1)
- [ ] todo-backend pod: Running (Ready 1/1)
- [ ] No CrashLoopBackOff errors

### 3. Services Active
```bash
kubectl get svc
```
- [ ] todo-frontend service: ClusterIP on port 3000
- [ ] todo-backend service: ClusterIP on port 8000

### 4. Ingress Configured
```bash
kubectl get ingress
```
- [ ] Ingress has ADDRESS assigned
- [ ] Host: todo.local configured

### 5. Hosts File Updated
- [ ] Added: `<minikube-ip> todo.local` to hosts file

---

## Todo Core Features (Phase I)

### Feature 1: Add Task
**Test:** "Add a task to buy groceries"

- [ ] Chat sends request successfully
- [ ] Task created in database
- [ ] Response confirms task added
- [ ] Task appears in task list

### Feature 2: View Tasks
**Test:** "Show my tasks" or "List all tasks"

- [ ] Chat displays task list
- [ ] All tasks visible with correct details
- [ ] Task IDs shown correctly

### Feature 3: Update Task
**Test:** "Update task 1 title to Call mom"

- [ ] Chat sends update request
- [ ] Task updated in database
- [ ] Response confirms update
- [ ] Changed task visible in list

### Feature 4: Mark Complete
**Test:** "Mark task 1 as done" or "Complete task 1"

- [ ] Chat sends completion request
- [ ] Task status changed to completed
- [ ] Response confirms completion
- [ ] Task shows as completed in list

### Feature 5: Delete Task
**Test:** "Delete task 1" or "Remove task 1"

- [ ] Chat sends delete request
- [ ] Task removed from database
- [ ] Response confirms deletion
- [ ] Task no longer in list

---

## AI Chat Features (Phase III)

### Natural Language Understanding
- [ ] "Add buy milk to my list" → Creates task
- [ ] "What do I need to do?" → Shows tasks
- [ ] "I finished the grocery task" → Marks complete
- [ ] "Remove the first task" → Deletes task

### Conversation History
- [ ] Previous messages visible
- [ ] Context maintained across messages
- [ ] Can reference previous tasks

### Error Handling
- [ ] Invalid commands show helpful message
- [ ] Low confidence triggers CLI fallback
- [ ] Network errors handled gracefully

---

## Kubernetes Features (Phase IV)

### Scaling
```bash
kubectl scale deployment todo-backend --replicas=3
kubectl get pods
```
- [ ] New pods created
- [ ] All pods reach Ready state
- [ ] App continues working during scale

### Pod Restart Recovery
```bash
kubectl delete pod <pod-name>
kubectl get pods
```
- [ ] New pod automatically created
- [ ] App recovers without data loss
- [ ] No manual intervention needed

### Logs Accessible
```bash
kubectl logs -l app=todo-backend
kubectl logs -l app=todo-frontend
```
- [ ] Backend logs visible
- [ ] Frontend logs visible
- [ ] No critical errors in logs

---

## AI-Ops Commands (kubectl-ai)

```bash
kubectl-ai "show all pods"
kubectl-ai "analyze cluster health"
kubectl-ai "scale backend to 3 replicas"
kubectl-ai "get backend logs"
```
- [ ] Commands translate correctly
- [ ] Actions execute successfully

---

## Performance Checks

- [ ] Frontend loads in < 3 seconds
- [ ] API responses in < 500ms
- [ ] No memory leaks (check with `kubectl top pods`)
- [ ] CPU usage reasonable

---

## Final Sign-Off

| Check | Status | Tester | Date |
|-------|--------|--------|------|
| Deployment works | ⬜ | | |
| Add task works | ⬜ | | |
| View tasks works | ⬜ | | |
| Update task works | ⬜ | | |
| Complete task works | ⬜ | | |
| Delete task works | ⬜ | | |
| Scaling works | ⬜ | | |
| AI-Ops works | ⬜ | | |

---

**Phase 4 Test Complete:** ⬜ Yes / ⬜ No

**Notes:**
_______________________________________
_______________________________________
_______________________________________
