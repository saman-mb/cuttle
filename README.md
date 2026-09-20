# Cuttle

<p align="center">
  <img src="docs/assets/logo.gif" width="220" alt="Cuttle — animated pixel-art cuttlefish with cycling chromatophore colours (30s seamless loop)" />
</p>

<p align="center">
  <b>Coding agent harness: frontier plans, local implements. The router is code.</b><br/>
  Pin <b>brain</b> / <b>hands</b> / <b>escalate</b> in the orchestrator — so expensive models plan and <b>your</b> local (or cheap) models execute, gated by deterministic evals.
</p>

<p align="center">
  <i>Frontier mind. Local hands.</i> — tagline only; local-first by default.
</p>

[![License: MIT](https://img.shields.io/github/license/saman-mb/cuttle?color=0f766e)](LICENSE)
[![Website](https://img.shields.io/badge/website-saman--mb.github.io%2Fcuttle-14b8a6?logo=github)](https://saman-mb.github.io/cuttle/)
[![Local hands](https://img.shields.io/badge/default-local%20hands-0d9488)](#-modes)
[![Router is code](https://img.shields.io/badge/router-is%20code-134e4a)](#-how-it-works)
[![Python](https://img.shields.io/badge/engine-Python%203.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-pre--alpha-yellow)](#-status)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Stars](https://img.shields.io/github/stars/saman-mb/cuttle?style=flat&logo=github)](https://github.com/saman-mb/cuttle/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/saman-mb/cuttle)](https://github.com/saman-mb/cuttle/commits/main)
[![Issues](https://img.shields.io/github/issues/saman-mb/cuttle)](https://github.com/saman-mb/cuttle/issues)

<p align="center">
  <img src="docs/assets/demo.gif" width="760" alt="Illustrative cuttle implement run: plan → hands → eval with a local-first status spine and cost/privacy receipt." />
</p>
<p align="center"><sub><i>Illustrative — phases of <code>cuttle implement</code>; metrics in real runs come from the ledger (not invented here).</i></sub></p>

**[Website →](https://saman-mb.github.io/cuttle/)** · **[How it works →](#-how-it-works)** · **[Install →](#-install)**

---

## Why Cuttle

Claude Code, Codex, and friends are excellent agents. They are weak at **enforced hybrid economics**: “plan expensive, execute local.” Skills and config *ask* the model to delegate; the orchestrator LLM still decides whether to comply.

Cuttle inverts that:

| Concern | Who owns it |
|---|---|
| Which model is brain vs hands | **Orchestrator** (config) — never the LLM |
| What “done” means for a step | **Deterministic evals** (commands, files, content) |
| When to spend frontier again | **Escalate policy** after failed local/cheap hands |

Not another “supports Ollama” checkbox. A **control plane** for local-first coding agents.

---

## How it works

```text
cuttle implement "fix failing auth test"
        │
        ▼
   Brain (pinned) ──► Directive (linted, checkable steps)
        │
        ▼
   Hands (local by default) × N scoped steps
        │
        ▼
   Evals ──► retry / replan / escalate (only if you configured it) / done
        │
        ▼
   Receipt: brain $ · hands $ · escalate $ · what left the machine
```

- **Brain** plans only (read/search) and emits a structured directive.
- **Hands** execute one step at a time under path scope, with a fresh attempt packet on retry.
- **Evals** are code, not vibes — no LLM-as-judge gate.
- **Status spine** (CLI now; Rust TUI later): model · locality · cost · phase.

---

## Modes

| Mode | Brain | Hands | Cloud escalate |
|---|---|---|---|
| **`local`** (default intent) | Local / cheap | Local | Off unless you opt in |
| **`hybrid`** | Frontier | Local | Optional mid-tier after failed evals |
| **`cloud`** | Frontier | Cloud / cheap cloud | Per policy |

Escalate-to-cloud is a **configured door**, not a silent surprise.

---

## What leaves the machine

Be honest about hybrid:

- **Local mode:** plan + implement stay on your endpoint (e.g. Ollama). Nothing need phone home.
- **Hybrid:** the **brain** may send repo context / snippets to a frontier provider. Hands stay local by default.
- Every run should print a **privacy receipt** (what class of data left the box) once that surface ships — until then, assume hybrid brain traffic is sensitive.

---

## Install

Pre-alpha scaffold — APIs will move. Python **3.12+**.

```bash
git clone https://github.com/saman-mb/cuttle.git
cd cuttle
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cuttle version
```

### BYO Ollama quickstart (target path)

Point hands at a model you already run — no download theatre inside `implement`:

```bash
# example — exact flags land with the runtime epics
export CUTTLE_HANDS_MODEL=ollama:qwen2.5-coder:32b
export CUTTLE_HANDS_BASE_URL=http://127.0.0.1:11434
# optional hybrid brain:
# export CUTTLE_BRAIN_MODEL=anthropic:claude-sonnet-4-6

cuttle doctor          # tool-call smoke (when shipped)
cuttle implement "fix the failing test"
```

Copy [`.env.example`](.env.example) for more knobs. Optional `cuttle hands setup` (llmfit-class wizard) is **out of band** — never a side effect of `implement`.

---

## Status

**Pre-alpha.** Contracts and docs are ahead of the runtime. The kill criterion for marketing “local hands” is a **published golden suite** (pass@1, escalate %, $ vs all-frontier) — see the backlog.

Roadmap epics: [E1–E9 on GitHub](https://github.com/saman-mb/cuttle/issues?q=is%3Aissue+is%3Aopen+label%3Aepic).

---

## Stack (target)

- **Python 3.12+** engine — phase machine, `CuttleAgentRuntime`, evals, thin provider access
- **Rust** interactive TUI later — status spine + connect/models overlays; no orchestration in Rust
- Versioned engine event stream shared by CLI and TUI
- Typer / `--plain` / `NO_COLOR` always available

---

## Layout

| Path | Role |
|---|---|
| `src/cuttle/` | Engine (CLI, orchestrator, contracts, agents, evals, backends, …) |
| `crates/cuttle-tui/` | Rust TUI (when landed) |
| `docs/` | HLA, architecture, viability, assets |
| `docs/assets/` | README / site demo GIFs |
| `AGENTS.md` | Instructions for every coding harness |

---

## Docs

- [HLA](docs/hla.md) — end-state architecture (being aligned to local-first vision)
- [Architecture](docs/architecture.md) — design rationale
- [Viability](docs/viability.md) — why a harness beats hope-based routing
- [Website](https://saman-mb.github.io/cuttle/) — landing (Pages epic)

---

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Agent instructions

| File | Role |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Source of truth for Cursor, Codex, Copilot, OpenCode, … |
| `CLAUDE.md` | Symlink → `AGENTS.md` |

Edit **`AGENTS.md` only**.

---

## License

[MIT](LICENSE)
