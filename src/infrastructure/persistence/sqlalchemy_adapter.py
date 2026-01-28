import uuid
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Puertos
from src.domain.ports import RepositoryPort

# Modelos
from src.infrastructure.persistence.models import (
    User, Session, Subject, SessionSubject, 
    IngestionStaging, BiometricEvent, 
    Report, PDFArtifact, LlmRun
)

class SQLAlchemyAdapter(RepositoryPort):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    # --- 1. OPERATIONAL (Users, Sessions, Subjects) ---
    
    def create_or_update_user(self, email: str, name: str, role: str, city: Optional[str] = None) -> User:
        db = self.SessionLocal()
        try:
            user = db.query(User).filter_by(email=email).first()
            if user:
                user.name = name
                user.role = role
                user.city = city
                user.updated_at = datetime.now()
            else:
                user = User(email=email, name=name, role=role, city=city)
                db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def create_or_update_session(self, app_session_id: str, case_id: str, status: str = 'created', created_by: Optional[uuid.UUID] = None) -> Session:
        db = self.SessionLocal()
        try:
            session = db.query(Session).filter_by(app_session_id=app_session_id).first()
            if session:
                session.case_id = case_id
                session.status = status
                session.updated_at = datetime.now()
            else:
                session = Session(app_session_id=app_session_id, case_id=case_id, status=status, created_by=created_by)
                db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()

    def get_session_by_app_id(self, app_session_id: str) -> Optional[Session]:
        db = self.SessionLocal()
        try:
            return db.query(Session).filter(Session.app_session_id == app_session_id).first()
        finally:
            db.close()

    def update_session_status(self, session_id: uuid.UUID, new_status: str):
        db = self.SessionLocal()
        try:
            session = db.query(Session).filter_by(session_id=session_id).first()
            if session:
                session.status = new_status
                db.commit()
        finally:
            db.close()

    def get_subject_by_app_id(self, app_subject_id: str) -> Optional[Subject]:
        db = self.SessionLocal()
        try:
            return db.query(Subject).filter(Subject.app_subject_id == app_subject_id).first()
        finally:
            db.close()

    def get_participants_with_roles(self, session_id: uuid.UUID) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            query = db.query(
                Subject.subject_id, Subject.app_subject_id, Subject.name,
                Subject.age, Subject.gender, Subject.city,
                SessionSubject.role_in_session
            ).join(
                SessionSubject, Subject.subject_id == SessionSubject.subject_id
            ).filter(SessionSubject.session_id == session_id)
            results = query.all()
            return [{"subject_id": r.subject_id, "app_id": r.app_subject_id, "name": r.name, "age": r.age, "gender": r.gender, "city": r.city, "role": r.role_in_session} for r in results]
        finally:
            db.close()

    # --- 2. AUDIT (Capa Bronze) ---

    def save_staging_data(self, session_id: uuid.UUID, source: str, payload: Dict[str, Any]):
        db = self.SessionLocal()
        try:
            new_entry = IngestionStaging(session_id=session_id, source_cell=source, raw_payload=payload, is_validated=False)
            db.add(new_entry)
            db.commit()
        finally:
            db.close()

    def get_pending_audit(self, session_id: uuid.UUID):
        """MÉTODO FALTANTE CORREGIDO: Retorna datos de staging para la refinería"""
        db = self.SessionLocal()
        try:
            return db.query(IngestionStaging).filter_by(session_id=session_id, is_validated=False).all()
        finally:
            db.close()

    # --- 3. CLEANSED (Capa Silver) ---

    def save_cleansed_event(self, session_id, subject_id, source_type, payload, t_start):
        db = self.SessionLocal()
        try:
            silver_record = BiometricEvent(
                session_id=session_id,
                subject_id=subject_id,
                source_type=source_type,
                processed_payload=payload,
                t_start_ms=t_start
            )
            db.add(silver_record)
            db.commit()
        finally:
            db.close()

    def get_cleansed_events(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            query = db.query(BiometricEvent).filter(BiometricEvent.session_id == session_id)
            if subject_id:
                query = query.filter(BiometricEvent.subject_id == subject_id)
            events = query.order_by(BiometricEvent.t_start_ms.asc()).all()
            return [{"source": e.source_type, "t_start": e.t_start_ms, "data": e.processed_payload} for e in events]
        finally:
            db.close()

    # --- 4. ARTIFACTS & CACHE (Capa Gold) ---

    def get_report_by_hash(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID], kind: str, data_hash: str) -> Optional[Report]:
        db = self.SessionLocal()
        try:
            return db.query(Report).filter_by(session_id=session_id, subject_id=subject_id, kind=kind, prompt_hash=data_hash).first()
        finally:
            db.close()

    def save_report_meta(self, session_id: uuid.UUID, subject_id: Optional[uuid.UUID], kind: str, markdown: str, json_data: Dict[str, Any], prompt_hash: str) -> uuid.UUID:
        db = self.SessionLocal()
        try:
            existing = db.query(Report).filter_by(session_id=session_id, subject_id=subject_id, kind=kind).first()
            if existing:
                existing.content_markdown = markdown
                existing.content_json = json_data
                existing.prompt_hash = prompt_hash
                existing.generated_at = datetime.now()
                db.commit()
                return existing.report_id
            else:
                new_report = Report(session_id=session_id, subject_id=subject_id, kind=kind, content_markdown=markdown, content_json=json_data, prompt_hash=prompt_hash)
                db.add(new_report)
                db.commit()
                db.refresh(new_report)
                return new_report.report_id
        finally:
            db.close()

    def save_pdf_artifact(self, report_id: uuid.UUID, blob_path: str):
        db = self.SessionLocal()
        try:
            file_hash = hashlib.sha256(blob_path.encode()).hexdigest()
            artifact = PDFArtifact(report_id=report_id, blob_path=blob_path, sha256_hash=file_hash)
            db.add(artifact)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()