# Module 2 Summary: Multi-Agent SRE Brain

We have completed **Phase 2 — Add Multi-Agent System**. This summary reviews the design of our multi-agent architecture, the mechanics of parallel execution (Map-Reduce) in LangGraph, and how to avoid state conflicts.

---

## 1. What is a Multi-Agent System?

A **Multi-Agent System** is a software architecture where several specialized AI agents work collaboratively to solve a complex problem.

### Single Agent vs. Multi-Agent Design
*   **Single Agent (Phase 1):** One LLM prompt reads the entire context (metrics, logs, and version history) and attempts to diagnose the issue. This results in large, complex prompts and makes it hard to scale tools.
*   **Multi-Agent (Phase 2):** We divide the problem. Individual "specialist agents" analyze specific parts of the system load, summarize their findings, and write them back to a shared state. A final "synthesizer agent" reviews the summaries to produce the root-cause report.

---

## 2. LangGraph Parallel Execution: The Map-Reduce Pattern

In LangGraph, we structured our workflow using the **Map-Reduce** pattern:

```
                    Incident Input (Telemetry)
                              │
                    ┌─────────┼─────────┐ [MAP]
                    ▼         ▼         ▼
             Metrics Node  Logs Node  Deployment Node
                    │         │         │
                    └─────────┼─────────┘ [REDUCE / MERGE]
                              ▼
                        Synthesizer Node
```

1.  **Map Step (Parallel branching):** The initial incident state is broadcasted to three nodes simultaneously:
    *   `metrics_node` (MetricsAgent)
    *   `logs_node` (LogsAgent)
    *   `deployment_node` (DeploymentAgent)
2.  **Reduce Step (State Merging):** Once all three nodes complete, LangGraph merges their outputs and routes the state to `rca_node` (RootCauseAgent). The synthesizer consumes the merged findings.

---

## 3. Resolving LangGraph State Merge Conflicts

### The Problem
During development, our parallel nodes initially returned the *entire* state dictionary:
```python
# INCORRECT (Caused conflict)
state['metrics_findings'] = findings
return state
```
Since `metrics_node`, `logs_node`, and `deployment_node` ran concurrently, they all returned the `service` and `cpu` keys at the same step. LangGraph detected that multiple nodes were writing to the same keys simultaneously and threw an `InvalidUpdateError`.

### The Resolution
In LangGraph, nodes should only return **what has changed** (the delta), not the entire state. LangGraph will automatically merge these keys into the shared state:
```python
# CORRECT (State Merging)
return {"metrics_findings": findings}
```

---

## 4. Specialized SRE Agent Configurations

### 1. Metrics Agent
*   **Responsibility:** Evaluates CPU and error rate telemetry.
*   **Rule Output:** Scans CPU spikes (e.g. CPU > 90%) and alerts on error thresholds.

### 2. Logs Agent
*   **Responsibility:** Scans logs for exception track trace signals.
*   **Rule Output:** Highlights database timeouts, connection failures, or memory heap errors.

### 3. Deployment Agent
*   **Responsibility:** Correlates active version changes.
*   **Rule Output:** Logs active releases and alerts that new versions may introduce memory leaks or database schema mismatches.

### 4. Root Cause Agent (Synthesizer)
*   **Responsibility:** Consumes the specialist summaries.
*   **Rule Output:** Forms the final root cause hypothesis and step-by-step remediation advice.

---

## 5. Verification Results

We verified the multi-agent system by writing a new test suite inside `backend/test_main.py`:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/test_main.py
```
*   **Findings Merging test:** Validated that the parallel map-reduce workflow runs and successfully merges metrics, logs, and deployment findings into the final report.
*   **Outcome:** `5 passed in 1.70s` (0 warnings).
