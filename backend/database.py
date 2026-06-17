import uuid
from datetime import datetime
from typing import Dict, List, Optional
from models import IncidentPayload, SREAnalysisReport

# Simple in-memory storage for simulated incidents and their corresponding AI reports.
# Keys are incident IDs.
_INCIDENTS_STORE: Dict[str, IncidentPayload] = {}
_REPORTS_STORE: Dict[str, SREAnalysisReport] = {}

class IncidentRepository:
    @staticmethod
    def save_incident(payload: IncidentPayload) -> str:
        """
        Saves a simulated incident payload and returns a generated unique incident ID.
        """
        incident_id = str(uuid.uuid4())
        _INCIDENTS_STORE[incident_id] = payload
        return incident_id

    @staticmethod
    def get_incident(incident_id: str) -> Optional[IncidentPayload]:
        """
        Retrieves a simulated incident by its ID.
        """
        return _INCIDENTS_STORE.get(incident_id)

    @staticmethod
    def save_report(incident_id: str, report: SREAnalysisReport) -> None:
        """
        Saves the AI-generated SRE analysis report.
        """
        _REPORTS_STORE[incident_id] = report

    @staticmethod
    def get_report(incident_id: str) -> Optional[SREAnalysisReport]:
        """
        Retrieves the AI-generated report for an incident.
        """
        return _REPORTS_STORE.get(incident_id)

    @staticmethod
    def list_reports() -> List[SREAnalysisReport]:
        """
        Returns all AI-generated reports.
        """
        return list(_REPORTS_STORE.values())
