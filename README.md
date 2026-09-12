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

- **Python 3.12+** engine: LangGraph orchestrator + LangChain models/tools + CuttleAgentRuntime + provider hub
- **Rust** interactive TUI (event consumer; no LangGraph in Rust)
- Versioned engine↔TUI event protocol (shared with plain text CLI)
- Typer/plain CLI always available (`--plain` / `NO_COLOR`)
- **Providers:** connect many vendors (`cuttle auth`), browse available models (`cuttle models`), assign to brain/hands/escalate

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# optional local-runtime helpers:
# pip install -e ".[dev,local]"

cuttle version
```

Copy `.env.example` to `.env` when you start wiring models — or use `cuttle auth login` once the provider hub lands (preferred for multi-vendor keys).

## Layout

| Path | Role |
|---|---|
| `src/cuttle/cli/` | Python entry, plain text UI, engine event stream |
| `src/cuttle/orchestrator/` | LangGraph phase machine |
| `src/cuttle/contracts/` | Directive / step / acceptance / run-event schemas |
| `src/cuttle/agents/` | `AgentRuntime` + Cuttle tool-loop implementation |
| `src/cuttle/middleware/` | Scope guard, stuck detector, telemetry |
| `src/cuttle/evals/` | Deterministic checks |
| `src/cuttle/backends/` | Model factory + adapters (native / openai_compat / …) |
| `src/cuttle/providers/` | Vendor registry + model catalog |
| `src/cuttle/auth/` | Credential store (`auth login` / list / logout) |
| `src/cuttle/provisioner/` | llmfit → download → deploy local hands |
| `crates/cuttle-tui/` | Rust interactive TUI (render-only) |
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
