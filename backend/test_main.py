from fastapi.testclient import TestClient
import sys
import os

# Adjust path to import main correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from main import app

client = TestClient(app)

def test_health():
    """
    Test the health check endpoint returns 200 and indicates healthy state.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_incident_database_timeout():
    """
    Test that a database timeout telemetry payload is correctly diagnosed
    as a database connection issue by the agent.
    """
    payload = {
        "service": "payment-api",
        "error_rate": "25%",
        "cpu": "65%",
        "deployment": "v1.4.2",
        "logs": [
            "ERROR: Database connection timeout occurred",
            "Failed to establish connection to RDS postgresql-instance"
        ]
    }
    response = client.post("/incident", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "payment-api"
    # The root cause analysis should diagnose database issue
    root_cause_lower = data["root_cause"].lower()
    assert "database" in root_cause_lower or "db" in root_cause_lower or "connection pool" in root_cause_lower
    assert data["confidence"] >= 0.8
    assert len(data["evidence"]) > 0

def test_incident_oom():
    """
    Test that a memory-related log payload is correctly diagnosed
    as an Out-Of-Memory (OOM) error by the agent.
    """
    payload = {
        "service": "auth-service",
        "error_rate": "10%",
        "cpu": "85%",
        "deployment": "v2.0.1",
        "logs": [
            "OutOfMemoryError: Java heap space limits reached",
            "Container processes terminated: OOMKilled status"
        ]
    }
    response = client.post("/incident", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "auth-service"
    root_cause_lower = data["root_cause"].lower()
    assert "memory" in root_cause_lower or "oom" in root_cause_lower or "heap" in root_cause_lower
    assert data["confidence"] >= 0.8

def test_list_and_get_incidents():
    """
    Test that we can create an incident, fetch it by ID, and list all incident reports.
    """
    # 1. Post a new incident
    payload = {
        "service": "billing-service",
        "error_rate": "5%",
        "cpu": "95%",
        "deployment": "v3.0.0",
        "logs": ["High load detected on service CPU"]
    }
    post_res = client.post("/incident", json=payload)
    assert post_res.status_code == 200
    incident_id = post_res.json()["incident_id"]

    # 2. Get that single incident analysis report
    get_res = client.get(f"/incident/{incident_id}")
    assert get_res.status_code == 200
    assert get_res.json()["service"] == "billing-service"

    # 3. List all reports and verify the count includes our new report
    list_res = client.get("/incidents")
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) >= 1
    # Check that our ID is in the list
    ids = [r["incident_id"] for r in reports]
    assert incident_id in ids

def test_multi_agent_findings_merging():
    """
    Test that the LangGraph Orchestrator parallel agents execute 
    and successfully merge metrics, logs, and deployment findings into the evidence.
    """
    payload = {
        "service": "payment-api",
        "error_rate": "15%",
        "cpu": "92%",
        "deployment": "v1.4.2",
        "logs": [
            "ERROR: Database connection timeout",
            "Failed to connect to database"
        ]
    }
    response = client.post("/incident", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Verify the synthesizer successfully received and merged findings from the three specialized agents
    evidence_str = " ".join(data["evidence"]).lower()
    assert "metrics finding:" in evidence_str
    assert "logs finding:" in evidence_str
    assert "deployment finding:" in evidence_str
