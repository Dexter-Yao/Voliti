# Voliti

> A Leadership Coach for behavioral alignment, built with Gemini 3 for [Gemini Global Hackathon 2025](https://googleai.devpost.com/)

## Overview

Voliti is a coaching agent that helps users build self-leadership through evidence-based behavioral interventions. Unlike traditional diet trackers that count numbers, it trains decision-making capacity under real-life pressure through personalized coaching interactions.

**First scenario:** Weight management for knowledge workers
**Core capability:** Behavioral alignment system extensible to sleep, exercise, focus, and other self-management domains

## Key Features

### 1. Experiential Interventions
AI-generated personalized images for mental rehearsal and cognitive reframing, grounded in behavioral science (Future Self-Continuity, MCII/WOOP, CBT frameworks).

### 2. Composable UI System (A2UI)
Agent dynamically composes interaction interfaces from 7 UI primitives:
- `text`, `image`, `slider`, `text_input`, `number_input`, `select`, `multi_select`

No fixed forms — flexible interactions that adapt to coaching context.

### 3. Multi-Modal Gemini 3 Pipeline
Single interaction flow: **Vision → Reasoning → Generation**

| Gemini Capability | Implementation |
|---|---|
| Agentic Vision | Food photo analysis with bounding boxes + context inference |
| Thought Signatures | Cross-session coaching continuity (multi-day pattern recognition) |
| Thinking Levels | Adaptive reasoning depth |
| Nano Banana Pro | Personalized intervention image generation |
| Mixed text/image output | Analysis + visualization in single response |
| 1M Context | 21-day behavior history pattern analysis |

### 4. Ethical Guardrails
- **Content Boundaries:** No idealized body images, no body comparison, focus on behavioral capability
- **Transparency:** Generated content framed as exploration, not prediction
- **User Control:** Consent required before interventions, dismissal/feedback options

Implementation: [`prompts/intervention_composer_system.j2`](prompts/intervention_composer_system.j2) (lines 55-66)

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed system design.

**High-level components:**
- **Coach Agent** (DeepAgent): Main conversational agent with cross-day memory
- **Intervention Composer** (Subagent): Assembles experiential interventions using Gemini 3 Pro Image
- **A2UI System**: Composable UI protocol for dynamic interactions
- **Behavioral Ledger**: Event-sourced behavior history using virtual file system

## Tech Stack

**AI Models:**
- Gemini 3 (`gemini-3-pro-preview`, `gemini-3-flash-preview`)

**Backend:**
- LangGraph (agent runtime)
- LangChain DeepAgent
- Python 3.12

**Frontend:**
- Next.js 15
- React + TypeScript
- CSS Modules

**Infrastructure:**
- LangGraph Dev Server
- InMemoryStore (demo), Supabase-ready architecture
- Jinja2 prompt templates

## Quick Start

### Option A: Docker (Recommended for reviewers)

```bash
# 1. Clone and configure
git clone https://github.com/Dexter-Yao/Voliti.git
cd Voliti
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 2. Start with Docker Compose
docker compose up --build

# 3. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:2024
```

### Option B: Local Development

#### Prerequisites
- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

#### Setup

1. **Install dependencies**
```bash
uv sync
cd frontend && npm install
```

2. **Configure API keys**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. **Start backend**
```bash
uv run langgraph dev --port 2024
```

4. **Start frontend** (new terminal)
```bash
cd frontend && npm run dev
```

5. **Access application**
```
http://localhost:3000
```

See [`README_DEV.md`](README_DEV.md) for detailed development setup including LangGraph Studio debugging.

## Project Structure

```
.
├── src/voliti/          # Backend agent system
│   ├── agent.py              # Coach agent factory
│   ├── a2ui.py               # A2UI component models
│   ├── tools/
│   │   ├── fan_out.py        # A2UI interaction tool
│   │   └── experiential.py   # Intervention composition
│   └── config/
│       ├── models.py         # LLM configuration registry
│       └── prompts.py        # Prompt template registry
├── prompts/                  # Jinja2 prompt templates
│   ├── coach_system.j2
│   └── intervention_composer_system.j2
├── frontend/                 # Next.js application
│   └── src/
│       ├── components/
│       │   ├── ChatContainer.tsx
│       │   └── fanout/
│       │       └── A2UIRenderer.tsx
│       └── lib/
│           └── types.ts      # Shared type definitions
├── config/
│   └── models.toml           # LLM model configurations
└── tests/                    # Test suite
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/voliti/a2ui.py` | A2UI component type definitions |
| `src/voliti/tools/fan_out.py` | A2UI interaction tool |
| `src/voliti/tools/experiential.py` | Experiential intervention composition |
| `prompts/intervention_composer_system.j2` | Intervention subagent system prompt with ethical constraints |
| `frontend/src/components/fanout/A2UIRenderer.tsx` | A2UI component renderer (7 primitives) |
| `frontend/src/lib/types.ts` | Frontend type definitions |

## License

MIT

## Acknowledgments

Built with Gemini 3 for Gemini Global Hackathon 2025.

Theoretical foundations:
- Future Self-Continuity (Hershfield)
- MCII/WOOP (Oettingen)
- Conceptual Metaphor Theory (Lakoff & Johnson)
- Cognitive Behavioral Therapy frameworks
