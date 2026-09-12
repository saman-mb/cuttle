# Cuttle — high-level architecture (end state)

**Audience:** anyone building Cuttle.  
**Purpose:** target architecture, how the orchestration loop works, how it plugs into the LangGraph / LangChain stack, and what we have to implement.

**Tagline:** Frontier mind. Local hands.

---

## 1. Deep Agents: target or shortcut?

| | Role |
|---|---|
| **Target** | Cuttle-owned CLI, orchestrator, contracts/evals, local provisioner, and (eventually) our own agent runtime |
| **Deep Agents** | Bootstrap implementation of the **Agent Runtime** only |

Deep Agents is **not** the long-term dependency. Early on it sits behind an interface. Later we can replace it with LangChain `create_agent` + our middleware, or a fully custom LangGraph tool loop, without rewriting the orchestrator.

**Hard rule:** Deep Agents’ `task` / subagent tool is **never** the system router. Cuttle’s orchestrator decides phases and models.

---

## 2. How the LangChain stack fits (mental model)

Think in four layers. Cuttle uses more than one of them.

```text
┌─────────────────────────────────────────────────────────────┐
│  Cuttle CLI / product                                       │  we build
│  commands, skills UX, config, sessions, provisioner UI      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  Cuttle Orchestrator                                        │  we build
│  LangGraph StateGraph: PLAN → … → DONE                      │
│  deterministic — almost no “let the LLM choose the phase”   │
└─────────────┬──────────────────────────────┬────────────────┘
              │ invokes                      │ invokes
┌─────────────▼──────────────┐ ┌─────────────▼────────────────┐
│  Brain Agent Runtime       │ │  Hands Agent Runtime         │
│  bootstrap: create_deep_   │ │  bootstrap: create_deep_     │
│  agent(...)                │ │  agent(...)                  │
│  end state: our runtime    │ │  end state: our runtime      │
│  (still LangGraph graph)   │ │  (still LangGraph graph)     │
└─────────────┬──────────────┘ └─────────────┬────────────────┘
              │                              │
┌─────────────▼──────────────────────────────▼────────────────┐
│  LangChain primitives                                       │
│  init_chat_model / ChatOpenAI / ChatOllama / …              │
│  tools, middleware, messages, structured output             │
│  checkpointers, stores                                      │
└─────────────────────────────────────────────────────────────┘
```

| Piece | Library | Who owns behaviour |
|---|---|---|
| Outer run loop (plan/eval/escalate) | **LangGraph** `StateGraph` | **Cuttle** |
| Inner “LLM + tools until done” loop | Deep Agents → later our agent | Bootstrap vs Cuttle |
| Model client | LangChain chat models | Config / adapters |
| Persistence of orchestrator run | LangGraph checkpointer | Cuttle |
| Persistence of a single agent turn thread | Agent checkpointer (optional) | Runtime adapter |

So: **two graphs**, not one.

1. **Orchestrator graph** — Cuttle, phase machine, no freeform agenting.  
2. **Role agent graphs** — brain or hands, classic tool-calling agent, one role per invoke.

---

## 3. End-state system diagram

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
                         │  Orchestrator (LangGraph)    │
                         │  PLAN→VALIDATE→DISPATCH→EVAL │
                         │  model bind · budgets · IDs  │
                         └───────┬──────────────┬───────┘
                                 │              │
                    ┌────────────▼──┐      ┌────▼────────────┐
                    │ Brain Runtime │      │ Hands Runtime   │
                    │ (frontier)    │      │ (local / cheap) │
                    └───────┬───────┘      └────┬────────────┘
                            │         ┌─────────▼──────────┐
                            │         │ Local Provisioner  │
                            │         │ llmfit → download  │
                            │         │ → deploy runtime   │
                            │         └─────────┬──────────┘
                    ┌───────▼───────────────────▼──────────┐
                    │     Tool Host + Workspace            │
                    │  FS · shell · MCP · git · sandbox    │
                    └──────────────────────────────────────┘
