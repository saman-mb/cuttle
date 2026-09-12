Repository instruction sources (read these first):

1. `AGENTS.md` — single source of truth for this repo
2. `docs/hla.md` — end-state architecture and LangGraph integration
3. `docs/architecture.md` — design rationale
4. `docs/viability.md` — harness vs prompts in existing CLIs

Rules:

- Python 3.12+ project (`src/cuttle/`, see `pyproject.toml`).
- Orchestrator owns phase control and model binding; do not route via Deep Agents `task`/subagents.
- Brain plans (Directive); hands execute steps; deterministic evals gate progress.
- Deep Agents is bootstrap for AgentRuntime only, not the product.
- Update HLA/docs when changing the control plane.
- Do not commit unless asked.
