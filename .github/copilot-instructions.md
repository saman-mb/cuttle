Repository instruction sources (read these first):

1. `AGENTS.md` — single source of truth for this repo
2. `docs/brief.md` — authoritative product brief (wins on conflict)
3. `docs/hla.md` — end-state architecture
4. `docs/architecture.md` — design rationale
5. `docs/viability.md` — harness vs configuring peers

Rules:

- Python 3.12+ project (`src/cuttle/`, see `pyproject.toml`).
- Pool of ≤5 coding models; `decide()` (Jev / local) owns judgement; coding models own edits; deterministic verifier gates progress.
- Complexity classes C0–C4 + step kinds; presets Thrifty / Balanced / Best quality / Local only; cascade on failure.
- Privacy is a routing rule (local-only paths never to cloud). LiteLLM library as gateway; Textual TUI; ACP for editors.
- Do not add Deep Agents. Do not treat brain/hands role pins or a Rust TUI as the day-one product (superseded by the brief).
- Update brief/HLA when changing the control plane.
- Do not commit unless asked.
