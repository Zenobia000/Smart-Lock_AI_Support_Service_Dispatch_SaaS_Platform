# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Smart Lock AI Support & Service Dispatch SaaS Platform — an AI-powered LINE Bot customer service system for smart lock troubleshooting, with technician dispatch and accounting (V2.0).

- **V1.0**: LINE Bot AI customer support, ProblemCard diagnosis, three-layer resolution engine, self-evolving knowledge base, admin panel
- **V2.0**: Technician workbench, smart dispatch, pricing engine, accounting system

**Current status**: Planning phase — comprehensive documentation and database schema are complete; no application code exists yet.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+, async), Uvicorn, SQLAlchemy 2.0 async |
| Frontend (V2.0) | Next.js 14+ (React, TypeScript, Server Components) |
| Database | PostgreSQL 16 + pgvector 0.7+ |
| Cache | Redis 7+ (session management, rate limiting) |
| LLM | Google Gemini 3 Pro via LangChain 0.3.x |
| Embedding | Google text-embedding-004 (768-dim vectors) |
| LINE SDK | line-bot-sdk-python 3+ |
| Infra | Docker + Docker Compose |

## Architecture

**Pattern**: Modular Monolith with Clean Architecture (Domain → Application → Infrastructure), organized by DDD bounded contexts.

**Bounded Contexts** (each is an independent Python package under `backend/src/smart_lock/`):
- `customer_service` — LINE Bot interaction, conversation state machine, ProblemCard creation
- `knowledge_base` — Case entries, PDF manual parsing/chunking, embedding, SOP generation
- `dispatch` (V2.0) — Work orders, technician matching
- `accounting` (V2.0) — Pricing rules, invoices, reconciliation
- `user_management` — LINE user binding, admin/technician accounts, RBAC

**Three-Layer Resolution Engine** (core V1.0 flow):
1. **L1**: Vector similarity search against `case_entries` (pgvector cosine, threshold ≥ 0.85)
2. **L2**: RAG pipeline — retrieve `manual_chunks` + Gemini 3 Pro generation
3. **L3**: Human escalation — create support ticket or work order

**Key async constraint**: LINE Webhook must return HTTP 200 within 1 second; all LLM calls (2-10s) are processed asynchronously.

## Repository Structure

```
docs/                    # All design documents (PRD, ADRs, BDD, API spec, architecture)
docs/adrs/               # Architecture Decision Records (ADR-001 through ADR-005)
SQL/Schema.sql           # Complete PostgreSQL schema (V1.0 + V2.0, 768-dim vectors)
RAG_data/                # Product knowledge for RAG ingestion
transcript/              # Domain expert interview transcripts
VibeCoding_Workflow_Templates/  # Development process templates (not project code)
```

**Planned code structure** (defined in `docs/08_project_structure_guide.md`):
```
backend/src/smart_lock/  # FastAPI app, organized by domain
backend/tests/           # pytest + pytest-asyncio
backend/alembic/         # Database migrations
frontend/src/            # Next.js app (V2.0)
configs/prompts/         # LLM system prompt templates
```

## Database

Schema is at `SQL/Schema.sql`. Key design decisions:
- **Vectors are 768-dim** (text-embedding-004), NOT 1536. HNSW indexes with m=16, ef_construction=64.
- `users.line_user_id` is the primary lookup key for LINE consumers; `display_name` is synced from LINE Get Profile API.
- `conversations` ↔ `problem_cards` is 1:1 (UNIQUE FK).
- `manual_chunks.embedding` powers L2 RAG; `case_entries.embedding` powers L1 search.
- All tables with `updated_at` have auto-update triggers.

## Key Documents

| Document | Purpose |
|---|---|
| `docs/02_project_brief_and_prd.md` | Single source of truth — 37 user stories, acceptance criteria |
| `docs/05_architecture_and_design_document.md` | C4 diagrams, DDD contexts, data model, deployment |
| `docs/06_api_design_specification.md` | REST API contracts, auth (JWT + LINE signature), error codes |
| `docs/08_project_structure_guide.md` | Folder conventions, Clean Architecture layer rules |
| `docs/03_behavior_driven_development.md` | BDD scenarios (Gherkin) for all 11 epics |

## Conventions

- **Language**: Documentation is in Traditional Chinese; code and identifiers use English
- **API naming**: Resource paths use lowercase kebab-case (`/problem-cards`), JSON fields use `snake_case`
- **Pagination**: Cursor-based (not offset-based)
- **Dates**: ISO 8601 UTC (`2026-02-17T10:30:00Z`)
- **Commit style**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
