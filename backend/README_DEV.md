# Voliti Development Guide

## Environment Setup

### Prerequisites
- Python 3.12+
- `uv` package manager
- Azure OpenAI credentials（AZURE_OPENAI_API_KEY、AZURE_OPENAI_ENDPOINT、AZURE_OPENAI_API_VERSION）

### Initial Setup

1. **Clone and install dependencies**
```bash
git clone <repo-url>
cd voliti/backend
uv sync
```

2. **Configure environment**
```bash
# Set Azure OpenAI credentials
export AZURE_OPENAI_API_KEY="your-key-here"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_VERSION="2024-02-01"

# (Optional) Copy and edit model config
cp config/models.toml.example config/models.toml
```

## Running the Application

### Backend (LangGraph API)

**Standard mode** (local only):
```bash
uv run langgraph dev --port 2025
```

**Tunnel mode** (for LangGraph Studio):
```bash
uv run langgraph dev --port 2025 --tunnel
```

The `--tunnel` flag creates a Cloudflare HTTPS tunnel for Studio access. Each run generates a new temporary domain.

**Expected output:**
```
🚀 API: http://127.0.0.1:2025
🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=https://xxx-xxx.trycloudflare.com
📚 API Docs: https://xxx-xxx.trycloudflare.com/docs
```

iOS 客户端位于 `frontend-ios/`，使用 Xcode 打开 `Voliti.xcodeproj`。

## Development Workflow

### Using LangGraph Studio

LangGraph Studio provides visual debugging for agent execution.

**Access:** Open the Studio UI URL from backend startup output

**First-time setup:**
1. Go to Studio URL
2. Click **Advanced Settings** (bottom of page)
3. Add the tunnel domain to allowed list
4. Refresh page

**Studio Features:**

| Feature | Usage |
|---------|-------|
| **Chat Mode** | Test conversations directly |
| **Graph Mode** | Visualize agent execution flow (nodes highlight in sequence) |
| **Tool Inspection** | Click tool nodes to see arguments and results |
| **State Snapshots** | Right panel shows state at each node |
| **Step-through** | Pause and advance execution node-by-node |
| **Interrupt Handling** | Manually respond to agent interrupts (A2UI interactions) |

**Debugging Tips:**
- Use Graph mode to identify where agent gets stuck
- Inspect tool calls to verify file system operations
- Check State panel for memory loading (AGENTS.md, context.md)
- Monitor SummarizationMiddleware triggers (at 85% context)

### Testing

**Run all tests:**
```bash
uv run pytest
```

**Run specific test file:**
```bash
uv run pytest tests/test_a2ui.py
```

**Run with coverage:**
```bash
uv run pytest --cov=src/voliti
```

### Code Style

Project uses:
- **Type hints:** Full type annotations required
- **Docstrings:** Google-style docstrings
- **Formatting:** (Configure with your preferred formatter)

## Project Structure

```
.
├── src/voliti/           # Backend Python package
│   ├── agent.py               # Coach agent factory
│   ├── graph.py               # LangGraph dev server entry
│   ├── bootstrap.py           # Registry initialization
│   ├── a2ui.py                # A2UI component models
│   ├── tools/
│   │   ├── fan_out.py         # A2UI interaction tool
│   │   └── experiential.py    # Intervention composition tool
│   └── config/
│       ├── models.py          # ModelRegistry (LLM config)
│       └── prompts.py         # PromptRegistry (Jinja2 templates)
├── prompts/                   # Jinja2 system prompt templates
│   ├── coach_system.j2
│   └── intervention_composer_system.j2
├── config/
│   └── models.toml            # LLM model configurations
├── tests/                     # Pytest test suite
└── langgraph.json             # LangGraph graph registration
```

> iOS 客户端位于 `frontend-ios/`，使用 Xcode 打开 `Voliti.xcodeproj`。

## Key Development Tasks

### Adding a New A2UI Component

1. **Define component model** (`src/voliti/a2ui.py`):
```python
class NewComponent(BaseModel):
    kind: Literal["new_component"]
    name: str
    # ... component-specific fields
```

2. **Add to union type**:
```python
Component = text | image | slider | ... | NewComponent
```

