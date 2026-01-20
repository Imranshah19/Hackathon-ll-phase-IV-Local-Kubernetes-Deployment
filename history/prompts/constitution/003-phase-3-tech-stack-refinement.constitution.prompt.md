---
id: 003
title: Phase 3 Tech Stack Refinement
stage: constitution
date: 2026-01-19
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: 005-data-schemas-phase2
user: developer
command: /sp.constitution
labels: ["phase-3", "openai-agents-sdk", "mcp-server", "dataset-schema"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - n/a (constitution update)
---

## Prompt

/sp.constitution
Title: Hackathon II — Evolution of Todo
Project Mode: Spec-Driven Development
Tech Mode: CLI + Web + AI Chat
Phases: 1 → 2 → 3
Goal: Build Todo App starting from console, evolve to AI-powered Chatbot

# PHASE-1: In-Memory Console App
- Define project Constitution
- Create SP.Plan and SP.Task specs
- Establish rules and validation
- Local console test, No DB, no AI

# PHASE-2: Full-Stack Web App with Bonsai CLI
- CRUD todos via CLI
- Persistent storage using JSON or DB
- SP.Plan execution validation
- Bonsai CLI is authoritative execution engine

# PHASE-3: AI-Powered Chatbot
- AI interprets natural language commands
- Generates SP.Plan → Bonsai CLI executes
- Maintains backward compatibility with Phase-2 CLI
- Stateless AI Chat Layer → SP.Task → Dataset update → Response

# Technology Stack
- Frontend: OpenAI ChatKit (optional console UI)
- Backend: Python FastAPI
- AI: OpenAI Agents SDK, Claude/OpenAI
- MCP Server: Official MCP SDK
- ORM: SQLModel
- Database: Neon PostgreSQL or JSON
- Execution: Bonsai CLI (Phase-2 reuse)

# Dataset (normalized)
- tasks.json: {id, title, description, status, due}
- conversations.json: {id, user_id, timestamp}
- messages.json: {conversation_id, role, content, timestamp}

## Response snapshot

Updated `.specify/memory/constitution.md` from v2.0.0 to v2.1.0 with:

1. **Phase Descriptions Refined**:
   - Phase 1: Simplified to "No DB, no AI"
   - Phase 2: Renamed to "Full-Stack Web App with Bonsai CLI"
   - Phase 3: Added "Stateless AI Chat Layer" note and 7-step execution flow

2. **Technology Stack Updated**:
   - Added OpenAI Agents SDK for agent orchestration
   - Added Official MCP SDK for Model Context Protocol
   - Added OpenAI ChatKit as optional console UI
   - Marked Bonsai CLI as "Phase 2 reuse"

3. **Dataset Schema Normalized**:
   - tasks.json: Core task data
   - conversations.json: Conversation metadata (new)
   - messages.json: Individual messages with FK to conversations (new)

4. **Architecture Flow**: Added NLP Interpreter as explicit step in execution chain

## Outcome

- ✅ Impact: Minor version bump (2.0.0 → 2.1.0) - Tech stack additions and schema normalization
- 🧪 Tests: n/a (constitution is specification document)
- 📁 Files: 1 modified (.specify/memory/constitution.md)
- 🔁 Next prompts: /sp.specify for Phase 3 AI Chat feature implementation
- 🧠 Reflection: Constitution now includes OpenAI Agents SDK and MCP Server integration, with normalized dataset schema for better data management

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Template compatibility verified - PASS
- Prompt variant (if applicable): n/a
- Next experiment: Implement MCP Server integration with Bonsai CLI tools