```

---

## 4. Orchestration loop (detailed)

### 4.1 What the loop is responsible for

The orchestrator is normal code shaped as a LangGraph. It:

- Picks **which model** runs (brain / hands / escalate-hands) from config  
- Calls brain **once** (or again on replan) to get a `Directive`  
- Walks `directive.steps` in order (default)  
- For each step: run hands → run evals → retry / escalate / advance  
- Stops on success, budget exhaustion, or unrecoverable failure  

It does **not** ask an LLM “what should we do next?” for phase transitions.

### 4.2 Orchestrator state (what we implement)

Conceptual `TypedDict` / pydantic state for the outer LangGraph:

```text
OrchestratorState
  run_id: str
  goal: str                          # user request
  workspace_root: str

  # model refs resolved from config at start
  brain_model: ModelRef
  hands_model: ModelRef
  escalate_hands_model: ModelRef

  directive: Directive | None
  step_index: int
  step_attempt: int                  # retries for current step
  step_tier: "local" | "escalate"    # which hands model this attempt

  last_step_result: StepResult | None
  last_eval: EvalReport | None

  status: "running" | "awaiting_approval" | "succeeded" | "failed"
  failure_reason: str | None

  usage: list[UsageEvent]            # per-role tokens / $ / latency
  max_step_retries: int
  max_replans: int
  replan_count: int
```

Contracts (`Directive`, `Step`, `StepResult`, `EvalReport`, `ModelRef`, `UsageEvent`) are Cuttle packages under `contracts/`.

### 4.3 Nodes and edges

```text
                    ┌─────────────┐
                    │  ensure_    │
           ┌───────►│  hands      │──┐
           │        └─────────────┘  │
           │                         ▼
┌──────┐   │        ┌─────────────┐  ┌─────────────┐
│start │───┴───────►│    plan     │─►│  validate   │
└──────┘            │  (brain)    │  └──────┬──────┘
                    └─────────────┘         │
                           ▲                ▼
                           │         ┌──────────────┐
                           │         │ approve?     │──no──► failed / aborted
                           │         │ (optional)   │
                           │         └──────┬───────┘
                           │                │ yes
                           │                ▼
                           │         ┌──────────────┐
                           │         │  dispatch    │
                           │         │  (hands)     │
                           │         └──────┬───────┘
                           │                ▼
                           │         ┌──────────────┐
                           │         │    eval      │
                           │         └──────┬───────┘
                           │                ▼
                           │         ┌──────────────┐
                           │    ┌────│  route_after │
                           │    │    │    eval      │
                           │    │    └──────────────┘
                           │    │
                           │    ├── pass + more steps ──► dispatch (next step)
                           │    ├── pass + no steps ────► final_eval ──► succeed
                           │    ├── fail + retries left ► dispatch (same step)
                           │    ├── fail + escalate OK ─► dispatch (escalate model)
                           │    ├── fail + replan OK ───► plan (brain again)
                           │    └── fail + exhausted ───► fail
                           │
                           └─────────────────────────────────────────┘
```

| Node | LLM? | What it does |
|---|---|---|
| `ensure_hands` | No | If local hands missing/unhealthy → provisioner (or fail with setup instructions) |
| `plan` | **Yes — brain** | Invoke brain runtime with goal + repo context budget; parse `Directive` |
| `validate` | No | Schema validate; path sanity; reject empty/unsafe directives |
| `approve` | No (HITL) | Optional interrupt for user to accept/edit plan |
| `dispatch` | **Yes — hands** | Build step prompt from `Step`; invoke hands with scoped tools; collect `StepResult` |
| `eval` | No | Run acceptance checks for this step; produce `EvalReport` |
| `route_after_eval` | No | Pure branching on eval + counters (retries, tier, replans) |
| `final_eval` | No | Run `directive.final_checks` |
| `succeed` / `fail` | No | Persist run, emit cost report |

### 4.4 Step lifecycle (one step)

```text
dispatch(step_index, tier=local)
  → hands.run(Step, model=hands_model)
  → eval(step.acceptance)
       pass → step_index += 1; step_attempt = 0; tier = local
       fail → step_attempt += 1
            if step_attempt <= max_step_retries:
                 dispatch again (fresh hands thread)
            else if tier == local and escalate configured:
                 tier = escalate; step_attempt = 0; dispatch
            else if replan_count < max_replans:
                 replan_count += 1; go to plan with failure packet
            else:
                 fail run
