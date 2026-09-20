# Contributing to Cuttle

Thanks for helping. Cuttle is pre-alpha; small, focused PRs are easiest to review.

## Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

- Prefer British English in user-facing copy.
- Do not commit secrets (`.env`, auth stores, API keys).
- Architecture changes: update `docs/hla.md` (and related docs) in the same PR when behaviour shifts.
- Agent instructions live in `AGENTS.md` only.

## Pull requests

1. Branch from `main`.
2. Keep the diff scoped to one story or fix.
3. Link the GitHub issue in the PR body.
4. Say how you validated (docs-only is fine when that is the ticket).

## Code of conduct

Be kind. No harassment. Disagreements stay about the work.
