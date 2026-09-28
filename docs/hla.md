# Cuttle — high-level architecture (end state)

> Product authority: [`docs/brief.md`](brief.md). This HLA is the engineering reading of that brief.

## One paragraph

Cuttle is a **single Python program**: Textual (or headless) in front, a LangGraph agent core in the middle, and a LiteLLM-backed **model pool (≤5)** plus a typed **`decide()`** layer underneath. Every step is classified (C0–C4 + kind), scored for per-model success by Jev (or a local Jev-style model), routed to the cheapest eligible model above the preset threshold, verified by deterministic checks, and recorded in a routing ledger. Privacy, budgets, and escalation are enforced in code — not left to an LLM’s good manners.

## Request flow

```text
User (TUI / headless / ACP)
        │
        ▼
   Planner ── decide: plan? clarify? ──► steps sized to target context windows
        │
        ▼
   For each step:
     decide: class + kind + P(success|model) for pool
     router: privacy filter → pick model (preset) → LiteLLM call
     tools: edit / shell / search / git / MCP  (worktree if sub-agent)
     verifier: tests · lint · types · decide: done?
     on fail: decide retry | escalate | ask
        │
        ▼
   Integrator (merge worktrees) → one diff + cost receipt + ledger write
```

## Layers

### Interfaces

| Surface | Role |
|---|---|
| Textual TUI | Plan view, live steps, diffs, `/why`, `/cost`, approvals |
| Headless | `cuttle run`, GitHub Action, JSON |
| ACP | Zed / JetBrains / Neovim now; VS Code later if ACP is not enough |

### Agent core (LangGraph)

- **Planner** — split request; size steps to chosen models
- **Agent loop / sub-agents** — one git worktree per parallel writer; SQLite checkpoints
- **Verifier** — tests, lint, typecheck = definition of done
- **Integrator** — merge worktrees, re-run checks, one combined diff

### Decision layer

```python
def decide(state: DecisionState, questions: list[Question]) -> list[Answer]:
    """Typed answers with calibrated probabilities. Never writes code."""
```

Backends: hosted Jev → local Winnow-12B / mini-jev → (cloud-only) cheapest pool model structured-output fallback.

Safety & privacy sit beside `decide()`: approval modes, command-risk classification, gitleaks, local-only paths, OS sandbox (bubblewrap / Seatbelt).

### Router (LiteLLM library)

Pool config (`pool.yaml`), capability profiles, preset thresholds, fallbacks, budgets, cost logging, normalised tool/edit formats, privacy filter (local-only never to cloud).

### Model pool

- Up to **five** coding models (cloud and/or local)
- **Outside the five:** decision model, embedding model
- Local: llama-swap → llama.cpp (or MLX on Mac)
- Optional shared LiteLLM **proxy** when two machines or a company gateway share one address (`local-fast`, `local-strong`, `decide`, `embed` role names)

### Local stores (files on disk)

| Store | Contents |
|---|---|
| Repo index | tree-sitter map + sqlite-vec embeddings |
| Session store | checkpoints, transcripts, replay |
| Routing ledger | outcome per step: class, kind, model, pass/fail, cost, time |
| Config | `pool.yaml`, AGENTS.md, skills, privacy rules |

## Complexity, kinds, presets

See brief. Classes C0–C4; kinds explore/edit/test/review/summarise; presets Thrifty / Balanced / Best quality / Local only.

## Hard problems (must design for)

Documented in the brief: unknown difficulty → cascade; context-window mismatch; tool-skill mismatch; switching costs; single-GPU scheduling; parallel merge; model format quirks; prompt injection; proving routing vs baselines.

## Build phases

Follow brief phases **01–10**. Kill criteria are the “Done when” lines there. Do not claim routing wins without phase-03 baselines and a phase-05 pass-rate×cost chart.

## Implementation checklist (summary)

- [ ] LiteLLM pool + cost logging; cloud-only path with no local setup
- [ ] `decide()` + Winnow; then hosted Jev
- [ ] `cuttle init` (providers, catalog, optional local detect, pool of ≤5)
- [ ] Single-model agent loop + core tools + approvals + checkpoints
- [ ] Eval harness + single-model baselines
- [ ] Repo map + embeddings + `decide()` context filter
- [ ] C0–C4 routing + presets + `/why` + pre-run cost estimate
- [ ] Planner + worktree sub-agents + cascade + integrator
- [ ] Local-only paths, gitleaks, command risk, sandbox, injection suite
- [ ] Routing ledger + calibration + session replay
- [ ] Textual TUI, headless/GHA, ACP, MCP, skills, slash, hooks
- [ ] OpenTelemetry, packaging (uv/pipx/Homebrew), docs, demo

## Explicitly not day-one

- Rust interactive TUI as primary UI (optional later front-end only)
- Brain/hands/escalate **role pins** as the product model (superseded by per-step pool routing)
- Hosted Cuttle SaaS, custom graphical IDE, training coding models, multi-user sessions
