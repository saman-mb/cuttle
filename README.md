# Cuttle

**Frontier mind. Local hands.**

Cuttle is an agentic coding CLI harness that separates expensive reasoning from cheap execution:

1. A frontier **brain** inspects the repo and emits a detailed, prescriptive **directive**
2. A local (or cheap) **hands** agent executes one bounded step at a time
3. A deterministic **orchestrator** owns model binding, retries, and eval gates — not the LLM

> Scaffold only — implementation coming next. See [docs/architecture.md](docs/architecture.md).

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

## Why Cuttle

| Typical agent CLIs today | Cuttle |
|---|---|
| One model (or hope the model picks cheaper children) | Orchestrator **pins** brain vs hands models |
| Freeform plans + long tool loops on frontier pricing | Prescriptive **directive** → local execution |
| LLM-as-judge or vibes | Deterministic **eval gates** advance the run |
| Parallel swarm as the default story | Serial hands by default; capped scouts optional |

## Status

Early scaffold. Directories are placeholders; no runtime code yet.

| Path | Role |
|---|---|
| `orchestrator/` | Phase machine (plan → validate → execute → eval) |
| `contracts/` | Directive / step / acceptance schemas |
| `agents/` | Brain + hands agent runtimes |
| `middleware/` | Scope guard, stuck detector, cost telemetry |
| `evals/` | Deterministic checks |
| `backends/` | Model factories (frontier + local) |
| `cli/` | `cuttle` entrypoint |
| `skills/` | Optional reusable workflows |
| `docs/` | Architecture & diagrams |

## Docs

- [HLA (end state)](docs/hla.md) — target architecture; Deep Agents = bootstrap only
- [Architecture](docs/architecture.md) — harness design, comparison to today’s tools, diagrams
- [Viability](docs/viability.md) — harness vs prompts in Claude Code / Codex; product bet scorecard

## License

MIT
