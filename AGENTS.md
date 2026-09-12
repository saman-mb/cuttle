# Cuttle — agent instructions

> **Shared instructions for every coding harness.** This file is the source of truth for Cursor, Codex CLI, OpenCode, GitHub Copilot, Windsurf, Antigravity, and anything else that reads `AGENTS.md`. Claude Code reads the same content via `CLAUDE.md` (symlink). Keep this file tool-neutral: no harness-specific spawn syntax, no "use the Task tool" assumptions.

**Product:** Cuttle — frontier mind, local hands. An agentic coding CLI that plans on a frontier model and executes on local (or cheap) hands under a deterministic orchestrator.

**Repo status:** Scaffold + docs. Little or no runtime code yet. Prefer docs and structure over inventing APIs.

---

## 1. What you must know before changing code

Read, in order, if the task touches architecture or the agent loop:

1. [`docs/hla.md`](docs/hla.md) — end-state architecture, orchestration loop, LangGraph/LangChain integration, implementation checklist
2. [`docs/architecture.md`](docs/architecture.md) — design rationale and diagrams
3. [`docs/viability.md`](docs/viability.md) — why a harness beats prompts in Claude Code / Codex

Do not invent a different control plane than the HLA.

---

## 2. Hard product rules

1. **Orchestrator owns phases and model binding.** Never let an LLM choose which model is brain vs hands, or advance steps on vibes.
2. **Brain plans; hands execute.** Brain emits a structured `Directive`. Hands run one `Step` at a time. Evals (deterministic) gate progress.
3. **Own the agent runtime from day one.** Brain/hands run on Cuttle’s tool loop (`create_agent` / LangGraph model↔tools), not Deep Agents. No third-party `task` / subagent router — ever.
4. **Two graphs:** outer Cuttle LangGraph orchestrator; inner brain/hands agent loops (also Cuttle-owned).
5. **Local provisioner (llmfit → download → deploy) is first-class.** Do not assume the user already set up Ollama by hand as the only path.
6. **Provider hub is first-class.** Many vendors via a registry + adapters; easy auth (`cuttle auth` / `/connect`); catalog makes models available; operators assign to brain/hands/escalate. Secrets stay in the auth store — not in committed config. Orchestrator still pins roles; agents do not self-select providers mid-run.
7. **Default concurrency:** one hands writer. Optional read-only scouts later. No swarm-as-default.
8. **Process split:** Python owns the engine (LangGraph + runtime + evals + provisioner + provider hub). The interactive TUI is a **Rust** binary that renders a versioned event stream from the engine — it must not own phases, model binding, or evals.

---

## 3. Language and stack

- **Engine language: Python 3.12+** (see `pyproject.toml`) — LangGraph orchestrator, `CuttleAgentRuntime`, evals, provisioner, thin Typer/text CLI.
- **TUI language: Rust** — fast interactive terminal UI; consumes engine events only (no LangGraph in Rust; no official Rust LangGraph).
- **Packaging:** `src/cuttle/` for the Python engine; Rust TUI crate under e.g. `crates/cuttle-tui/` (or equivalent). Engine install: `pip install -e ".[dev]"`.
- **Orchestrator:** LangGraph `StateGraph` (Python only for this product).
- **Models / tools:** LangChain (`init_chat_model`, tools, middleware) behind a modular provider hub (registry → auth → catalog → factory).
- **Agent runtime:** Cuttle-owned (`AgentRuntime` → `create_agent` and/or hand-rolled LangGraph tool loop). Do not add Deep Agents as a dependency.
- **Providers:** native adapters for first-class vendors; `openai_compat` catch-all for long-tail + local; optional thin adapters (Bedrock/Azure) when needed. Do not hardcode vendor lists into the orchestrator.
- **Model controls:** `ModelRef` may set context depth, effort, thinking/budget, and sampling — applied only when the provider/model capability profile supports them; unsupported knobs fail closed (no silent ignore), especially for brain.
- **Wire protocol:** versioned NDJSON / JSON-RPC-style events (status lexicon, usage, step progress) shared by text CLI and Rust TUI.
- **Schemas:** Pydantic v2 in `contracts` (or `src/cuttle/contracts`).
- **CLI:** `cuttle` entry — Rust TUI as default interactive path when available; Python text/`--plain` always works.
- **Tests:** pytest (engine); Rust tests for TUI crate.
- **Lint/format:** ruff (Python); rustfmt/clippy (TUI).

Do not introduce a third language for the engine or move orchestration into Rust. Do not use community “LangGraph for Rust” as the control plane.

---

## 4. Repo layout (target)

```text
src/cuttle/
  cli/              # thin Python entry / plain text / engine spawn helpers
  orchestrator/     # LangGraph phase machine
  contracts/        # Directive, Step, EvalReport, run events…
  agents/           # AgentRuntime + Cuttle tool-loop implementation
  middleware/       # scope guard, stuck detector
  evals/            # deterministic checks
  backends/         # model factory, adapters
  providers/        # vendor registry + catalog
  auth/             # credential store (login/list/logout)
  provisioner/      # llmfit + HF/download + deploy
crates/
  cuttle-tui/       # Rust interactive TUI (event consumer only)
docs/               # HLA, architecture, viability, diagrams
```

Prefer implementing the engine under `src/cuttle/`. Rust TUI lives under `crates/` (or equivalent). Do not put orchestration in the TUI crate.

---

## 5. How to work in this repo

- **Docs-first for architecture.** If behaviour changes, update `docs/hla.md` (and diagrams if the loop changes).
- **Diagrams:** use Shipmates `diagram` JSON → SVG under `docs/diagrams/` (not Mermaid-as-source-of-truth).
- **No secrets in git.** Use `.env.example` only; real keys stay local.
- **Small diffs.** Match existing style; do not drive-by refactor.
- **Do not commit** unless the user asks.
- **British English** in user-facing docs and CLI help copy.
- **No corporate hype** in docs ("game-changing", "revolutionary", etc.).
- Prefer plain language over sales tone.

---

## 6. Implementation order (from HLA)

When building runtime (only if asked):

1. Contracts (Pydantic)
2. Eval engine
3. Orchestrator LangGraph
4. Cuttle `AgentRuntime` (brain read-only + hands tool host)
5. Thin CLI (`cuttle implement` stub OK) + **versioned run-event stream**
6. Provisioner (llmfit path)
7. Peer-class harness polish (streaming, stuck detection, tool reliability) — still owned Python code
8. Rust coastal TUI consuming the same events (E5)

---

## 7. Harness compatibility note

These files exist so *other* agent CLIs behave the same while developing Cuttle:

| File | Consumed by |
|---|---|
| `AGENTS.md` | Codex, Cursor, OpenCode (often), Windsurf, shared Agent Skills world |
| `CLAUDE.md` | Claude Code (symlink → `AGENTS.md`) |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `opencode.json` `instructions` | OpenCode (points at `AGENTS.md`) |

Edit **`AGENTS.md` only**. Do not fork conflicting rules into harness-specific copies.

Cuttle-the-product will later ship its own skills/commands for *end users*; that is separate from these *developer* instructions for working on this repository.
