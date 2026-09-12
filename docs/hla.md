# Cuttle — high-level architecture (end state)

**Audience:** anyone building Cuttle.  
**Purpose:** define the *target* system architecture for the finished product — not the day-one bootstrap.

**Tagline:** Frontier mind. Local hands.

---

## Deep Agents: target or shortcut?

| | Role |
|---|---|
| **Target architecture** | Cuttle-owned control plane + Cuttle-owned agent runtimes + Cuttle-owned local provisioner + Cuttle CLI product surface |
| **Deep Agents** | **Optional bootstrap only** — a fast way to get a working tool-using coding agent while the product shell and orchestrator are built |

Deep Agents is **not** the end-state dependency.  
If we use it early, it sits behind an internal **Agent Runtime** interface. The final architecture assumes we can run brain/hands on our own LangGraph/`create_agent` (or equivalent) implementation without Deep Agents in the critical path.

Day-one path and end-state path share the same boxes; only the *implementation* of “Agent Runtime” changes.

---

## What the product is (end state)

Cuttle is a full coding-agent CLI (and later optional IDE integration) that:

1. Exposes a complete agent product surface (tools, skills/commands, config, permissions, MCP, sessions) comparable to Claude Code / Codex-class tools.
2. Runs a **deterministic hybrid loop**: frontier **brain** plans; **hands** execute; evals decide progress.
3. **Provisions local hands for the user**: hardware detect → model recommend (llmfit) → download (Hugging Face / runtime registries) → deploy runtime → wire config — without manual Ollama/LM Studio setup.

---

## End-state system diagram

```text
                         ┌──────────────────────────────┐
                         │     User / IDE extension     │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────▼───────────────┐
                         │         Cuttle CLI           │
                         │  commands · skills · config  │
                         │  sessions · permissions· MCP │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────▼───────────────┐
                         │      Control Plane           │
                         │   (Cuttle Orchestrator)      │
                         │  PLAN→VALIDATE→DISPATCH→EVAL │
                         │  model bind · budgets · IDs  │
                         └───────┬──────────────┬───────┘
                                 │              │
                    ┌────────────▼──┐      ┌────▼────────────┐
                    │ Brain Runtime │      │ Hands Runtime   │
                    │ (frontier)    │      │ (local / cheap) │
                    │ plan-only     │      │ implement loop  │
                    └───────┬───────┘      └────┬────────────┘
                            │                   │
                            │         ┌─────────▼──────────┐
                            │         │ Local Provisioner  │
                            │         │ llmfit → HF/pull   │
                            │         │ → runtime deploy   │
                            │         └─────────┬──────────┘
                            │                   │
                    ┌───────▼───────────────────▼──────────┐
                    │     Tool Host + Workspace            │
                    │  FS · shell · MCP · git · sandbox    │
                    └──────────────────────────────────────┘
```

---

## Major subsystems (final)

### 1. Product surface (CLI / later IDE)

Owns everything the user touches:

- Interactive + non-interactive CLI (`cuttle`, `cuttle implement`, `cuttle ask`, …)
- Project + user config
- Skills and slash-style commands
- Permissions / approval modes
- MCP client (and optional MCP server for Cuttle itself)
- Session list / resume / transcripts
- Doctor, setup, cost/usage reports

This layer is **always Cuttle-owned**. No Deep Agents UI.

### 2. Control plane (orchestrator)

Owns reliability and cost behaviour:

- Phase machine: plan → validate directive → dispatch step → eval → retry / escalate / done
- **Model binding** (which model is brain, hands, escalate-hands) — never left to the LLM
- Concurrency policy (default: one writer; optional read-only scouts)
- Budgets (frontier $, local wall-time, retries)
- Run state persistence
- HITL plan approval (optional)

This layer is **always Cuttle-owned** (LangGraph or equivalent state machine).  
It calls runtimes as workers; workers do not decide the phase graph.

### 3. Contracts

Stable data shapes between brain, orchestrator, and hands:

- `Directive` — objective, steps, scopes, acceptance, escalate_if
- `Step` / `StepResult`
- `AcceptanceCheck` results
- Run / cost telemetry events

Schemas live in Cuttle. Runtimes produce/consume them.

### 4. Agent runtimes (brain & hands)

Two roles, same runtime interface, different config:

| Role | Model | Allowed behaviour |
|---|---|---|
| **Brain** | Frontier cloud (subscription or API) | Read/search; emit `Directive`; no repo mutation |
| **Hands** | Local by default (or mid-tier cloud on escalate) | Edit/bash/tools within step scope; return `StepResult` |

**End-state implementation:** Cuttle’s own agent runtime on LangGraph (tool loop, context compaction, etc.).  
**Bootstrap implementation:** Deep Agents (or LangChain `create_agent`) behind the same interface.

