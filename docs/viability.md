# Product viability: purpose-built harness vs configuring peers

> See also [`brief.md`](brief.md) § “Why build it, rather than configure an existing tool”.

## Short answer

Encoding **per-step routing with calibrated decisions, privacy guarantees, and a learning ledger** in a harness **is** more reliable than prompts and model pins inside Claude Code, Codex, OpenCode, or pi.

Whether that is worth a full product depends on proving — with evals — that routing beats “frontier for everything” on cost at similar pass rate, or beats “local only” on pass rate. The brief’s phase order (baselines before routing claims) exists so that proof is forced.

## What breaks in prompt/config world

| Approach | Failure mode |
|---|---|
| “Use Haiku for explore” | Orchestrator ignores you or burns frontier on tool loops |
| Per-agent model pins | Works *if* that agent is invoked; invocation still LLM-chosen |
| Skills / slash | Instructions, not a state machine |
| pi extension (~60–70% of the idea) | Per-turn routing; you orchestrate sub-agents yourself; no LangGraph planner/integrator |

## What only a harness cleanly owns

1. **Routing outside the expensive model** — Jev/`decide()` before a large coding call
2. **Calibrated thresholds** and reliability diagrams
3. **Guarantees** — local-only paths, command risk, escalation in code
4. **Learning** — per-step routing ledger on *your* repositories
5. **Planning sized** to each model’s context window and tool skill
6. **Local GPU scheduling** with visibility into every sub-agent

## Kill criteria (product)

- After phase 05: if no preset sits on a better pass-rate×cost frontier than the best single-model baseline on your labelled set, routing is not yet a product — keep learning (phase 08) or narrow scope.
- Privacy: any local-only content reaching cloud in evals is a ship blocker (phase 07).

## Path if it works

Open-source core (agent, router, local models, your keys) → teams (shared ledger/pools/budgets) → enterprise (central policy, audit, company gateway). Check employment IP / outside-interests before selling anything.
