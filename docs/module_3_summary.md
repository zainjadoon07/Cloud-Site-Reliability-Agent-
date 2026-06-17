# Module 3 Summary: AWS Integration and Databases

We have completed **Phase 3 — AWS Integration & Databases**. This module marks the transition of our platform from static simulations to a resilient database-backed architecture capable of querying real AWS telemetry APIs.

---

## 1. AWS IAM Security and Cross-Account Role Assumptions

In production cloud operations, we must **never** ask clients to give us their permanent IAM User access keys. That is a critical security vulnerability. Instead, we use **AWS STS (Security Token Service) Cross-Account Role Assumptions**.

### How STS AssumeRole Works:
```
  AI-SRE Platform Account                     Customer AWS Account
 ┌───────────────────────┐                  ┌──────────────────────┐
 │                       │                  │  [SREConnectionRole] │
 │  [sre-dev-user]       ├─────────────────►│  Trusts platform user│
 │  Calls sts.assume_role│  (STS Exchange)  │  Has Read-Only policy│
 │                       │◄─────────────────┤                      │
 │  Gets temporary keys  │  Temporary keys  └──────────────────────┘
 └──────────┬────────────┘  (Expires 1hr)
            │
            ▼
 Queries CloudWatch Metrics
```

1.  **Trust Definition:** Inside the Customer's Account, they create an IAM Role (e.g. `SREConnectionRole`) and configure its **Trust Policy** to allow our platform's IAM User ARN (`sre-dev-user`) to assume it.
2.  **API Call:** Our backend executes `sts.assume_role()` pointing to the customer's role ARN.
3.  **STS Token Exchange:** AWS verifies the trust policy. If authorized, STS returns **temporary credentials** (an Access Key ID, Secret Access Key, and Session Token) that automatically expire (e.g. in 1 hour).
4.  **Least Privilege:** Even if our platform is compromised, these keys are temporary. The role itself is attached to a restricted policy like `CloudWatchReadOnlyAccess`, guaranteeing we can never write or delete client resources.

---

## 2. Resilient Database Layer (SQLAlchemy ORM + Fallbacks)

### Moving to Database Persistence
We introduced SQLAlchemy ORM models mapped to PostgreSQL database tables:
*   **`aws_accounts`:** Stores Customer Account IDs, assumed role ARNs, and connection status.
*   **`incidents`:** Stores telemetry snapshots.
*   **`reports`:** Stores AI-generated analysis reports linked to incidents.

### High-Availability Fallback: PostgreSQL to SQLite
In SRE, **resilience is everything**. We engineered our database client inside [database.py](file:///c:/Users/zainu/OneDrive/Desktop/Cloud%20Reliability%20Agent/backend/database.py) to check for PostgreSQL availability:
1.  On application start, SQLAlchemy attempts to connect to our local PostgreSQL database container on port `5432` with a 2-second timeout.
2.  **Active Mode:** If PostgreSQL is up (via `docker compose`), the engine connects and maps tables.
3.  **Fallback Mode:** If Docker Desktop is offline, the code catches the connection exception and falls back to a local **SQLite database file** (`sre_local.db`).
This guarantees that developers can run the entire platform and test suite offline with zero container configurations, while keeping identical repository APIs!

---

## 3. Telemetry Collector: Querying Amazon CloudWatch

Our collector inside [aws_collector.py](file:///c:/Users/zainu/OneDrive/Desktop/Cloud%20Reliability%20Agent/backend/aws_collector.py) fetches telemetry using `boto3`:
*   **STS Client:** Obtains the temporary credentials.
*   **CloudWatch Client:** Calls `get_metric_data` to retrieve timeseries data.
    *   `AWS/EC2` Namespace -> `CPUUtilization` (Average CPU load query).
    *   `AWS/ApplicationELB` Namespace -> `HTTPCode_Target_5XX_Count` (Sum of target ELB errors query).
*   **Error Tolerance:** If the connection to AWS fails (e.g. role not configured yet), the collector logs the warning, injects warning details into the telemetry logs, and generates a fallback telemetry dataset so the downstream SRE multi-agent brain can analyze the connection failure itself!

---

## 4. Verification Results

We verified Phase 3 by executing the pytest integration suite:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/test_main.py
```
*   **`test_connect_aws_account`:** Validated that customer AWS credentials register and store correctly.
*   **`test_collect_and_analyze_incident`:** Validated the full AWS collector-driven incident analysis flow (STS AssumeRole connection fallback + CloudWatch query simulation + state merging).
*   **Outcome:** `7 passed in 15.73s` (0 warnings).