Interface sketch (conceptual):

```text
AgentRuntime.run(role, model_ref, prompt, tools, constraints) → result
```

Swapping Deep Agents → native runtime must not change the control plane.

### 5. Tool host + workspace

Shared capability layer used by runtimes:

- Filesystem read/write/edit, grep/glob
- Shell / sandbox
- Git helpers
- MCP tools
- Optional worktree isolation for parallel writers

End state: Cuttle-owned (or thin wrappers over well-defined libraries). Bootstrap may reuse Deep Agents filesystem/shell middleware.

### 6. Eval engine

Deterministic gates (not LLM-as-judge as primary):

- Command checks (pytest, tsc, linters, …)
- File/content assertions
- Path allowlist / forbid list
- Final suite checks

Orchestrator advances only on pass (or explicit escalate policy).

### 7. Local provisioner (hands install)

End-to-end “make local hands work”:

1. Detect hardware (CPU/RAM/GPU/VRAM, OS)
2. Recommend models via **llmfit** (`recommend --use-case coding --json`, etc.)
3. Resolve artifacts (Hugging Face GGUF/MLX/etc., or Ollama library)
4. Download with progress / resume
5. Deploy into a managed runtime (Ollama and/or llama.cpp and/or MLX)
6. Health-check inference + tool-calling suitability
7. Register as the active hands model in Cuttle config
8. Optional: upgrade / rollback / re-recommend when hardware changes

Brain credentials stay separate (API key or subscription login for frontier).  
Hands should work after `cuttle setup` / `cuttle hands install` with minimal user expertise.

### 8. Model registry (config)

Logical model refs, not scattered env vars only:

- `brain` → frontier provider/model
- `hands` → local endpoint + model id
- `hands_escalate` → cheap cloud model
- Optional `scout` → smaller local

Control plane reads only this registry.

---

## Runtime flow (end state)

```text
cuttle implement "<goal>"

1. Ensure hands ready (provisioner if missing/unhealthy)
2. Control plane → Brain(frontier) → Directive
3. Validate directive (+ optional user approve)
4. For each step:
     Hands(local) executes step under scope
     Eval engine runs acceptance checks
     fail → retry hands
     fail → escalate to cheap cloud hands OR brain replan
5. Final checks → report (brain cost, hands cost, escalations)
```

Parallel scouts (read-only) are optional and capped. Default implement path is serial hands.

---

## What is in / out of the end-state core

### In (must be Cuttle)

- CLI product surface  
- Orchestrator / control plane  
- Directive + eval contracts  
- Local provisioner (llmfit + download + deploy)  
- Model registry + cost/telemetry  
- Permissions / sessions / skills/commands/config as product features  

### Out (not required in-process)

- Training models  
- Hosting frontier models ourselves (use existing APIs/subscriptions)  
- Being an IDE-first Cursor clone on day one (IDE can come later; CLI is primary)

### Replaceable adapters

- Deep Agents (bootstrap agent runtime)  
- Specific local backends (Ollama vs llama.cpp vs MLX)  
- Specific frontier providers (Anthropic, OpenAI, …)

---

## Bootstrap vs end state (same architecture)

```text
                    END STATE                 BOOTSTRAP (allowed)
Control plane       Cuttle orchestrator       same
CLI / skills        Cuttle                    same (can be thinner)
Contracts / evals   Cuttle                    same
Provisioner         Cuttle + llmfit + HF      stub / manual model OK
Brain/Hands loop    Cuttle agent runtime      Deep Agents behind interface
Tool host           Cuttle                    Deep Agents middleware OK
```

Rule: **never** let Deep Agents’ subagent/`task` tool be the system router.  
Routing always stays in the Cuttle control plane.

---

## Non-functional targets (end state)

- **Reliability:** model roles are config-enforced; steps gated by evals  
- **Setup:** new user can get local hands running via Cuttle without hand-editing Ollama/HF flows  
- **Cost:** frontier tokens concentrated on plan/replan/escalate; most implement tokens on local/cheap hands  
- **Operability:** doctor, logs, per-role token/$ accounting, reproducible run IDs  
- **Swappability:** agent runtime and local backend are replaceable without rewriting the CLI or orchestrator  

---

## Summary

| Question | Answer |
|---|---|
| Is Deep Agents the target? | **No** |
| Is Deep Agents useful? | **Yes, as an early implementation of Agent Runtime** |
| Optimal end-state architecture? | **Cuttle CLI + Cuttle orchestrator + Cuttle contracts/evals + Cuttle provisioner + swappable agent runtimes for brain/hands** |
| What must never be delegated to an LLM? | **Phase control and model binding** |

Related docs: [architecture.md](architecture.md) (design rationale), [viability.md](viability.md) (why a harness vs prompts).
