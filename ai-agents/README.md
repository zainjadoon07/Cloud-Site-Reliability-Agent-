# AI Agents (SRE Brain)

This directory contains our LangGraph-based SRE agent orchestrator and its constituent agents (Metrics Agent, Logs Agent, Deployment Agent, Root Cause Agent).

## Architecture
- **Orchestrator**: Coordinates tasks, passes state between agents.
- **Metrics Agent**: Queries CloudWatch/telemetry metrics.
- **Logs Agent**: Searches and filters log streams.
- **Deployment Agent**: Reviews git and deployment changes.
- **Root Cause Agent**: Performs LLM-based reasoning to identify the root issue and recommend remediation steps.
