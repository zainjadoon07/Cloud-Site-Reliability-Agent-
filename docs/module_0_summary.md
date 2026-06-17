# Module 0 Summary: SRE and AI Foundation

Welcome to your first learning report! This summary captures the foundational concepts and infrastructure setup we completed during **Phase 0 — Foundation**.

---

## 1. Core Concept: Site Reliability Engineering (SRE)

**Site Reliability Engineering (SRE)** is a software engineering approach to IT operations. SRE teams use software as a tool to manage systems, solve problems, and automate operations tasks.

### Key SRE Terminology
*   **SLI (Service Level Indicator):** A carefully defined quantitative measure of some aspect of the level of service provided.
    *   *Example:* Request latency (response time), throughput, error rate, availability.
*   **SLO (Service Level Objective):** A target value or range of values for a service level that is measured by an SLI.
    *   *Example:* The service must respond in less than 200 milliseconds for 99% of requests.
*   **SLA (Service Level Agreement):** A legal commitment between a service provider and a client specifying what happens if the service fails to meet the SLO.
    *   *Example:* If availability falls below 99.9%, the client receives a 10% refund. SREs focus on SLOs, while business/legal teams handle SLAs.
*   **Error Budget:** The allowable rate of failure. It is calculated as `100% - SLO`.
    *   *Example:* If your availability SLO is 99.9%, your error budget is 0.1% downtime (about 43 minutes of downtime per month). SREs use this budget to balance the deployment of new features (which introduces risk) with stability.

---

## 2. Core Concept: AWS Bedrock

**Amazon Bedrock** is a fully managed service that makes foundation models (FMs) from Amazon and leading AI startups (like Anthropic, Meta, Cohere) available through an API.

### Why AWS Bedrock?
*   **Serverless LLMs:** Instead of deploying and running high-end GPUs to host models like Llama or Claude, Bedrock handles all infrastructure scaling.
*   **Data Security:** Any data we send to Bedrock is encrypted and does not leave our AWS environment. Amazon guarantees that customer data is not used to train the base models.
*   **Unified API:** We can switch between different models (e.g., Anthropic Claude for complex SRE agent reasoning, Amazon Titan for fast embeddings) using the exact same Python SDK (`boto3`).

### How Bedrock Access Works (Authentication)
1.  **Model Access Enablement:** By default, Bedrock models are locked. You must go to the AWS Bedrock Console, navigate to "Model Access," and check the box to request access for the models you want to use (such as Claude 3.5 Sonnet or Llama 3).
2.  **IAM Permissions:** The backend application needs permissions to invoke the Bedrock API. We grant this via IAM roles or policies (e.g., `bedrock:InvokeModel`).
3.  **Boto3 SDK:** Python connects using AWS credentials, retrieves the prompt, calls `bedrock-runtime`, and receives the model response.

---

## 3. Local Development Verification Results

We verified your local developer environment. All critical tools are installed and ready to go:
*   **Python:** `3.11.8` (Ready for FastAPI backend and LangGraph agents)
*   **Node.js:** `v22.19.0` (Ready for Next.js dashboard)
*   **npm:** `10.9.3` (Package manager for frontend dependencies)
*   **Git:** `2.45.2.windows.1` (For version control)
*   **Docker:** `28.1.1` (Ready for local database testing and service containers)

---

## 4. Repository Structure Initialized

The project directories have been created in the workspace root:
*   **`backend/`:** Contains the FastAPI backend, requirements, and main server logic.
*   **`frontend/`:** Placeholder for our Next.js dashboard.
*   **`ai-agents/`:** Placeholder for the LangGraph-based multi-agent system.
*   **`terraform/`:** Placeholder for Infrastructure as Code (IaC).
*   **`docs/`:** Holds reports, learning materials, and system architecture details.
