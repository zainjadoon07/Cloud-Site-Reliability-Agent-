import os
import json
import boto3
from typing import Dict, Any
from root_cause_agent import SREAgentState

class MetricsAgent:
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
        cpu_val = 0.0
        try:
            # Extract only the numeric prefix before the '%' symbol to support mock text
            cpu_clean = state['cpu'].split("%")[0].strip()
            cpu_val = float(cpu_clean)
        except Exception:
            pass

        findings = []
        if cpu_val >= 90.0:
            findings.append(f"CRITICAL: CPU utilization is extremely high at {state['cpu']}. This is causing severe resource exhaustion and scheduling latency.")
        elif cpu_val >= 70.0:
            findings.append(f"WARNING: CPU utilization is elevated at {state['cpu']}. Performance degradation might occur under load spikes.")
        else:
            findings.append(f"INFO: CPU utilization is healthy at {state['cpu']}.")

        if "%" in state['error_rate']:
            try:
                err_clean = state['error_rate'].split("%")[0].strip()
                err_val = float(err_clean)
                if err_val > 10.0:
                    findings.append(f"CRITICAL: Error rate is at {state['error_rate']}, which exceeds the standard 1% reliability threshold.")
                elif err_val > 2.0:
                    findings.append(f"WARNING: Error rate is elevated at {state['error_rate']}.")
            except Exception:
                pass
        
        return " | ".join(findings)

    def _generate_bedrock_findings(self, state: SREAgentState) -> str:
        prompt = f"""
You are an expert SRE Telemetry Metrics Agent.
Analyze the following metrics and return a concise summary (max 3 sentences) of your findings regarding system load and error rates.

Metrics:
- Service Name: {state['service']}
- CPU Utilization: {state['cpu']}
- Error Rate: {state['error_rate']}

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

    def analyze_metrics(self, state: SREAgentState) -> Dict[str, Any]:
        """
        Analyzes the metric parameters of the state and returns the findings.
        """
        if self.use_bedrock:
            findings = self._generate_bedrock_findings(state)
        else:
            findings = self._generate_mock_findings(state)
            
        return {"metrics_findings": findings}
