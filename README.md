# AI-Powered Cloud Operations Engineer (AI-SRE Platform)

An autonomous Site Reliability Engineering (SRE) platform that connects securely to AWS environments, retrieves CloudWatch metrics and logs using temporary credentials, and orchestrates a multi-agent LangGraph system to perform root-cause analysis and generate remediation recommendations.

---

## 🏗️ Architecture & Flow

```
                      +-----------------------------------------+
                      |       Customer AWS Account              |
                      |   +─────────────────────────────────+   |
                      |   │       SREConnectionRole         │   |
                      |   │ (Read-Only access to telemetry) │   |
                      |   +────────────────┬────────────────+   |
                      +----------------────┼────────────────----+
                                           │
                                           │ (STS AssumeRole token exchange)
                                           ▼
+-------------------------------------------------------------------------------+
|                        AI-SRE Platform Backend                                |
|                                                                               |
|   +──────────────────────+    +─────────────────────+   +─────────────────+   |
|   │     AWS Collector    │◄──►│ Persistent Database │◄──►│   FastAPI API   │   |
|   │  (AssumeRole boto3)  │    │  (PostgreSQL/Docker)│   │ (/collect-inc)  │   |
|   +──────────┬───────────+    +─────────────────────+   +────────┬────────+   |
|              │                                                   │            |
|              │ (Telemetry state payload)                         │            |
|              ▼                                                   ▼            |
|   +──────────────────────────────────────────────────────────────┴────────+   |
|   │                      LangGraph Orchestrator                           │   |
|   │                                                                       │   |
|   │     ┌───────────────┐      ┌─────────────┐      ┌─────────────────┐   │   |
|   │     │ Metrics Agent │      │  Logs Agent │      │Deployment Agent │   │   |
|   │     └───────┬───────┘      └───────┬─────┘      └────────┬────────┘   │   |
|   │             │                     │                      │            |   |
|   │             └─────────────────────┼──────────────────────┘            │   |
|   │                                   ▼                                   │   |
|   │                     Root Cause Agent (Synthesizer)                    │   |
|   │                        (AWS Bedrock / Mock LLM)                       │   |
|   +-----------------------------------------------------------------------+   |
+-------------------------------------------------------------------------------+
```

---

## 📂 Project Structure

```
├── backend/
│   ├── main.py            # FastAPI API Gateway routes (/health, /aws-account, /collect-incident)
│   ├── models.py          # Pydantic schemas validating API requests/responses
│   ├── database.py        # SQLAlchemy database mapping and CRUD repository operations
│   ├── aws_collector.py   # Boto3 client executing STS AssumeRole and CloudWatch metric queries
│   ├── test_main.py       # Pytest integration suite for database & endpoints
│   └── requirements.txt   # Python application dependencies
├── ai-agents/
│   ├── orchestrator.py    # LangGraph multi-agent parallel map-reduce workflow compiler
│   ├── metrics_agent.py   # Specialist node evaluating system metrics
│   ├── logs_agent.py      # Specialist node analyzing application log tracebacks
│   ├── deployment_agent.py# Specialist node correlating code releases
│   └── root_cause_agent.py# Synthesizer node producing final incident reports
├── docs/
│   ├── module_0_summary.md# SRE Foundations & setup notes
│   ├── module_1_summary.md# API & single agent simulation summary
│   ├── module_2_summary.md# Multi-agent graph & state updates report
│   └── module_3_summary.md# AWS STS AssumeRole & database connection report
├── docker-compose.yml     # Persistent local PostgreSQL database service
└── .gitignore             # Version control exclusion file
```

---

## 🚀 Getting Started

### Prerequisites
- **Python:** Version `3.11.x`
- **Docker Desktop:** (For running persistent PostgreSQL)
- **AWS CLI:** Configure credentials by running `aws configure`

### 1. Database Setup
Start the persistent local PostgreSQL instance:
```bash
docker compose up -d
```
*(If Docker Desktop is offline, the backend resilient driver automatically falls back to a local SQLite file `sre_local.db` dynamically to keep the system active.)*

### 2. Python Virtual Environment
Navigate to the root and configure dependencies:
```powershell
# Create & Activate Virtual Environment
python -m venv backend/venv
backend\venv\Scripts\Activate.ps1

# Install dependencies
backend\venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

### 3. Run Application Server
Start the FastAPI server:
```powershell
cd backend
venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Visit API Documentation at: `http://localhost:8000/docs`.

### 4. Running Integration Tests
Execute the pytest suite:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/test_main.py
```
*(Test execution runs at 4.0s against live PostgreSQL and automatically leverages STS AssumeRole graceful fallbacks for offline environments.)*
