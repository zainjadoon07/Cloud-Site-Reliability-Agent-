import sys
import os
from fastapi import FastAPI, HTTPException
from datetime import datetime

# Adjust Python path to allow importing from the sibling 'ai-agents' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-agents")))

# pyrefly: ignore [missing-import]
from root_cause_agent import RootCauseAgent, SREAgentState
from models import IncidentPayload, SREAnalysisReport
from database import IncidentRepository

app = FastAPI(
    title="AI-SRE Platform API",
    description="Backend API for the Autonomous Cloud Reliability Engineer platform.",
    version="0.1.0"
)

# Instantiate the AI Root Cause Agent
agent = RootCauseAgent()

@app.get("/health")
async def health_check():
    """
    Service health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "AI-SRE Backend",
        "version": "0.1.0",
        "bedrock_active": agent.use_bedrock
    }

@app.post("/incident", response_model=SREAnalysisReport)
async def analyze_incident(payload: IncidentPayload):
    """
    Receives a simulated incident telemetry payload, saves it,
    runs the SRE AI Root Cause Agent, saves the result, and returns the analysis.
    """
    # 1. Save incoming telemetry incident
    incident_id = IncidentRepository.save_incident(payload)
    
    # 2. Construct LangGraph Agent State
    state: SREAgentState = {
        "service": payload.service,
        "error_rate": payload.error_rate,
        "cpu": payload.cpu,
        "deployment": payload.deployment,
        "logs": payload.logs,
        "metrics_findings": "",
        "logs_findings": "",
        "deployment_findings": "",
        "root_cause": "",
        "confidence": 0.0,
        "evidence": [],
        "recommendation": ""
    }
    
    # 3. Run AI Root Cause Analysis node
    try:
        updated_state = agent.analyze_incident(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine failed to run: {str(e)}")
        
    # 4. Construct response report object
    report = SREAnalysisReport(
        incident_id=incident_id,
        timestamp=datetime.utcnow(),
        service=payload.service,
        root_cause=updated_state["root_cause"],
        confidence=updated_state["confidence"],
        evidence=updated_state["evidence"],
        recommendation=updated_state["recommendation"]
    )
    
    # 5. Persist report in database repository
    IncidentRepository.save_report(incident_id, report)
    
    return report

@app.get("/incidents", response_model=list[SREAnalysisReport])
async def list_incidents():
    """
    Lists all SRE analysis reports generated.
    """
    return IncidentRepository.list_reports()

@app.get("/incident/{incident_id}", response_model=SREAnalysisReport)
async def get_incident(incident_id: str):
    """
    Retrieves a specific incident analysis report by its unique ID.
    """
    report = IncidentRepository.get_report(incident_id)
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found.")
    return report
