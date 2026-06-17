import sys
import os
from fastapi import FastAPI, HTTPException
from datetime import datetime
from dotenv import load_dotenv

# Load configurations from .env file
load_dotenv()

# Adjust Python path to allow importing from the sibling 'ai-agents' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-agents")))

# pyrefly: ignore [missing-import]
from orchestrator import SREOrchestrator
from root_cause_agent import SREAgentState
from models import IncidentPayload, SREAnalysisReport, AWSAccountConnect, CollectIncidentRequest
from database import IncidentRepository, AWSAccountRepository
from aws_collector import AWSCollector

app = FastAPI(
    title="AI-SRE Platform API",
    description="Backend API for the Autonomous Cloud Reliability Engineer platform.",
    version="0.1.0"
)

# Instantiate the SRE LangGraph Orchestrator
orchestrator = SREOrchestrator()

@app.get("/health")
async def health_check():
    """
    Service health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "AI-SRE Backend",
        "version": "0.1.0",
        "bedrock_active": orchestrator.use_bedrock
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
    
    # 3. Run AI Root Cause Analysis via LangGraph Orchestrator
    try:
        updated_state = orchestrator.run_analysis(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Orchestrator failed to run: {str(e)}")
        
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

@app.post("/aws-account")
async def connect_aws_account(payload: AWSAccountConnect):
    """
    Registers a new AWS account and role ARN for connection.
    """
    try:
        account_id_db = AWSAccountRepository.save_account(payload.account_id, payload.role_arn)
        return {
            "status": "connected",
            "account_id": payload.account_id,
            "database_id": account_id_db
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect AWS Account: {str(e)}")

@app.post("/collect-incident", response_model=SREAnalysisReport)
async def collect_and_analyze_incident(payload: CollectIncidentRequest):
    """
    Assumes customer's SRE Connection IAM Role, queries AWS CloudWatch to collect
    live service metrics, stores the incident payload, and performs AI multi-agent diagnosis.
    """
    # 1. Initialize Collector
    collector = AWSCollector()
    
    # 2. Trigger CloudWatch query and save incident telemetry
    try:
        incident_id = collector.collect_incident(
            service_name=payload.service,
            account_id=payload.account_id,
            deployment_version=payload.deployment or "v1.0.0"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pull CloudWatch metrics: {str(e)}")
        
    # 3. Retrieve the saved incident telemetry data
    incident_payload = IncidentRepository.get_incident(incident_id)
    if not incident_payload:
        raise HTTPException(status_code=500, detail="Failed to retrieve collected incident telemetry.")
        
    # 4. Construct LangGraph Agent State
    state: SREAgentState = {
        "service": incident_payload.service,
        "error_rate": incident_payload.error_rate,
        "cpu": incident_payload.cpu,
        "deployment": incident_payload.deployment,
        "logs": incident_payload.logs,
        "metrics_findings": "",
        "logs_findings": "",
        "deployment_findings": "",
        "root_cause": "",
        "confidence": 0.0,
        "evidence": [],
        "recommendation": ""
    }
    
    # 5. Run SRE multi-agent LangGraph analysis
    try:
        updated_state = orchestrator.run_analysis(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI SRE Analysis failed: {str(e)}")
        
    # 6. Construct report object
    report = SREAnalysisReport(
        incident_id=incident_id,
        timestamp=datetime.utcnow(),
        service=incident_payload.service,
        root_cause=updated_state["root_cause"],
        confidence=updated_state["confidence"],
        evidence=updated_state["evidence"],
        recommendation=updated_state["recommendation"]
    )
    
    # 7. Persist report in database
    IncidentRepository.save_report(incident_id, report)
    
    return report
