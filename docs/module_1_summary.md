# Module 1 Summary: Fake Incident Simulator and SRE Brain

We have completed **Phase 1 — Build Fake Incident Simulator**. This summary details the key architectural patterns, API mechanics, and AI agent reasoning concepts built during this phase.

---

## 1. Core Concept: REST APIs and POST Requests

An **API (Application Programming Interface)** allows different software services to communicate with each other. In modern web architectures, we use **REST (Representational State Transfer)** over HTTP.

### HTTP Methods (Verbs)
*   **GET:** Used to retrieve data from a resource. It must be idempotent (running it multiple times should not change the system state).
    *   *Example:* `GET /incidents` retrieves all SRE reports.
*   **POST:** Used to submit data to a resource, often creating a new entity or triggering an action.
    *   *Example:* `POST /incident` submits simulated telemetry (CPU spikes, memory logs) and triggers SRE AI analysis.

---

## 2. Core Concept: AI Agents and LangGraph

### What is an AI Agent?
An **AI Agent** is a software design pattern where an LLM is placed in a loop and given "agency"—the ability to make decisions, execute logic, use tools, and inspect environment outputs to achieve a specific goal.

Unlike standard chatbots that respond linearly to a single prompt, SRE agents can:
1. Parse unstructured log lines.
2. Formulate hypotheses about system state.
3. Decide what additional data points (metrics, versions) are needed.
4. Render a structured diagnosis.

### What is LangGraph?
**LangGraph** is a library for building stateful, multi-agent applications with graphs. It defines the agent flow using:
*   **State:** A central, shared data structure passed from node to node (e.g., CPU metrics, logs, deployment version, and current findings).
*   **Nodes:** Independent python functions or agents that inspect the state, run logic (e.g. call an LLM), and append their findings back to the state.
*   **Edges:** Define the routing logic between nodes (e.g., if metrics are high, route to CPU Agent; if database errors are found, route to Logs Agent).

---

## 3. The Root Cause Agent (RCA) Reasoning Loop

The **Root Cause Agent** we built in `ai-agents/root_cause_agent.py` uses a **dual-mode architecture**:

1.  **AWS Bedrock Mode (Production):** Connects to Amazon Bedrock runtime client using `boto3`. It sends a prompt containing:
    *   System context (Service name, active code version).
    *   Performance metrics (CPU, error rate).
    *   Telemetry (unstructured logs).
    It instructs the LLM to output a precise, structured JSON report containing `root_cause`, `confidence`, `evidence`, and `recommendation`.
2.  **Mock LLM Mode (Local Testing):** If AWS credentials are not configured, the agent utilizes rule-based heuristics. It scans telemetry logs and metrics for keywords (like "timeout", "OOM", "heap") to dynamically generate realistic SRE analysis reports offline.

---

## 4. Codebase Architecture Summary

```
c:\Users\zainu\OneDrive\Desktop\Cloud Reliability Agent/
├── backend/
│   ├── main.py           # FastAPI entrypoint defining REST API routes (/health, /incident)
│   ├── models.py         # Pydantic schemas validating API inputs/outputs
│   ├── database.py       # Local in-memory repository (mocking PostgreSQL CRUD operations)
│   ├── test_main.py      # Pytest suite validating API routes and agent rules
│   └── requirements.txt  # Project Python dependencies
└── ai-agents/
    └── root_cause_agent.py # SRE Root Cause Agent logic and LangGraph state schemas
```

---

## 5. Verification Results

We verified Phase 1 by running the integration test suite:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/test_main.py
```
*   **Health Checks:** Tested `/health` route validation.
*   **DB Timeout Diagnosis:** Verified that logs indicating database timeouts are caught and diagnosed as connection issues with a high confidence score.
*   **Memory Limit (OOM) Diagnosis:** Verified that logs indicating heap issues and process termination are diagnosed as memory limits exceeded (OOMKilled).
*   **Report Retrieval:** Verified that reports are indexed in-memory and retrievable via GET routes.
*   **Outcome:** `4 passed with 0 warnings` (Resolved the StarletteDeprecationWarning by installing both `httpx2` and `httpx` to satisfy third-party dependencies).
