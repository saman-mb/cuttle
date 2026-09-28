# Cuttle — architecture rationale

> Companion to [`brief.md`](brief.md) and [`hla.md`](hla.md). Explains *why* the pieces exist, not the full product surface.

## The bet

Existing coding agents are excellent at “one strong model with tools.” They are weak at **cheap, measured, enforced routing**: deciding *per step* which model should work, proving it with evals, and guaranteeing privacy without trusting a prompt.

Cuttle’s bet: a purpose-built harness with a typed decision layer (**Jev** / `decide()`) and a small **model pool** beats both “frontier for everything” on cost (at similar pass rate) and “local only” on pass rate — or we publish that it does not.

## Why not configure OpenCode / Claude Code / pi?

| Approach | What you get | What you do not get |
|---|---|---|
| Sub-agent model pins | Different models for explore vs edit | Routing still often decided by an expensive orchestrator LLM |
| Skills / prompts | Fast to try | Instructions, not guarantees |
| pi-style extension | Good prototype for Jev-before-turn | Per-turn not per-planned-step; no LangGraph planner/integrator; TS extension limits |
| **Cuttle harness** | `decide()` outside the coding model; ledger; privacy in the router; GPU-aware scheduling | You maintain the control plane |

Suggested spike: pi extension for routing baselines → then LangGraph build once the idea holds up on your tasks.

## Control plane vs coding models

```text
decide()          →  class, model pick, done?, escalate?, privacy?, risk?
coding model      →  read / edit / shell / argue about code
verifier (code)   →  tests, lint, types (ground truth)
router (code)     →  privacy filter, budgets, LiteLLM call, cost log
```

Never let the coding model choose the next coding model as a matter of policy. It may *propose*; `decide()` + router *commit*.

## Why LiteLLM as a library

One process, no extra daemon for the common case. Same config shape scales to a **LiteLLM proxy** when two machines (or a company gateway) should look like one pool with role names (`local-fast`, `local-strong`, `decide`, `embed`).

## Why Textual, not a Rust TUI first

The brief’s interactive surface is a Python Textual TUI beside the LangGraph engine — one language for agent core and rich terminal UX. A faster Rust CLI front-end remains an optional later optimisation, not the product’s defining split.

## Why five models

More models make calibration slow and `/why` hard to explain. Decision and embedding models sit outside the five so the pool stays about *coding work*.

## Why worktrees

Parallel sub-agents editing the same tree conflict. One worktree per writer + an integrator that merges and re-runs checks is the boring, correct answer.

## Eval honesty

Routing is only worth shipping if the phase-05 chart shows a better pass-rate×cost point than the phase-03 baselines. If it does not, say so and keep cascading / learning until it does — or narrow the claim.
