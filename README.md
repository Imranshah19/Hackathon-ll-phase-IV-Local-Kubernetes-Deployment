# AI-Powered Todo Chatbot

A full-stack Todo application with AI-powered natural language interface built using Spec-Driven Development (SDD).

## Features

- **User Authentication**: Secure JWT-based login/registration
- **Task Management**: Full CRUD operations for todos
- **AI Chat Interface**: Manage tasks using natural language
- **Conversation History**: Persistent chat sessions
- **Confidence Scoring**: AI interpretation with fallback to CLI commands

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (Neon) / SQLite (dev)
- **ORM**: SQLModel
- **Auth**: JWT + Argon2 password hashing
- **AI**: OpenAI GPT-4 function calling

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **State**: React hooks

## Project Structure

```
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routers
│   │   ├── models/       # SQLModel entities
│   │   ├── services/     # Business logic
│   │   ├── ai/           # AI interpretation layer
│   │   └── auth/         # JWT & password handling
│   ├── alembic/          # Database migrations
│   └── tests/            # Unit, integration, contract tests
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # API client & auth
├── specs/                # Feature specifications
└── docs/                 # Project documentation
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, SQLite for dev)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with your API URL

# Start dev server
npm run dev
```

### Access the App
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-your-api-key
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login & get token |
| GET | `/api/auth/me` | Get current user |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks/{id}` | Get task |
| PATCH | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |

### AI Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/message` | Send message |
| POST | `/api/chat/confirm` | Confirm action |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Get conversation |

## AI Chat Examples

```
"Add a task to buy groceries"
"Show my pending tasks"
"Mark task 1 as done"
"Delete the grocery task"
```

## Development Phases

- **Phase 1**: Constitution + Specification + Planning
- **Phase 2**: Backend + Frontend Implementation
- **Phase 3**: AI Integration + Deployment
- **Phase 4**: Local Kubernetes Deployment (Current)

See [docs/](./docs/) for detailed phase documentation.

---

## Phase 4: Kubernetes Deployment

Deploy the Todo application on a local Kubernetes cluster using Minikube and Helm.

### Prerequisites

- Docker Desktop
- Minikube
- Helm 3.x
- kubectl

### Quick Start (Kubernetes)

```bash
# 1. Start Minikube
./scripts/minikube-setup.sh   # Linux/macOS
# OR
./scripts/minikube-setup.ps1  # Windows

# 2. Deploy application
./scripts/deploy-local.sh     # Linux/macOS
# OR
./scripts/deploy-local.ps1    # Windows

# 3. Add to /etc/hosts (get IP from minikube ip)
<minikube-ip> todo.local

# 4. Access the app
http://todo.local
```

### Kubernetes Architecture

```
┌─────────────────────────────────────────┐
│            MINIKUBE CLUSTER             │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      NGINX Ingress (todo.local) │   │
│  └──────────────┬──────────────────┘   │
│          ┌──────┴──────┐               │
│          ▼             ▼               │
│   ┌───────────┐ ┌───────────┐         │
│   │ Frontend  │ │  Backend  │         │
│   │ (Next.js) │ │ (FastAPI) │         │
│   │ x2 pods   │ │ x2 pods   │         │
│   └───────────┘ └─────┬─────┘         │
│                       │                │
└───────────────────────┼────────────────┘
                        ▼
              ┌─────────────────┐
              │ Neon PostgreSQL │
              │   (External)    │
              └─────────────────┘
```

### Helm Commands

```bash
# Install
helm install todo-app ./helm/todo-app

# Upgrade with custom values
helm upgrade todo-app ./helm/todo-app --set backend.replicas=3

# Uninstall
helm uninstall todo-app
```

### AI-Ops Integration

Use natural language to manage the cluster with kubectl-ai:

```bash
# Install kubectl-ai
kubectl krew install ai

# Example commands
kubectl ai "show all pods"
kubectl ai "scale backend to 3 replicas"
kubectl ai "get backend logs"
kubectl ai "why is pod failing?"
```

See [docs/ai-ops.md](./docs/ai-ops.md) for full AI-Ops guide.

### Documentation

| Document | Description |
|----------|-------------|
| [docs/deployment.md](./docs/deployment.md) | Full deployment guide |
| [docs/ai-ops.md](./docs/ai-ops.md) | AI-Ops integration guide |
| [docs/troubleshooting.md](./docs/troubleshooting.md) | Common issues & solutions |

---

## Cloud Deployment

### Backend (Render/Railway)
1. Connect GitHub repository
2. Set environment variables
3. Deploy with `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)
1. Import from GitHub
2. Set `NEXT_PUBLIC_API_URL` to backend URL
3. Deploy

### Database (Neon/Supabase)
1. Create PostgreSQL database
2. Get connection string
3. Set `DATABASE_URL` in backend

## License

MIT
