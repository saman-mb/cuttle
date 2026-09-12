Repository instruction sources (read these first):

1. `AGENTS.md` — single source of truth for this repo
2. `docs/hla.md` — end-state architecture and LangGraph integration
3. `docs/architecture.md` — design rationale
4. `docs/viability.md` — harness vs prompts in existing CLIs

Rules:

- Python 3.12+ project (`src/cuttle/`, see `pyproject.toml`).
- Orchestrator owns phase control and model binding; never an LLM or third-party `task`/subagent router.
- Brain plans (Directive); hands execute steps; deterministic evals gate progress.
- Agent runtime is Cuttle-owned from day one (`create_agent` / LangGraph tool loop). Do not add Deep Agents.
- Python owns the LangGraph engine; Rust owns the interactive TUI only (event consumer). Do not put orchestration in Rust.
- Update HLA/docs when changing the control plane.
- Do not commit unless asked.