```

**Fresh hands thread per attempt** matters: local models context-rot; don’t keep appending forever.

### 4.5 What brain receives / returns

**Input (orchestrator → brain):**

- User goal  
- Optional: file tree summary, failing tests, previous failure packet  
- System rules: emit only `Directive`; do not edit files  

**Output:** structured `Directive` (via `response_format` / structured output).

Brain tools (allowed): read-only FS, grep/glob, maybe read-only shell.  
Brain tools (denied): write/edit/mutating execute.

### 4.6 What hands receive / returns

**Input (orchestrator → hands):**

- Single `Step` (goal, instructions, allowed paths, commands, acceptance text)  
- Injected snippets orchestrator chose (not full brain chat)  
- System rules: only touch `files_allowed`; stop when step goal met  

**Output:** `StepResult` (summary, files touched, commands run, raw errors).

Hands tools: full coding toolset, optionally filtered by path middleware.

### 4.7 Failure packet (for replan)

When escalating back to brain:

```text
FailurePacket
  goal
  directive_id / version
  failed_step: Step
  attempts: [StepResult + EvalReport, ...]
  git_diff_stat or file list
  escalate_if matches (if any)
```

Brain’s job on replan: revise remaining steps (or whole directive), not chat vaguely.

---

## 5. LangGraph / LangChain integration points

This section is the “what do we call in the stack?” map.

### 5.1 Orchestrator graph (Cuttle)

**Implement with:** `langgraph.graph.StateGraph`

| Integration | API / concept | Cuttle use |
|---|---|---|
| Define state | `TypedDict` + reducers | `OrchestratorState` |
| Add nodes | `builder.add_node(name, fn)` | plan, validate, dispatch, eval, … |
| Conditional edges | `add_conditional_edges` | `route_after_eval` |
| Compile | `builder.compile(checkpointer=...)` | resume runs, HITL |
| Invoke | `graph.ainvoke(input, config={"configurable": {"thread_id": run_id}})` | CLI entry |
| Interrupt / HITL | `interrupt()` or interrupt-before node | plan approval |
| Streaming | `astream_events` / `astream` | CLI live UI |

**We write:** all node functions, routing functions, state schema, compile wiring.

**We do not use:** a single `create_deep_agent` as the outer graph.

### 5.2 Model binding (LangChain)

**Implement with:** `langchain.chat_models.init_chat_model` and/or explicit clients.

| Role | Typical binding |
|---|---|
| Brain | `init_chat_model("anthropic:…")` or OpenAI/etc. from config |
| Hands local | `ChatOllama` / OpenAI-compatible client → `http://127.0.0.1:11434` (or llama.cpp/MLX server) |
| Hands escalate | cheaper cloud model string |

Orchestrator resolves `ModelRef` → `BaseChatModel` **before** invoke and passes the instance into the runtime. The role agent must not pick another model mid-run.

### 5.3 Brain / hands runtime interface (Cuttle adapter)

Stable interface so Deep Agents is swappable:

```text
class AgentRuntime(Protocol):
  def run(
    self,
    *,
    role: Literal["brain", "hands"],
    model: BaseChatModel,
    system_prompt: str,
    user_payload: dict | str,    # goal or Step JSON
    tools: Sequence[BaseTool] | None,
    response_schema: type | None,  # Directive or StepResult
    thread_id: str,
    workspace: WorkspaceRef,
  ) -> AgentRunResult: ...
```

| Adapter | When | Implements `run` via |
|---|---|---|
| `DeepAgentsRuntime` | Bootstrap | `create_deep_agent(...).invoke/ainvoke` |
| `CreateAgentRuntime` | Mid | `langchain.agents.create_agent` |
| `CuttleAgentRuntime` | End state | Our LangGraph tool loop |

Orchestrator only depends on `AgentRuntime`.

