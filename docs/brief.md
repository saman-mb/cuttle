# Cuttle — project brief

> **Authoritative product brief.** Derived from *AI Practice Project Brief — Cuttle* (career development docs, Sep 2026). If HLA, README, AGENTS.md, or the GitHub backlog conflict with this file, **this file wins** until deliberately revised.

**One-liner:** A local-first coding agent that gives every piece of work to the right model. Like a cuttlefish, it changes to suit the job.

---

## Goal

Build a terminal coding agent with the features people expect from Claude Code, Codex CLI, or pi — but around a different idea. Instead of one model doing everything, Cuttle works with a **pool of up to five models**, from frontier cloud down to models on your machine. It breaks each request into pieces, classifies how hard each piece is, and sends it to the cheapest model that is likely to get it right.

Routing is powered by **Jev**, a decision model that answers typed questions with calibrated probabilities. Jev also handles every small yes/no or pick-one decision, so large models are kept for reasoning about code and writing it.

## The product

**Cuttle is a coding agent you run in your terminal, in your editor, or in CI.** You ask for a change; it plans the work, shows which model will do each step and what it should cost, then does it, checks it against your tests, and hands you a diff to review. Easy work runs locally and for free; hard work goes to a frontier model; private code never leaves the machine.

### Who it is for

| Audience | Why |
|---|---|
| Developers | Frontier quality without frontier prices for every rename and test fix |
| Cloud-only users | Cut cost by spreading work across cheaper cloud models (no local hardware) |
| Privacy-bound teams | Fully offline, or route only sensitive parts locally |
| You (the builder) | Learn agent loops, model routing, evals, and local inference in one project |

### The journey

1. **Connect providers and pick the pool.** `cuttle init` connects providers (Anthropic, OpenAI, Google, OpenRouter, Azure, Bedrock, or a company gateway), detects local model servers, lists models with price / context / tool support, suggests up to five across tiers, and lets you edit the pool. Local models are optional.
2. **Calibrate.** A short built-in task set (~30 tasks across complexity classes) measures pass rate, tool-calling reliability, speed, and cost → a **capability profile** per model and an editable routing table.
3. **Ask.** Cuttle splits the request into steps, labels each with class + model + estimated cost/time. You approve, edit, or pin a step.
4. **Watch it work.** Sub-agents run in parallel, each in its own git worktree. A verifier runs tests/lint/types. Failures retry or escalate.
5. **Review and learn.** One combined diff, summary, actual cost. Outcomes feed the routing ledger so routing improves on your codebase.

### Cloud only, local only, or both

Routing saves money whatever the pool is made of. Example pools:

- **Cloud only** — frontier + mid-tier + cheap fast + open-weight via OpenRouter/Groq
- **Mixed** — frontier + mid-tier cloud, plus local Qwen3-Coder / gpt-oss-120b for easy and private work
- **Local only** — up to five local models; offline; free per task; slower

With no local models, GPU scheduling / llama-swap / shared gateway simply switch off.

### Complexity classes

Every step gets one of five classes. The class (not the user) decides which models are eligible.

| Class | Meaning | Example |
|---|---|---|
| **C0 · Look up** | Read and answer; no edits | "Where do we validate API keys?" |
| **C1 · Mechanical** | Small, fully specified edits | Rename; fix this lint |
| **C2 · Contained** | Fix/feature in a few files, with tests | Empty-list case + test |
| **C3 · Cross-cutting** | Many files, real design choices | Memory sessions → Redis |
| **C4 · Open-ended** | Architecture, ambiguous bugs | "Why does this deadlock under load?" |

Each step also has a **kind**: explore, edit, test, review, or summarise (a model weak at writing can still be strong at search).

### Routing presets

| Preset | Behaviour |
|---|---|
| **Thrifty** | Cheapest model likely to pass; frontier only for C4 or after two failures |
| **Balanced** | Default — mix of pass rate, cost, and time |
| **Best quality** | Strongest model for every C2+; local only for look-ups |
| **Local only** | Nothing leaves the machine |

### What every session gets

- File editing, shell, code search, git, MCP, skills, slash commands, `AGENTS.md`, checkpoints with undo
- Approval modes: read-only, ask before changes, automatic within the repo
- Cost estimate before work; real cost after, by model
- `/why` on any step (class, model, probabilities)
- Privacy rules: local-only paths never go to cloud, whatever the preset

### Limits

- Up to **five models** in the pool (decision + embedding models sit outside the five)
- Five complexity classes, five step kinds — nothing finer until evals justify it
- One repository per session, one user, on your machine
- **Terminal first**; editors via **Agent Client Protocol** (not a custom extension per editor)
- **No hosted service** — cloud models use your keys

### Out of scope

- A graphical IDE of its own, or a hosted cloud version
- Training or fine-tuning the coding models themselves
- Multiple users sharing one session

---