3. **Implement iOS renderer** (`frontend-ios/...A2UITypes.swift` + `A2UIRenderer.swift`):
```swift
case "new_component":
    NewComponentView(component: component)
```

### Adding a New Intervention Type

1. **Update intervention_composer_system.j2**:
   - Add intervention type documentation
   - Define theoretical framework
   - Specify prompt construction rules

2. **Add to purpose enum** (`src/voliti/tools/experiential.py`):
```python
InterventionPurpose = Literal[..., "new_type"]
```

3. **Update frontend purpose labels** (if needed)

### Modifying System Prompts

System prompts use Jinja2 templates in `prompts/` directory.

**Example:**
```jinja2
{# prompts/coach_system.j2 #}
You are a leadership coach specializing in {{ domain }}.

Your role:
- Help users build self-leadership through {{ methodology }}
- ...
```

**Rendering with variables:**
```python
prompt = PromptRegistry.get("coach_system", domain="weight management", methodology="S-PDCA")
```

**Best practices:**
- Use `StrictUndefined` mode (undefined variables throw errors)
- Keep prompts version-controlled
- Document required variables in comments

### Working with Behavioral Ledger

The ledger uses a virtual file system abstracted by DeepAgent.

**Write event:**
```python
# In agent tool or system prompt instruction
write_file(
    path="/user/ledger/2026-02-09/143052_meal.json",
    content={
        "ts": "2026-02-09T14:30:52Z",
        "type": "meal",
        "evidence": "User said: 'I had a salad for lunch'",
        "summary": "Mixed greens salad",
        "tags": ["lunch", "healthy"],
    }
)
```

**Query patterns:**
```python
# List events in date range
glob("/user/ledger/2026-02-*/")

# Search for keyword in evidence
grep(pattern="stress", path="/user/ledger/")

# Read specific event
read_file("/user/ledger/2026-02-09/143052_meal.json")
```

## Debugging Common Issues

### Backend won't start

**Symptom:** `uv run langgraph dev` fails

**Check:**
1. Python version: `python --version` (must be 3.12+)
2. Dependencies: `uv sync`
3. API key: `echo $AZURE_OPENAI_API_KEY`
4. Port conflict: Try different port with `--port 2025`

### A2UI interrupt not rendering

**Symptom:** A2UI panel doesn't appear in iOS client

**Debug:**
1. Verify `stream.interrupt` received in SSE stream
2. Inspect interrupt payload structure (should match A2UIPayload type)
3. Check A2UIRenderer.swift for unhandled component kind
4. Review Xcode console for decoding errors

### Agent memory not persisting

**Symptom:** Coach forgets previous sessions

**Remember:** InMemoryStore clears on server restart (by design for demo)

**For persistence:**
- Implement Supabase backend
- Or use file-based store for development

### Intervention images not generating

**Symptom:** Experiential interventions fail

**Check:**
1. Azure OpenAI credentials valid and gpt-image-1.5 deployment accessible
2. Prompt length (very long prompts may fail)
3. Ethical constraints not blocking content
4. Check agent logs for API errors

## Performance Tips

### Reducing Context Window Usage

- SummarizationMiddleware triggers at 85% → adjust in `src/voliti/graph.py`
- Keep system prompts concise
- Regularly archive old conversation history

### Speeding Up Development Iteration

- Use `--no-tunnel` flag (faster startup without Cloudflare tunnel)
- Backend: Restart required for code changes (no hot-reload)

### Optimizing LLM Calls

- Cache intervention images (already implemented in experiential.py)
- `azure_openai:gpt-5.4`: Main Coach Agent
- `azure_openai:gpt-5.4-nano`: Intervention Composer subagent
- `gpt-image-1.5`: 图片生成（experiential.py 直接调用）
- Batch multiple A2UI components in single interrupt

## Deployment

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for production deployment strategy (Vercel + LangGraph Cloud + Supabase).

Demo deployment uses:
- InMemoryStore (ephemeral)
- Local dev server
- No authentication

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [DeepAgent Guide](https://github.com/deeplearning-ai/deepagents)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)

## Getting Help

- Check [`ARCHITECTURE.md`](ARCHITECTURE.md) for system design details
- Review tests for usage examples
- Use LangGraph Studio for visual debugging
- Check LangGraph logs for detailed execution traces
