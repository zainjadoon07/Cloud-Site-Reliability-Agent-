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