### 5.4 Deep Agents bootstrap wiring (concrete)

For bootstrap, each role is a **separate** `create_deep_agent` graph (or one factory with different kwargs). Orchestrator invokes them like subprocesses (in-process graphs).

**Brain `create_deep_agent` knobs we care about:**

| Param | Brain setting |
|---|---|
| `model` | frontier `BaseChatModel` |
| `system_prompt` | plan-only instructions |
| `response_format` | `Directive` schema |
| `tools` | none extra, or read-only extras |
| `permissions` / middleware | deny write/edit/execute mutate |
| `subagents` | **empty / GP disabled** — no `task` router |
| `backend` | workspace backend rooted at repo |
| `checkpointer` | optional ephemeral per plan call |

**Hands `create_deep_agent` knobs:**

| Param | Hands setting |
|---|---|
| `model` | local or escalate `BaseChatModel` |
| `system_prompt` | execute-this-step instructions |
| `response_format` | `StepResult` (or parse final message) |
| `tools` | coding tools as needed |
| `middleware` | path scope guard (Cuttle middleware) |
| `subagents` | disabled |
| `backend` | same workspace (or worktree) |
| `interrupt_on` | optional for destructive tools |

**Important Deep Agents details for implementers:**

- Built-in tools include FS + `execute` + `task`. For Cuttle, **strip/disable `task`** (no general-purpose subagent; don’t pass subagents).  
- Use `permissions` / tool-exclusion / custom middleware so brain cannot mutate.  
- Prefer `response_format` for Directive so orchestrator doesn’t regex JSON out of prose.  
- Pass an explicit `model=` every time; never rely on library defaults.

### 5.5 End-state agent runtime (what replaces Deep Agents)

Same outer orchestrator. Inner runtime becomes our graph:

```text
agent_loop (LangGraph)
  node: model (BaseChatModel.bind_tools)
  node: tools (ToolNode)
  edges: model → tools → model until no tool calls / structured end
  middleware: summarization, scope guard, stuck detector
```

Built from LangChain `create_agent` or hand-rolled `StateGraph` + `ToolNode`.  
Filesystem/shell can stay as LangChain tools we own under `backends/` / tool host.

### 5.6 Tools and MCP

| Concern | Stack piece | Cuttle work |
|---|---|---|
| Define tools | `langchain.tools.BaseTool` / `@tool` | Tool host package |
| MCP tools | LangChain MCP adapters / client | Load from user config; attach to hands (and limited to brain) |
| Sandbox execute | backend protocol / our executor | Provisioner + security policy |

Orchestrator chooses **tool allowlists per role** when calling `AgentRuntime.run`.

### 5.7 Persistence

| What | Mechanism |
|---|---|
| Whole Cuttle run (step index, directive, usage) | Orchestrator LangGraph checkpointer (`thread_id=run_id`) |
| Single hands attempt transcript | Optional separate thread_id; discard after eval |
| Cross-session memory (later) | Store / memory files — product feature, not required for MVP loop |

### 5.8 Provisioner (mostly outside LangChain)

| Step | Integration |
|---|---|
| Recommend | shell out / library call to **llmfit** JSON |
| Download | Hugging Face Hub API / `huggingface_hub`, or Ollama pull |
| Deploy | start/ensure Ollama|llama.cpp|MLX server; wait for `/health` |
| Register | write `ModelRef` into Cuttle config |
| Use | `init_chat_model` / OpenAI-compat base URL pointing at that server |

LangChain only sees a normal chat model endpoint after provisioner finishes.

### 5.9 Observability (optional but planned)

- LangSmith tracing on brain/hands runs (`langchain` env vars / callbacks)  
- Cuttle-native usage events in orchestrator state for the user-facing cost report  

---

## 6. What needs to be implemented (checklist)

Ordered roughly by dependency. Packages map to repo folders.

### A. Contracts (`contracts/`) — no LLM required

- [ ] `ModelRef`  
- [ ] `Directive`, `Step`, `AcceptanceCheck`  
- [ ] `StepResult`, `EvalReport`, `FailurePacket`  
- [ ] `UsageEvent`, run status enums  
- [ ] JSON Schema / pydantic validation helpers  