## How agentic it gets

| Level | Capability | Note |
|---|---|---|
| 1 | Answer | C0 steps |
| 2 | Edit and check | Tests as definition of done |
| 3 | Route | Model per step; escalate on failure |
| 4 | Coordinate | Plan, parallel sub-agents, merge |
| 5 | Learn | Ledger adjusts routing to your codebase |
| 6 | Background | Issue → PR unattended — **follow-up**, not core |

Levels 1–5 are the core build.

---

## The decision layer: Jev

**Jev** (TypeSafe AI) does not write text. You give it state and typed questions (yes/no, pick one, score); it returns answers with **calibrated probabilities** in one fast pass, several questions at once.

**Core routing call:** for each step, one question per pool model — *"Will this model complete this step and pass the checks?"* — five probabilities, then pick the cheapest model above the preset threshold. Low confidence on class → start one tier higher.

### Where `decide()` is used

| Decision | What Jev answers |
|---|---|
| Plan or just do it? | Single step vs needs a plan |
| Clarify first? | Ambiguous enough to ask the user |
| Complexity class | C0–C4 and kind |
| Model success | Per-model pass probability |
| Context selection | Is this file relevant? |
| Done? | Diff + test output → complete? |
| After failure | Retry, escalate, or ask |
| Command risk | Destructive / networked / outside repo? |
| Privacy | Secrets or restricted code? (after gitleaks) |
| Compaction | Which conversation parts are still needed? |

### Design rules

1. **Deterministic first.** Tests, type checks, secret scanners, allow-lists are ground truth. Jev handles judgement those cannot make.
2. **Jev never writes code.** It only decides.
3. **One interface, two backends.** Typed `decide(state, questions)` — hosted Jev or local Jev-style (Winnow-12B / mini-jev). Local-only mode always uses local. Cloud-only fallback: cheapest pool model with structured output.
4. **A threshold per decision**, from eval data, adjusted per preset.
5. **Log every decision with its probability** — `/why`, replay, and the ledger share one record.
6. **Measure calibration** with reliability diagrams before trusting thresholds.

---

## Hard problems to design for

- Difficulty is often unknown until you try → cascade + confidence
- Different context windows → size steps to the chosen model; hand-off summaries
- Different tool skills → fewer tools / shorter loops for weaker models; record in capability profiles
- Switching costs (prompt cache, local load) → prefer loaded/cached; one model per whole step
- One GPU → local GPU scheduler (prefer loaded, group big-model steps, cap parallel local, never unload decide/embed, cloud when queue is long and privacy allows)
- Merging parallel work → one git worktree per sub-agent; integrator merges + re-checks
- Model quirks → normalise in the gateway; one edit format (search-and-replace) every model is tested on
- Prompt injection → treat README/issues/MCP as data; no network in sandbox by default
- Proving it works → evals must beat "frontier for everything" on cost at same pass rate, or beat "local only" on pass rate

---

## Architecture (at a glance)

| Layer | Pieces |
|---|---|
| **Interfaces** | Textual TUI · headless/`cuttle run`/GitHub Action · editors via ACP |
| **Agent core** | LangGraph planner · agent loop + sub-agents (worktrees) · verifier · integrator · SQLite checkpoints |
| **Decisions** | `decide()` · Jev / local · safety & privacy (approvals, command risk, gitleaks, local-only paths, sandbox) |
| **Tools** | Search-and-replace edit · sandboxed shell · ripgrep + repo map + embeddings · git · MCP |
| **Router** | LiteLLM (library) · pool ≤5 · capability profiles · presets · fallbacks · budgets · cost · normalised tools · privacy filter |
| **Model pool** | Up to 3 cloud slots + local via llama-swap → llama.cpp (or MLX on Mac); hosted Jev with local fallback; decide + embed **outside** the five |
| **Local stores** | Repo index (tree-sitter + sqlite-vec) · session store · routing ledger · `pool.yaml` / AGENTS.md / skills / privacy |
| **All layers** | OpenTelemetry (+ optional Langfuse) · evals (SWE-bench Verified subset, Terminal-Bench, own tasks, routing replay, calibration) |

Cuttle is a **single program you install**, not a set of services. The only other process is the local model server (when used).

---

## Phases (core build)

