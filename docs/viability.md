# Product viability: harness vs prompts in existing CLIs

**Frontier mind. Local hands.**

This note captures why Cuttle encodes brain→hands in a custom harness (e.g. LangGraph + role agents) instead of relying on orchestration prompts and config inside Claude Code, Codex, or similar tools — and how viable that product bet is.

---

## Short answer

Encoding brain→hands in a harness **is** more reliable than prompts/config in Claude Code/Codex — for the specific failure mode we care about (cheap/local execution that actually runs).

Whether that is a **product** worth shipping is narrower: the reliability gain is real; “must be a brand-new full coding CLI” is only half the story.

---

## What actually breaks today

| Approach | What you get | What fails |
|---|---|---|
| **Prompts** (“use Haiku for subagents”) | Easy | Model ignores you; inherits parent model; burns frontier on tool loops |
| **Config pins** (Claude agent `model: haiku`, Codex agent TOML) | Works *if that agent is used* | Orchestrator LLM still chooses *whether* to call it, what to put in the task, when to do the work itself |
| **Slash command / skill** | Nice UX | Usually instructions, not an enforced state machine |
| **Custom harness** (LangGraph, etc.) | Phases + model binding + evals owned by code | You build/maintain the control plane (and enough agent surface to be useful) |

The pain is real: there is no trustworthy “`/command` that always delegates subtasks to cheaper models” in mainstream agent CLIs. Pins exist; **invocation and discipline do not**.

---

## Why a harness is more deterministic

```text
Prompt/config world          Harness world
─────────────────            ─────────────────
LLM decides next action  →   Code decides next phase
LLM may call Task/Agent  →   Only hands can mutate code
LLM picks model (maybe)  →   Config pins brain vs hands
“Looks done”             →   Eval gates must pass
Hope                     →   Retry / escalate rules
```

LangGraph (or any orchestrator) is not magic. **Determinism comes from not trusting the frontier model as the control plane.** Deep Agents / Claude Code–class runtimes remain good *role engines*; Cuttle’s IP is the loop around them.

That makes brain→hands work more reliably than “configure Claude Code carefully,” for the same reason systems like Penny, local-first harnesses, and Aider’s architect/editor split work: **the router is not an LLM**.

---

## Where a custom harness does *not* automatically win

| Risk | Reality |
|---|---|
| **Local hands quality** | 14–32B models often cannot follow even good briefs on hard refactors → high escalate rate → savings shrink |
| **Directive quality** | Bad briefs = reliable failure. The brain must excel at *prescribing*, not only planning |
| **Product surface** | Claude Code / Codex already ship tools, permissions, IDE UX, auth, MCP. Rebuilding all of that is years of work |
| **Competition** | The planner/executor pattern is known; niche OSS exists; majors may improve native routing |
| **Distribution** | “Another coding CLI” is a brutal market unless the wedge stays sharp |

So: **more reliable for cost routing ≠ automatically a large commercial product.**

---

## Viable as what?

### Strong viability — tool / open-source / personal infra

Build a thin harness that:

- Brain = frontier (plan / directive only)
- Hands = local or mid-tier cheap model, **pinned**
- Directive schema + deterministic evals + escalate ladder

This is clearly worth it if the goal is lower subscription/API spend and repeatable runs. LangGraph is a valid substrate; Deep Agents (or similar) as brain/hands runtimes is fine.

### Medium viability — product / paid CLI

Viable **if** the wedge stays narrow:

> Frontier tokens only for planning and escalation; local (or cheap) models do the implement loop under contracts and tests.

Weak if positioned as “better Claude Code.” Polish and ecosystem will lose that fight.

### Weak viability — default assumption

“We’ll beat Cursor / Claude / Codex by re-prompting orchestration inside their tools” — already unreliable for enforced cheap delegation, and will not become reliable without platform changes from those vendors.

---

## LangGraph vs “just use Claude / Codex better”

| | Claude / Codex + config | Custom harness (Cuttle) |
|---|---|---|
| Time to first win | Days | Weeks–months |
| Model-binding reliability | Medium (pins) / low (ad-hoc spawn) | **High** |
| Eval-gated progress | DIY / weak | **First-class** |
| Local-first default | Possible, awkward | **Natural** |
| IDE / agent ergonomics | Excellent | Start near zero; borrow runtimes |
| Moat | None (their roadmap) | Contracts + evals + cost UX |

**Verdict:** A custom harness is the correct *engineering* answer to reliability. Prompts-only in existing tools is the correct answer only if you need occasional savings and can babysit runs.

LangGraph is not the insight. **Deterministic orchestration is.** LangGraph is a solid way to implement that.

---

## Product scorecard

| Dimension | Score | Note |
|---|---|---|
| Problem real? | **High** | Unreliable cheap subagent routing in mainstream CLIs |
| Technical approach sound? | **High** | Orchestrator-owned routing is a proven pattern |
| Diff vs “better prompts”? | **High** | Encoding beats hoping |
| Diff vs “multi-engine gateway”? | **Medium** | Must own directive + evals, not only bus/org-chart UX |
| Local hands enough? | **Unknown / make-or-break** | Validate on real tasks before betting the brand |
| Market timing | **Medium** | Hybrid routing rising; no dominant brain→local-hands IDE yet |
| Build cost | **High** if full CLI clone; **Medium** if thin orchestrator + role runtimes | |

---

## Viability test (not belief)

1. **Do not rebuild Claude Code.** Own orchestrator + directive + hands + evals. Reuse filesystem/shell/agent loops from Deep Agents or similar.
2. **Measure** on a fixed task set: all-frontier baseline vs Cuttle (local/cheap hands) — resolve rate, cost, wall time, escalate %.
3. **Kill criterion:** escalate rate stays very high (e.g. ≳ 40%) or quality gap is large → local hands are not ready. Fallback product is still useful: frontier plan + mid-tier cloud hands (weaker story, still deterministic).
4. **Ship criterion:** comparable quality at a clear cost cut (target ballpark: ~≤ 50% of all-frontier on a meaningful set) with **zero** “please use Haiku” prompts.

---

## Bottom line

| Question | Answer |
|---|---|
| Is encoding this in a harness valid? | **Yes** — meaningfully more reliable than config/prompts alone |
| Point vs existing tools? | **Yes** for enforced hybrid cost control; **no** if you only want nicer multi-agent UX |
| Product idea viability? | **Technically strong, commercially contingent** on hands quality, narrow positioning, and measured $/quality wins |

See also [architecture.md](architecture.md) for the control-plane design this argument implies.