### B. Model registry + config (`backends/` + config module)

- [ ] Load user/project config  
- [ ] Resolve env overrides  
- [ ] Factory: `ModelRef` → `BaseChatModel` (frontier + OpenAI-compat local)  
- [ ] Defaults for brain / hands / escalate  

### C. Eval engine (`evals/`)

- [ ] Command runner (timeout, cwd, capture)  
- [ ] File exists / content match / regex  
- [ ] Path allowlist diff check (git or walk)  
- [ ] Aggregate `EvalReport`  

### D. Orchestrator (`orchestrator/`) — LangGraph

- [ ] `OrchestratorState`  
- [ ] Nodes: ensure_hands, plan, validate, approve, dispatch, eval, route, final_eval, succeed/fail  
- [ ] Conditional edges for retry/escalate/replan  
- [ ] Checkpointer + `thread_id`  
- [ ] Usage aggregation + final report object  

### E. Agent runtime adapter (`agents/`)

- [ ] `AgentRuntime` protocol  
- [ ] `DeepAgentsRuntime` (bootstrap)  
  - [ ] Brain factory (read-only, `response_format=Directive`, no subagents)  
  - [ ] Hands factory (scoped tools, no subagents)  
- [ ] Prompt builders: goal→brain message; Step→hands message  
- [ ] Later: `CuttleAgentRuntime` replacing Deep Agents  

### F. Middleware / tool host (`middleware/`, tool host)

- [ ] Path scope guard for hands  
- [ ] Deny mutate tools for brain  
- [ ] Stuck detector (repeat tool loop)  
- [ ] Workspace backend wiring  

### G. Local provisioner (`backends/` or `provisioner/`)

- [ ] Hardware detect  
- [ ] llmfit recommend integration  
- [ ] Download + deploy + health check  
- [ ] `cuttle hands install` / `cuttle setup` flows  

### H. CLI product surface (`cli/`, `skills/`)

- [ ] `cuttle implement`  
- [ ] `cuttle doctor` / `cuttle hands`  
- [ ] Sessions / resume  
- [ ] Skills + slash commands  
- [ ] Permissions UX  
- [ ] MCP config loading  

### I. End-state replacement

- [ ] Native agent tool loop feature-parity with what we used from Deep Agents  
- [ ] Drop Deep Agents dependency from default installs (optional extra OK)  

---

## 7. Bootstrap vs end state (same loop)

```text
Component              Bootstrap                         End state
─────────────────────────────────────────────────────────────────────
Orchestrator loop      Cuttle LangGraph                  same
Contracts / evals      Cuttle                            same
Model factory          LangChain init_chat_model         same
Brain/hands invoke     DeepAgentsRuntime                 CuttleAgentRuntime
Tools / FS / shell     Deep Agents middleware + backend  Cuttle tool host
Provisioner            stub or manual model              full llmfit+HF path
CLI                    thin                              full product surface
```

The orchestration **loop shape does not change** when we leave Deep Agents. Only the body of `AgentRuntime.run` changes.

---

## 8. Non-goals for the orchestrator

- Letting brain call hands via Deep Agents `task`  
- LLM-as-judge as the primary step gate  
- One mega-agent graph that both plans and edits under a single model  
- Rebuilding provisioner inside LangChain (keep it a normal service module)  

---

## 9. Summary

| Question | Answer |
|---|---|
| Where is the Cuttle brain/hands logic enforced? | **Orchestrator LangGraph** (phases + model binding + evals) |
| Where does LangChain sit? | Chat models, tools, middleware, optional `create_agent` |
| Where does Deep Agents sit? | **Bootstrap** behind `AgentRuntime`, not the outer loop |
| What do we implement first? | Contracts → evals → orchestrator → DeepAgentsRuntime → thin CLI |
| What is the end state? | Same orchestrator; our own agent runtime; full CLI; llmfit provisioner |

Related: [architecture.md](architecture.md), [viability.md](viability.md).
