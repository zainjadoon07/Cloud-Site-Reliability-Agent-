import json
import os
import boto3
from typing import TypedDict, List, Dict, Any

# --- LangGraph State Definition ---
class SREAgentState(TypedDict):
    service: str
    error_rate: str
    cpu: str
    deployment: str
    logs: List[str]
    
    # Internal agent findings (now filled by specialists)
    metrics_findings: str
    logs_findings: str
    deployment_findings: str
    
    # Final diagnosis results
    root_cause: str
    confidence: float
    evidence: List[str]
    recommendation: str

class RootCauseAgent:
    def __init__(self):
        self.aws_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        self.use_bedrock = False
        
        try:
            self.bedrock = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.aws_region
            )
            if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI") or os.path.exists(os.path.expanduser("~/.aws/credentials")):
                self.use_bedrock = True
        except Exception:
            self.use_bedrock = False

    def _generate_mock_analysis(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Synthesizes findings from specialized agents locally to produce SRE report.
        """
        metrics = state.get('metrics_findings', '').lower()
        logs = state.get('logs_findings', '').lower()
        deployment = state.get('deployment_findings', '').lower()

        evidence = []
        root_cause = "General system regression detected."
        recommendation = "Review SRE logs and database clusters."
        confidence = 0.75

        # Incorporate specialist evidence
        if state['metrics_findings']:
            evidence.append(f"Metrics Finding: {state['metrics_findings']}")
        if state['logs_findings']:
            evidence.append(f"Logs Finding: {state['logs_findings']}")
        if state['deployment_findings']:
            evidence.append(f"Deployment Finding: {state['deployment_findings']}")

        # Synthesis rules
        is_database_exhaustion = "database" in logs and "pool" in logs
        is_oom_kill = "oom" in logs or "memory" in logs
        is_release_regression = "deployment version" in deployment or "new releases" in deployment

        if is_database_exhaustion:
            root_cause = "Database connection pool exhaustion."
            confidence = 0.92
            recommendation = (
                "1. Scale database connection capacity or increase pool size configuration.\n"
                "2. Check for long-running unindexed transactions in RDS performance insights.\n"
                "3. Rollback the latest code deployment if it includes query regressions."
            )
        elif is_oom_kill:
            root_cause = "Application container out-of-memory (OOMKilled) crash."
            confidence = 0.90
            recommendation = (
                "1. Increase ECS/EKS container memory request and limits.\n"
                "2. Run memory profiling to locate heap leaks.\n"
                "3. Restart the tasks to release cached memory pools."
            )
        elif "critical" in metrics:
            root_cause = "CPU starvation causing server queue exhaustion."
            confidence = 0.82
            recommendation = (
                "1. Scale container count (horizontal replicas) immediately.\n"
                "2. Profile API endpoints for cpu-intensive tasks.\n"
                "3. Check for external request flooding/DDoS signs."
            )
        else:
            root_cause = "Performance degradation after service environment change."
            recommendation = "Inspect system telemetry graphs on Amazon CloudWatch for latent anomalies."

        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": recommendation
        }

    def _generate_bedrock_analysis(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Synthesizes specialized findings into a final report using AWS Bedrock.
        """
        prompt = f"""
You are the Lead SRE Incident Commander Agent.
Analyze the findings reported by three specialized SRE agents (Metrics, Logs, and Deployment) and write a synthesized incident analysis report.

Specialist Agent Findings:
- Metrics Agent: {state['metrics_findings']}
- Logs Agent: {state['logs_findings']}
- Deployment Agent: {state['deployment_findings']}

Your response must be a valid JSON object containing exactly the following keys:
- root_cause: (string describing the primary synthesized reason)
- confidence: (float value between 0.0 and 1.0 representing your diagnostic confidence)
- evidence: (array of strings showing key facts extracted from the specialist findings)
- recommendation: (string with markdown-styled numbered steps for remediation)

Return ONLY raw JSON, with no explanation or wrapping. Do not include markdown code block syntax (like ```json).
"""
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "temperature": 0.1
        })
        
        try:
            response = self.bedrock.invoke_model(
                modelId=model_id,
                body=body
            )
            response_body = json.loads(response.get('body').read())
            completion_text = response_body['content'][0]['text'].strip()
            return json.loads(completion_text)
        except Exception as e:
            mock_res = self._generate_mock_analysis(state)
            mock_res["root_cause"] = f"[Bedrock Fallback: {str(e)}] " + mock_res["root_cause"]
            return mock_res

    def analyze_incident(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Master synthesis node. Evaluates findings and returns final incident report updates.
        """
        if self.use_bedrock:
            analysis = self._generate_bedrock_analysis(state)
        else:
            analysis = self._generate_mock_analysis(state)
            
        return {
            "root_cause": analysis.get('root_cause', 'Unknown anomaly.'),
            "confidence": analysis.get('confidence', 0.50),
            "evidence": analysis.get('evidence', []),
            "recommendation": analysis.get('recommendation', 'Check logs.')
        }
