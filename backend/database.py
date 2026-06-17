import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from models import IncidentPayload, SREAnalysisReport

# Fetch Database connection URL from environment variables or default to local compose config
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://sre_user:sre_password@localhost:5432/sre_db"
)

# Resilient Database Connection: Fallback to SQLite if PostgreSQL/Docker is not running
try:
    # Attempt to connect to PostgreSQL with a short 2-second timeout
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2} if "postgresql" in DATABASE_URL else {})
    with engine.connect() as conn:
        pass
    print("Database Connection: Successfully connected to PostgreSQL.")
except Exception:
    print("Database Connection: PostgreSQL not reachable. Falling back to local SQLite database.")
    DATABASE_URL = "sqlite:///./sre_local.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---

class AWSAccount(Base):
    __tablename__ = "aws_accounts"
    
    id = Column(String, primary_key=True, index=True)
    account_id = Column(String, unique=True, index=True, nullable=False)
    role_arn = Column(String, nullable=False)
    connection_status = Column(String, default="CONNECTED")
    created_at = Column(DateTime, default=datetime.utcnow)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(String, primary_key=True, index=True)
    service = Column(String, nullable=False)
    error_rate = Column(String, nullable=False)
    cpu = Column(String, nullable=False)
    deployment = Column(String, nullable=False)
    logs_json = Column(Text, nullable=False) # JSON-serialized list of logs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    report = relationship("Report", back_populates="incident", uselist=False)

class Report(Base):
    __tablename__ = "reports"
    
    incident_id = Column(String, ForeignKey("incidents.id"), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    service = Column(String, nullable=False)
    root_cause = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    evidence_json = Column(Text, nullable=False) # JSON-serialized list of evidence strings
    recommendation = Column(Text, nullable=False)
    
    incident = relationship("Incident", back_populates="report")

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

# --- Repository Layer ---

class AWSAccountRepository:
    @staticmethod
    def save_account(account_id: str, role_arn: str) -> str:
        db = SessionLocal()
        try:
            # Check if exists
            acc = db.query(AWSAccount).filter(AWSAccount.account_id == account_id).first()
            if acc:
                acc.role_arn = role_arn
                acc.connection_status = "CONNECTED"
                acc.created_at = datetime.utcnow()
                db.commit()
                return acc.id
            else:
                new_id = str(uuid.uuid4())
                acc = AWSAccount(id=new_id, account_id=account_id, role_arn=role_arn)
                db.add(acc)
                db.commit()
                return new_id
        finally:
            db.close()

    @staticmethod
    def get_account_by_id(account_id: str) -> Optional[AWSAccount]:
        db = SessionLocal()
        try:
            return db.query(AWSAccount).filter(AWSAccount.account_id == account_id).first()
        finally:
            db.close()

class IncidentRepository:
    @staticmethod
    def save_incident(payload: IncidentPayload) -> str:
        db = SessionLocal()
        try:
            incident_id = str(uuid.uuid4())
            new_incident = Incident(
                id=incident_id,
                service=payload.service,
                error_rate=payload.error_rate,
                cpu=payload.cpu,
                deployment=payload.deployment,
                logs_json=json.dumps(payload.logs),
                created_at=payload.timestamp or datetime.utcnow()
            )
            db.add(new_incident)
            db.commit()
            return incident_id
        finally:
            db.close()

    @staticmethod
    def get_incident(incident_id: str) -> Optional[IncidentPayload]:
        db = SessionLocal()
        try:
            inc = db.query(Incident).filter(Incident.id == incident_id).first()
            if not inc:
                return None
            return IncidentPayload(
                service=inc.service,
                error_rate=inc.error_rate,
                cpu=inc.cpu,
                deployment=inc.deployment,
                logs=json.loads(inc.logs_json),
                timestamp=inc.created_at
            )
        finally:
            db.close()

    @staticmethod
    def save_report(incident_id: str, report: SREAnalysisReport) -> None:
        db = SessionLocal()
        try:
            new_report = Report(
                incident_id=incident_id,
                timestamp=report.timestamp,
                service=report.service,
                root_cause=report.root_cause,
                confidence=report.confidence,
                evidence_json=json.dumps(report.evidence),
                recommendation=report.recommendation
            )
            db.add(new_report)
            db.commit()
        finally:
            db.close()

    @staticmethod
    def get_report(incident_id: str) -> Optional[SREAnalysisReport]:
        db = SessionLocal()
        try:
            rep = db.query(Report).filter(Report.incident_id == incident_id).first()
            if not rep:
                return None
            return SREAnalysisReport(
                incident_id=rep.incident_id,
                timestamp=rep.timestamp,
                service=rep.service,
                root_cause=rep.root_cause,
                confidence=rep.confidence,
                evidence=json.loads(rep.evidence_json),
                recommendation=rep.recommendation
            )
        finally:
            db.close()

    @staticmethod
    def list_reports() -> List[SREAnalysisReport]:
        db = SessionLocal()
        try:
            reps = db.query(Report).all()
            return [
                SREAnalysisReport(
                    incident_id=rep.incident_id,
                    timestamp=rep.timestamp,
                    service=rep.service,
                    root_cause=rep.root_cause,
                    confidence=rep.confidence,
                    evidence=json.loads(rep.evidence_json),
                    recommendation=rep.recommendation
                )
                for rep in reps
            ]
        finally:
            db.close()
