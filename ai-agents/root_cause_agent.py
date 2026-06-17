import json
import os
import boto3
from typing import TypedDict, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

# --- LangGraph State Definition ---
# In LangGraph, State is a schema that gets passed around between nodes.
# Each agent node reads from this state and writes findings back into it.
class SREAgentState(TypedDict):
    service: str
    error_rate: str
    cpu: str
    deployment: str
    logs: List[str]
    
    # Internal agent findings (filled in multi-agent phases)
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
        # We look for Bedrock environment variables. If present, we attempt connection.
        self.aws_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        self.use_bedrock = False
        
        # Test if AWS credentials are set up for Bedrock
        try:
            # Try to create a client with short timeout to verify if user has credentials configured
            self.bedrock = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.aws_region
            )
            # Simple check: do we have AWS keys in env?
            if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI") or os.path.exists(os.path.expanduser("~/.aws/credentials")):
                self.use_bedrock = True
        except Exception:
            self.use_bedrock = False

    def _generate_mock_analysis(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Generates a highly detailed SRE analysis report locally without calling AWS Bedrock.
        Uses rule-based heuristics based on telemetry logs and metrics to simulate AI reasoning.
        """
        logs_str = " ".join(state['logs']).lower()
        cpu_val = 0.0
        try:
            cpu_val = float(state['cpu'].replace("%", "").strip())
        except ValueError:
            pass
            
        error_rate_val = 0.0
        try:
            error_rate_val = float(state['error_rate'].replace("%", "").strip())
        except ValueError:
            pass

        evidence = []
        root_cause = "Unknown system anomaly detected."
        recommendation = "Investigate application metrics and log streams manually."
        confidence = 0.70

        # Correlation rules (Simulating SRE heuristics)
        is_database_issue = any(k in logs_str for k in ["db", "database", "sql", "postgres", "timeout", "connection refused", "pool"])
        is_oom = any(k in logs_str for k in ["oom", "out of memory", "oomkilled", "heap", "killed"])
        is_cpu_spike = cpu_val >= 90.0

        if is_database_issue:
            root_cause = "Database connection pool exhaustion or network timeout."
            confidence = 0.90
            evidence.append(f"Logs detected database connection failures: {[l for l in state['logs'] if 'db' in l.lower() or 'timeout' in l.lower() or 'connection' in l.lower()]}")
            evidence.append(f"Service '{state['service']}' is running deployment version {state['deployment']}")
            recommendation = (
                "1. Verify database instance CPU and connections in AWS Console.\n"
                "2. Increase the max connection pool limits in service environment variables.\n"
                "3. Review recent database queries for unindexed scans."
            )
        elif is_oom:
            root_cause = "JVM/Node.js heap memory limit exceeded, leading to process OOMKilled."
            confidence = 0.88
            evidence.append(f"Logs contain memory limit indicators: {[l for l in state['logs'] if 'memory' in l.lower() or 'oom' in l.lower() or 'killed' in l.lower()]}")
            evidence.append(f"Current container CPU utilization is at {state['cpu']}")
            recommendation = (
                "1. Increase container memory limit inside ECS/EKS task definition.\n"
                "2. Analyze application memory dumps to verify memory leak presence.\n"
                "3. Rollback the active deployment if this is a newly introduced memory leak."
            )
        elif is_cpu_spike:
            root_cause = "High CPU utilization causing request queueing and backend latency spike."
            confidence = 0.85
            evidence.append(f"CPU metrics reached critical threshold: {state['cpu']}")
            evidence.append(f"Active deployment: {state['deployment']}")
            recommendation = (
                "1. Scale out the service tasks (increase replica count) to distribute load.\n"
                "2. Profile service execution to identify compute-heavy hot paths.\n"
                "3. Check for external API rate-limiting or retry loops."
            )
        else:
            evidence.append(f"Service running version {state['deployment']} reported errors.")
            if state['logs']:
                evidence.append(f"Sample log line: {state['logs'][0]}")
            recommendation = "Review container deployment logs and system telemetry on Amazon CloudWatch."

        if state['deployment']:
            evidence.append(f"Incident occurred during active deployment version {state['deployment']}")
            
        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": recommendation
        }

    def _generate_bedrock_analysis(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Calls AWS Bedrock with a structured prompt asking for an SRE analysis report.
        """
        prompt = f"""
You are an expert Site Reliability Engineer (SRE) Agent.
Analyze the following incident data and return a JSON report outlining the root cause, confidence score, evidence list, and step-by-step remediation recommendation.

Incident Data:
- Service Name: {state['service']}
- Error Rate: {state['error_rate']}
- CPU Utilization: {state['cpu']}
- Active Deployment Version: {state['deployment']}
- Recent Application Logs:
{chr(10).join(['  * ' + log for log in state['logs']])}

Your response must be a valid JSON object with EXACTLY the following keys:
- root_cause: (string describing the primary reason)
- confidence: (float value between 0.0 and 1.0 representing your diagnostic confidence)
- evidence: (array of strings showing telemetry proof from the input data)
- recommendation: (string with markdown-styled numbered steps for remediation)

Return ONLY raw JSON, with no explanation or wrapping. Do not include markdown code block syntax (like ```json).
"""
        # We will use Anthropic Claude 3 Haiku or Claude 3.5 Sonnet on Bedrock
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
            
            # Parse the JSON response
            return json.loads(completion_text)
        except Exception as e:
            # Fall back to local analysis if Bedrock call fails (e.g. model not enabled yet)
            mock_res = self._generate_mock_analysis(state)
            mock_res["root_cause"] = f"[Bedrock Fallback: {str(e)}] " + mock_res["root_cause"]
            return mock_res

    def analyze_incident(self, state: SREAgentState) -> SREAgentState:
        """
        LangGraph node execution function. Analyzes the current state and returns updated state keys.
        """
        if self.use_bedrock:
            analysis = self._generate_bedrock_analysis(state)
        else:
            analysis = self._generate_mock_analysis(state)
            
        state['root_cause'] = analysis.get('root_cause', 'Unknown anomaly.')
        state['confidence'] = analysis.get('confidence', 0.50)
        state['evidence'] = analysis.get('evidence', [])
        state['recommendation'] = analysis.get('recommendation', 'Check logs.')
        return state
