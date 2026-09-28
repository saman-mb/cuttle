# Cuttle — agent instructions

> **Shared instructions for every coding harness.** Source of truth for Cursor, Codex CLI, OpenCode, GitHub Copilot, and anything that reads `AGENTS.md`. Claude Code reads the same content via `CLAUDE.md` (symlink). Keep this file tool-neutral.

**Product:** Cuttle — a local-first coding agent that routes each step to the cheapest model likely to pass, using **Jev** (`decide()`) for calibrated decisions. Tagline: *like a cuttlefish, it changes to suit the job.*

**Authoritative brief:** [`docs/brief.md`](docs/brief.md). If anything here conflicts with the brief, **the brief wins**.

**Repo status:** Scaffold + docs. Prefer docs and structure over inventing APIs.

---

## 1. What you must know before changing code

Read, in order, if the task touches architecture or the agent loop:

1. [`docs/brief.md`](docs/brief.md) — product, phases, Jev, stack, limits
2. [`docs/hla.md`](docs/hla.md) — end-state architecture and build checklist
3. [`docs/architecture.md`](docs/architecture.md) — design rationale
4. [`docs/viability.md`](docs/viability.md) — why a purpose-built harness vs configuring peers

Do not invent a different control plane than the brief / HLA.

---

## 2. Hard product rules

1. **Pool ≤ 5 coding models.** Decision (Jev / Winnow) and embedding models sit **outside** the five. Cloud-only, mixed, and local-only pools are all first-class.
2. **`decide()` owns judgement; coding models own edits.** Jev never writes code. Deterministic checks (tests, lint, types, gitleaks, allow-lists) are ground truth; Jev handles what those cannot.
3. **Complexity class + kind gate eligibility.** Steps are C0–C4 and explore/edit/test/review/summarise. The class (not the user ad-hoc) decides which models may run the step. Presets: Thrifty / Balanced / Best quality / Local only.
4. **Cascade on failure.** Start at the predicted tier; escalate (or ask) when checks fail. Log every decision with its probability for `/why`, replay, and the routing ledger.
5. **Privacy is a routing rule.** Local-only paths never go to cloud, whatever the preset. Secret scan before cloud; `decide()` as a second check.
6. **One edit format.** Search-and-replace blocks (unified-diff fallback), normalised in the LiteLLM gateway so every pool model is tested the same way.
7. **Sub-agents isolate in git worktrees.** Integrator merges and re-runs checks. Default is not an unbounded swarm.
8. **Python owns the product.** LangGraph agent core, LiteLLM router (library), Textual TUI, evals, provisioner/gateway glue. Editors via ACP. A Rust CLI front-end is optional later — **not** the day-one interactive path.
9. **Evals before routing claims.** Phase 03 baselines (“frontier for everything”, each model alone, “local only”) exist before phase 05 routing is declared a win. Be honest if routing does not win.
10. **No hosted Cuttle service.** Users bring their own keys. No custom graphical IDE.

---

## 3. Language and stack

- **Language:** Python 3.12+ (`pyproject.toml`)
- **Orchestration:** LangGraph (planner, agent loop, sub-agents, verifier, integrator) + SQLite checkpointer
- **Router / gateway:** LiteLLM as a library (Router); optional shared LiteLLM proxy for multi-machine / company gateway
- **Decision:** typed `decide(state, questions)` → hosted Jev or local Jev-style (Winnow-12B / mini-jev)
- **Local models:** llama-swap → llama.cpp (Linux); MLX / LM Studio (Mac); Ollama as a simpler option
- **Code understanding:** tree-sitter repo map, ripgrep, embeddings in sqlite-vec or LanceDB
- **TUI:** Textual (plan view, live steps, diffs, `/why`, `/cost`)
- **Headless:** `cuttle run`, GitHub Action, JSON output
- **Editors:** Agent Client Protocol (ACP)
- **MCP:** official MCP Python SDK as client
- **Schemas:** Pydantic v2 under `src/cuttle/contracts`
- **Tests:** pytest; promptfoo for decision/prompt regressions
- **Lint/format:** ruff
- **Packaging:** uv or pipx + Homebrew (phase 10)

Do not move the agent core to Rust. Do not add Deep Agents as a dependency. Do not treat “brain vs hands role pins” as the product — that was the previous sketch; the brief’s **per-step pool routing via `decide()`** is the product.

---

## 4. Repo layout (target)

```text
src/cuttle/
  cli/              # cuttle init | run | doctor | …
  tui/              # Textual interface
  agent/            # LangGraph planner, loop, sub-agents, verifier, integrator
  decide/           # decide() + Jev / local backends
  router/           # LiteLLM pool, presets, privacy filter, budgets, cost
  tools/            # edit, shell, search, git, MCP
  index/            # repo map, embeddings
  ledger/           # routing ledger + session store
  evals/            # harness, baselines, calibration
  sandbox/          # worktrees, bubblewrap/Seatbelt glue
  contracts/        # Pydantic schemas
docs/               # brief, HLA, architecture, viability, assets
```

Prefer implementing under `src/cuttle/`. Do not invent a parallel engine layout that contradicts the brief.

---

## 5. How to work in this repo

- **Brief-first for product.** Behaviour changes update `docs/brief.md` and `docs/hla.md`.
- **Diagrams:** Shipmates `diagram` JSON → SVG under `docs/diagrams/` when the loop changes.
- **No secrets in git.** `.env.example` only.
- **Small diffs.** Match existing style; no drive-by refactors.
- **Do not commit** unless the user asks.
- **British English** in user-facing docs and CLI help.
- **No corporate hype** ("game-changing", "revolutionary").
- Plain language over sales tone.

---

## 6. Implementation order (from the brief)

When building runtime (only if asked), follow phases **01 → 10**:

1. Pool + LiteLLM + `decide()` (Winnow first, then hosted Jev) + `cuttle init` sketch
2. Single-model LangGraph agent loop + core tools + approvals + checkpoints
3. Eval harness + single-model baselines
4. Repo map + embeddings + context selection via `decide()`
5. C0–C4 routing + presets + `/why` + cost estimates
6. Planner + worktree sub-agents + verifier cascade + integrator
7. Privacy, gitleaks, command risk, sandbox, injection suite
8. Routing ledger + calibration + session replay
9. Textual TUI, headless/GHA, ACP, MCP, skills, slash, hooks
10. OTel, packaging, docs, demo

Optional early spike: **pi extension** routing prototype as a baseline before full LangGraph (see brief).

---

## 7. Harness compatibility note

| File | Consumed by |
|---|---|
| `AGENTS.md` | Codex, Cursor, OpenCode, Windsurf, shared Agent Skills world |
| `CLAUDE.md` | Claude Code (symlink → `AGENTS.md`) |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `opencode.json` `instructions` | OpenCode (points at `AGENTS.md`) |

Edit **`AGENTS.md` only**. Do not fork conflicting rules into harness-specific copies.
