from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class IncidentPayload(BaseModel):
    """
    Schema representing the incoming simulated telemetry data for an incident.
    """
    service: str = Field(..., examples=["payment-api"], description="The name of the service experiencing issues.")
    error_rate: str = Field(..., examples=["25%"], description="The current error rate of the service.")
    cpu: str = Field(..., examples=["95%"], description="CPU utilization percentage.")
    deployment: str = Field(..., examples=["v1.4.2"], description="Active deployment version of the service.")
    logs: List[str] = Field(default=[], examples=[["database timeout", "connection pool exhausted"]], description="Recent log lines from the service.")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Time of the simulated incident.")

class SREAnalysisReport(BaseModel):
    """
    Schema representing the AI-generated SRE analysis report.
    """
    incident_id: str = Field(..., description="Unique UUID for the incident.")
    timestamp: datetime = Field(..., description="Timestamp of the analysis.")
    service: str = Field(..., description="The service analyzed.")
    root_cause: str = Field(..., description="AI-diagnosed root cause of the incident.")
    confidence: float = Field(..., description="AI confidence score between 0.0 and 1.0 (or percentage).")
    evidence: List[str] = Field(..., description="Key data points (metrics, logs, versions) that support the diagnosis.")
    recommendation: str = Field(..., description="AI-generated step-by-step remediation recommendation.")

class AWSAccountConnect(BaseModel):
    """
    Schema for connecting a customer AWS Account.
    """
    account_id: str = Field(..., min_length=12, max_length=12, examples=["123456789012"], description="The 12-digit AWS Account ID.")
    role_arn: str = Field(..., examples=["arn:aws:iam::123456789012:role/SREConnectionRole"], description="The cross-account SRE Connection Role ARN.")

class CollectIncidentRequest(BaseModel):
    """
    Schema for triggering automated CloudWatch collection of an incident.
    """
    service: str = Field(..., examples=["payment-api"], description="The name of the service to analyze.")
    account_id: str = Field(..., min_length=12, max_length=12, examples=["123456789012"], description="The 12-digit AWS Account ID.")
    deployment: Optional[str] = Field(default="v1.0.0", examples=["v1.4.2"], description="The active version tag.")
