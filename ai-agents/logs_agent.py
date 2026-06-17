import os
import json
import boto3
from typing import Dict, Any
from root_cause_agent import SREAgentState

class LogsAgent:
    def __init__(self):
        self.aws_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        
        # Check if Bedrock is explicitly enabled via environment configuration
        env_enabled = os.environ.get("USE_BEDROCK", "false").lower() == "true"
        self.use_bedrock = False
        
        if env_enabled:
            try:
                self.bedrock = boto3.client(
                    service_name="bedrock-runtime",
                    region_name=self.aws_region
                )
                self.use_bedrock = True
            except Exception:
                self.use_bedrock = False

    def _generate_mock_findings(self, state: SREAgentState) -> str:
        logs = state.get('logs', [])
        if not logs:
            return "INFO: Log stream is empty. No anomalous log lines detected."
            
        logs_str = " ".join(logs).lower()
        findings = []
        
        # Check for DB issues
        if any(k in logs_str for k in ["timeout", "connection refused", "db", "database", "postgres", "mysql", "pool"]):
            findings.append("CRITICAL: Detected database connectivity anomalies in logs. Connection pool limits might have been reached or DB is unresponsive.")
            # Find specific line
            matching_lines = [l for l in logs if any(k in l.lower() for k in ["timeout", "connection", "db"])]
            if matching_lines:
                findings.append(f"Sample log error: '{matching_lines[0]}'")
                
        # Check for OOM / Memory issues
        elif any(k in logs_str for k in ["oom", "out of memory", "heap", "killed", "oomkilled"]):
            findings.append("CRITICAL: Detected Out-Of-Memory (OOM) signatures. The container process was likely terminated due to heap exhaustion or task memory limit constraints.")
            matching_lines = [l for l in logs if any(k in l.lower() for k in ["memory", "oom", "killed"])]
            if matching_lines:
                findings.append(f"Sample log error: '{matching_lines[0]}'")
                
        else:
            findings.append("WARNING: Telemetry logs indicate generic exceptions or warning states.")
            findings.append(f"Sample warning: '{logs[0]}'")

        return " | ".join(findings)

    def _generate_bedrock_findings(self, state: SREAgentState) -> str:
        prompt = f"""
You are an expert SRE Application Log Analysis Agent.
Analyze the following logs from the service and return a concise summary (max 3 sentences) of the anomalies, error codes, and exceptions found in the log stream.

Logs:
- Service Name: {state['service']}
- Log Lines:
{chr(10).join(['  * ' + l for l in state['logs']])}

Return ONLY your concise findings as a plain text string. Do not include JSON formatting or conversational prefixes.
"""
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "temperature": 0.1
        })
        
        try:
            response = self.bedrock.invoke_model(modelId=model_id, body=body)
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text'].strip()
        except Exception as e:
            return f"[Bedrock Fallback Error: {str(e)}] " + self._generate_mock_findings(state)

    def analyze_logs(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Analyzes the log content in the state and returns the findings.
        """
        if self.use_bedrock:
            findings = self._generate_bedrock_findings(state)
        else:
            findings = self._generate_mock_findings(state)
            
        return {"logs_findings": findings}