| # | Phase | Epic | Done when |
|---|---|---|---|
| **00** | Spikes, gateway, publish discipline | [#100](https://github.com/saman-mb/cuttle/issues/100) | Pi spike go/no-go recorded; two-machine gateway stance explicit; decision-log + phase posts |
| **01** | Pool, router, and decision layer | [#89](https://github.com/saman-mb/cuttle/issues/89) | One config defines the pool; cloud-only works with no local setup; any model callable with cost recorded |
| **02** | Single-model agent loop | [#90](https://github.com/saman-mb/cuttle/issues/90) | Fixes a failing test in a sample repo end to end (no routing yet) |
| **03** | Eval harness | [#91](https://github.com/saman-mb/cuttle/issues/91) | Results table for each model alone (baselines before routing) |
| **04** | Understanding the repository | [#92](https://github.com/saman-mb/cuttle/issues/92) | Local model passes more eval tasks with selected context than raw search |
| **05** | Complexity classes and routing | [#93](https://github.com/saman-mb/cuttle/issues/93) | Pass-rate vs cost chart vs single-model baselines (honest if routing does not win) |
| **06** | Planning and sub-agents | [#94](https://github.com/saman-mb/cuttle/issues/94) | Multi-file task with ≥3 models and one clean diff |
| **07** | Safety and privacy | [#95](https://github.com/saman-mb/cuttle/issues/95) | No local-only content reaches cloud in evals; injection suite has a recorded pass rate |
| **08** | Learning router | [#96](https://github.com/saman-mb/cuttle/issues/96) | Routing on your repos improves after ~100 recorded steps |
| **09** | Interfaces and extensibility | [#97](https://github.com/saman-mb/cuttle/issues/97) | Textual TUI, headless + GHA, ACP, MCP, skills, slash, hooks |
| **10** | Observability and packaging | [#98](https://github.com/saman-mb/cuttle/issues/98) | OTel, cost/routing reports, uv/pipx + Homebrew, docs + demo |
| **11** | Follow-ups (after core) | [#99](https://github.com/saman-mb/cuttle/issues/99) | Each nice-to-have deferred or flagged MVP after dependencies |
| **Brand** | README / Pages / demo GIFs / mascot | [#80](https://github.com/saman-mb/cuttle/issues/80) | Public face matches this brief (not the superseded brain/hands sketch) |

Each epic body carries an unchecked story checklist (`- [ ] #<n>`). Open the epic for the full slice list (~80 user stories covering every deliverable in this brief).

**Suggested order note:** build eval harness (03) before trusting routing (05). Prototype routing as a **pi extension** (P00) before the full LangGraph build if useful. Get one model working well before adding a second.

### Follow-ups (not core) — tracked under [#99](https://github.com/saman-mb/cuttle/issues/99)

Background agents · best-of-several · review mode · trained router · shared ledger · native VS Code extension

---

## Recommended stack

| Concern | Choice |
|---|---|
| Language | **Python 3.12+** (LangGraph, LiteLLM, evals). Rust CLI front-end is optional later — not day-one |
| Orchestration | LangGraph + SQLite checkpointer |
| Router / gateway | LiteLLM as a library (Router); optional shared LiteLLM proxy for two machines / company gateway |
| Decision | Jev behind `decide()`; Winnow-12B / mini-jev local |
| Local models | llama.cpp + llama-swap (Framework); MLX / LM Studio (Mac); Ollama supported as simpler option |
| Code understanding | tree-sitter repo map, ripgrep, Qwen3-Embedding or bge-m3 in sqlite-vec/LanceDB |
| Editing | Search-and-replace blocks; unified-diff fallback |
| Sandbox | Git worktrees; bubblewrap (Linux) / Seatbelt (macOS); Docker/Podman optional |
| Secrets | gitleaks + privacy rules |
| Terminal UI | **Textual** (not a Rust TUI as the primary interactive path) |
| Protocols | MCP Python SDK (client); ACP for editors |
| Evals | SWE-bench Verified subset, Terminal-Bench, promptfoo, own labelled set |
| Observability | OpenTelemetry; Langfuse optional |
| Packaging | uv or pipx + Homebrew |

---

## Working rules

1. Get one model working well before adding a second.
2. Prototype routing as a pi extension before the full build; keep its results as a baseline.
3. Build the eval harness (phase 03) before routing. Without baselines you cannot tell whether routing helps.
4. Use Cuttle to build Cuttle once phase 02 works.
5. Keep a decision log — write-ups and interview material.
6. Publish: open repo, results tables, one blog post per phase.

## Path to product

- **Open source:** agent, router, local models, your keys
- **Teams:** shared ledger, pools, budgets, usage reports
- **Enterprise:** central policy, audit logs, company gateway

Check employment IP / outside-interests clauses before selling anything.

## Why build vs configure an existing tool

Configuration (OpenCode / Claude Code / Codex / pi) can approximate model pins. Purpose-built harness value:

- Routing **outside** the expensive model (Jev decides before a large model is involved)
- Calibrated, tunable decisions with thresholds and reliability diagrams
- Guarantees in code (privacy, command risk, escalation), not prompt instructions
- Learning from a per-step routing ledger on your code
- Planning sized to each model's context and tool skills
- Local GPU scheduling with visibility into every sub-agent

**Difference vs peers:** others let the user decide in advance which model does which kind of work. Cuttle decides **per step**, with calibrated probabilities, learns from outcomes, treats privacy as a routing rule, and can run fully offline.
