import os
import json
import boto3
from typing import Dict, Any
from root_cause_agent import SREAgentState

class DeploymentAgent:
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

    def _generate_mock_findings(self, state: SREAgentState) -> str:
        version = state.get('deployment', '').strip()
        if not version:
            return "INFO: No recent deployment versions were specified. Telemetry changes could be due to run-time load fluctuations."
            
        return f"INFO: Detected active deployment version '{version}'. Issues occurring immediately after new releases suggest configuration discrepancies, new resource limits, or code regressions introduced in this package."

    def _generate_bedrock_findings(self, state: SREAgentState) -> str:
        prompt = f"""
You are an expert SRE Deployment Analyst Agent.
Correlate the system version and analyze the deployment context for the service. Return a concise summary (max 3 sentences) outlining whether a code release/deployment was active during this incident.

Context:
- Service Name: {state['service']}
- Active Deployment version: {state['deployment']}

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

    def analyze_deployment(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Analyzes the deployment parameters of the state and returns the findings.
        """
        if self.use_bedrock:
            findings = self._generate_bedrock_findings(state)
        else:
            findings = self._generate_mock_findings(state)
            
        return {"deployment_findings": findings}
