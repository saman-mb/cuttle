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
3. **Deep Agents is bootstrap only.** It may implement `AgentRuntime` early. It is not the product and must not be the outer router (`task` / subagents are disabled for routing).
4. **Two graphs:** outer Cuttle LangGraph orchestrator; inner brain/hands agent loops.
5. **Local provisioner (llmfit → download → deploy) is first-class.** Do not assume the user already set up Ollama by hand as the only path.
6. **Default concurrency:** one hands writer. Optional read-only scouts later. No swarm-as-default.

---

## 3. Language and stack

- **Language: Python 3.12+** (see `pyproject.toml`).
- **Packaging:** `src/cuttle/` layout; install editable with `pip install -e ".[dev]"`.
- **Orchestrator:** LangGraph `StateGraph`.
- **Models / tools:** LangChain (`init_chat_model`, tools, middleware).
- **Bootstrap agent runtime:** Deep Agents (`create_deep_agent`) behind `AgentRuntime`.
- **End-state agent runtime:** Cuttle-owned loop (still LangGraph / `create_agent`); Deep Agents removable.
- **Schemas:** Pydantic v2 in `contracts` (or `src/cuttle/contracts`).
- **CLI:** intended entrypoint `cuttle` (Typer or Click when implemented).
- **Tests:** pytest.
- **Lint/format:** ruff (when configured).

Do not introduce a second primary language for the core CLI without an explicit decision in docs.

---

## 4. Repo layout (target)

```text
src/cuttle/
  cli/              # cuttle entrypoint
  orchestrator/     # LangGraph phase machine
  contracts/        # Directive, Step, EvalReport, …
  agents/           # AgentRuntime + Deep Agents adapter
  middleware/       # scope guard, stuck detector
  evals/            # deterministic checks
  backends/         # model factory, local runtimes
  provisioner/      # llmfit + HF/download + deploy
docs/               # HLA, architecture, viability, diagrams
```

Top-level placeholder dirs may still exist from the scaffold; prefer implementing under `src/cuttle/` going forward.

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
4. `DeepAgentsRuntime` adapter (brain read-only + hands)
5. Thin CLI (`cuttle implement` stub OK)
6. Provisioner (llmfit path)
7. Replace Deep Agents with native runtime later

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
