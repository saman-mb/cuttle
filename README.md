# Cuttle

**Frontier mind. Local hands.**

Cuttle is an agentic coding CLI (Python) that separates expensive reasoning from cheap execution:

1. A frontier **brain** inspects the repo and emits a detailed, prescriptive **directive**
2. A local (or cheap) **hands** agent executes one bounded step at a time
3. A deterministic **orchestrator** owns model binding, retries, and eval gates — not the LLM

> Pre-alpha scaffold. See [docs/hla.md](docs/hla.md).

```text
cuttle implement "add admin login UI"
        │
        ▼
   Brain (frontier) ──► Directive
        │
        ▼
   Hands (local) × N steps
        │
        ▼
   Evals (tests / scope / files) ──► retry / escalate / done
```

## Stack

- **Python 3.12+**
- LangGraph (orchestrator) + LangChain (models/tools)
- Deep Agents optional (`[deepagents]`) as bootstrap `AgentRuntime`
- Typer CLI entrypoint: `cuttle`

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# optional bootstrap runtime + local helpers:
# pip install -e ".[dev,deepagents,local]"

cuttle version
```

Copy `.env.example` to `.env` when you start wiring models.

## Layout

| Path | Role |
|---|---|
| `src/cuttle/orchestrator/` | LangGraph phase machine |
| `src/cuttle/contracts/` | Directive / step / acceptance schemas |
| `src/cuttle/agents/` | `AgentRuntime` + Deep Agents adapter |
| `src/cuttle/middleware/` | Scope guard, stuck detector, telemetry |
| `src/cuttle/evals/` | Deterministic checks |
| `src/cuttle/backends/` | Model factories (frontier + local) |
| `src/cuttle/provisioner/` | llmfit → download → deploy local hands |
| `src/cuttle/cli/` | `cuttle` entrypoint |
| `docs/` | HLA, architecture, viability, diagrams |
| `AGENTS.md` | Instructions for all coding harnesses |

Legacy top-level placeholder dirs (if present) are unused; implement under `src/cuttle/`.

## Docs

- [HLA (end state)](docs/hla.md) — target architecture, orchestration loop, LangChain integration
- [Architecture](docs/architecture.md) — design rationale and diagrams
- [Viability](docs/viability.md) — harness vs prompts in Claude Code / Codex

## Agent instructions (every harness)

One file drives Claude Code, Codex, Cursor, Copilot, OpenCode, etc.:

| File | Role |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Source of truth |
| `CLAUDE.md` | Symlink → `AGENTS.md` (Claude Code) |
| [`.github/copilot-instructions.md`](.github/copilot-instructions.md) | Copilot pointer |
| [`opencode.json`](opencode.json) | OpenCode `instructions` → `AGENTS.md` |

Edit **`AGENTS.md` only**.

## License

MIT
