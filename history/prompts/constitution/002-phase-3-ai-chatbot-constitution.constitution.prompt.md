---
id: 002
title: Phase 3 AI Chatbot Constitution Update
stage: constitution
date: 2026-01-19
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: 005-data-schemas-phase2
user: developer
command: /sp.constitution
labels: ["phase-3", "ai-chatbot", "constitution", "bonsai-cli"]
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

# ------------------------
# PHASE-1: In-Memory Console App
# ------------------------
Phase: 1
Objective:
- Define project Constitution
- Create SP.Plan and SP.Task specs
- Establish roles, rules, and validation checks
Deliverables:
- Constitution.md
- SP.Plan template
- SP.Task template
Execution:
- Local console test only
- No dataset, no CLI execution
- No AI integration

# ------------------------
# PHASE-2: Web App with Bonsai CLI
# ------------------------
Phase: 2
Objective:
- Implement CRUD todos via CLI
- Persist tasks in JSON or in-memory dataset
- Validate SP.Plan execution
Deliverables:
- Bonsai CLI commands for Add/Delete/Update/List todos
- Dataset management scripts
- Constitution & Spec updated
Execution:
1. Bonsai CLI is authoritative execution engine
2. User manually triggers commands
3. SP.Plan converted to Bonsai commands
Example Commands:
- bonsai add --title "Buy milk" --due "tomorrow"
- bonsai list --status pending
- bonsai update --id 3 --title "Call mom tonight"
- bonsai delete --id 2

# ------------------------
# PHASE-3: AI-Powered Chatbot
# ------------------------
Phase: 3
Objective:
- Add AI Chat interface
- Convert natural language input → SP.Plan → Bonsai CLI execution
- Preserve Constitution rules
- Automate CRUD operations through AI
Deliverables:
- AI Chat Layer (console or web optional)
- NLP Interpreter
- SP.Plan Generator
- Bonsai CLI Executor
- Dataset update and response rendering
Execution Flow:
1. User input (natural language)
2. AI interprets and converts to SP.Plan
3. Constitution validation
4. SP.Task built
5. Bonsai CLI executes task
6. Dataset updated
7. Response rendered to user
Example Natural Language Commands:
- "Add a todo for tomorrow: Buy groceries"
- "Show my pending tasks"
- "Mark task 3 as complete"
- "Delete the meeting task"
- "Update task 1 to 'Call mom tonight'"
Bonsai CLI Commands Generated:
- bonsai add --title "Buy groceries" --due "tomorrow"
- bonsai list --status pending
- bonsai complete --id 3
- bonsai delete --id 5
- bonsai update --id 1 --title "Call mom tonight"
Dataset:
- JSON/In-Memory database
- Stores task id, title, description, status, due
- Supports conversation history if needed
Architecture Diagram:
User → AI Chat Layer → SP.Plan Generator → Constitution Validation → SP.Task Builder → Bonsai CLI → Dataset → Response → User
Notes:
- Phase-3 reuses Phase-2 Bonsai CLI as execution engine
- AI automation layer only interprets commands; does not replace CLI
- Natural language → SP.Plan → Bonsai ensures Phase-2 backward compatibility

# ------------------------
# FINAL CLAUDE READY NOTES
# ------------------------
- Copy paste this file entirely into Claude
- Claude can process SP.Plan, SP.Task and execute Bonsai commands automatically
- Phase-3 fully automates todo management
- Constitution validation make start to end complete

## Response snapshot

Updated `.specify/memory/constitution.md` from v1.0.0 to v2.0.0 with:

1. **Phase Evolution Model**: Documented all three phases (Console → Web/CLI → AI Chatbot) with objectives, deliverables, and execution constraints

2. **Four New Principles (VII-X)**:
   - VII: AI as Interpreter, Not Executor - AI only interprets, Bonsai CLI executes
   - VIII: Backward Compatibility Across Phases - Each phase works with prior phases
   - IX: Intent Preservation - NL interpretation preserves user intent with high fidelity
   - X: Graceful AI Degradation - AI failures don't block core functionality

3. **Phase 3 AI Stack**: Added Claude API/OpenAI, NLP Interpreter, SP.Plan Generator, Bonsai CLI, Conversation Store

4. **Updated Project Structure**: Added `backend/src/ai/` and `backend/src/cli/` directories

5. **Bonsai CLI Command Reference**: Documented all core commands (add, list, update, delete, complete) with syntax

6. **Dataset Schema**: Defined task and conversation history JSON schemas

## Outcome

- ✅ Impact: Major version bump (1.0.0 → 2.0.0) - Added Phase 3 AI architecture and 4 new principles
- 🧪 Tests: n/a (constitution is specification document)
- 📁 Files: 1 modified (.specify/memory/constitution.md)
- 🔁 Next prompts: /sp.specify for Phase 3 AI Chat feature, /sp.plan for implementation planning
- 🧠 Reflection: Constitution now fully documents the three-phase evolution with clear architectural boundaries between AI interpretation and CLI execution

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Template compatibility verified - PASS
- Prompt variant (if applicable): n/a
- Next experiment: Test Phase 3 spec generation against new constitution principles
