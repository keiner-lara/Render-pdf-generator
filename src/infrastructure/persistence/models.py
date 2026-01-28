from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, LargeBinary, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()
# 1. SCHEMA: OPERATIONAL 
class User(Base):
    __tablename__ = 'users'
    __table_args__ = {"schema": "operational"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    city = Column(String(255))
    role = Column(String(50), nullable=False) 
    auth_provider = Column(String(50), default='local')
    last_login_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserCredentials(Base):
    __tablename__ = 'user_credentials'
    __table_args__ = {"schema": "operational"}
    user_id = Column(UUID(as_uuid=True), ForeignKey('operational.users.id', ondelete='CASCADE'), primary_key=True)
    password_hash = Column(Text, nullable=False)
    last_login = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserOAuthAccount(Base):
    __tablename__ = 'user_oauth_accounts'
    __table_args__ = {"schema": "operational"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('operational.users.id', ondelete='CASCADE'), nullable=False)
    provider = Column(String(50), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    email = Column(String(255))
    email_verified = Column(Boolean, default=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Case(Base):
    __tablename__ = 'cases'
    __table_args__ = {"schema": "operational"}
    case_id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)

class Subject(Base):
    __tablename__ = 'subjects'
    __table_args__ = {"schema": "operational"}
    subject_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_subject_id = Column(String(200), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    age = Column(Integer)
    gender = Column(String(50))
    city = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Session(Base):
    __tablename__ = 'sessions'
    __table_args__ = {"schema": "operational"}
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_session_id = Column(String(200), unique=True, nullable=False)
    case_id = Column(String(100), ForeignKey('operational.cases.case_id'), nullable=False)
    status = Column(String(50), default='created')
    created_by = Column(UUID(as_uuid=True), ForeignKey('operational.users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SessionSubject(Base):
    __tablename__ = 'session_subjects'
    __table_args__ = {"schema": "operational"}
    session_id = Column(UUID(as_uuid=True), ForeignKey('operational.sessions.session_id', ondelete='CASCADE'), primary_key=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('operational.subjects.subject_id', ondelete='CASCADE'), primary_key=True)
    role_in_session = Column(String(255), nullable=False)

# 2. SCHEMA: AUDIT
class IngestionStaging(Base):
    __tablename__ = 'ingestion_staging'
    __table_args__ = {"schema": "audit"}
    staging_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('operational.sessions.session_id'))
    source_cell = Column(String(50), nullable=False)
    raw_payload = Column(JSONB, nullable=False)
    is_validated = Column(Boolean, default=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
# 3. SCHEMA: CLEANSED (Unified JSONB Layer)
class BiometricEvent(Base):
    __tablename__ = 'biometric_events'
    __table_args__ = {"schema": "cleansed"}
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('operational.sessions.session_id'))
    subject_id = Column(UUID(as_uuid=True), ForeignKey('operational.subjects.subject_id'))
    source_type = Column(String(50), nullable=False) 
    processed_payload = Column(JSONB)
    t_start_ms = Column(BigInteger, nullable=False)

# 4. SCHEMA: STORAGE & LOGS (Outputs)
class Report(Base):
    __tablename__ = 'reports'
    __table_args__ = {"schema": "artifacts"}
    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('operational.sessions.session_id'), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('operational.subjects.subject_id'), nullable=True)
    kind = Column(String(50), nullable=False) 
    content_markdown = Column(Text, nullable=False)
    content_json = Column(JSONB)
    model_version = Column(String(100))
    prompt_hash = Column(String(64))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

class PDFArtifact(Base):
    __tablename__ = 'pdf_artifacts'
    __table_args__ = {"schema": "artifacts"}
    artifact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey('artifacts.reports.report_id'))
    blob_path = Column(Text, nullable=False)
    sha256_hash = Column(String(64), unique=True, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

class LlmRun(Base):
    __tablename__ = 'llm_runs'
    __table_args__ = {"schema": "logs"}
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('operational.sessions.session_id'))
    model = Column(String(100), nullable=False)
    total_tokens = Column(Integer)
    latency_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())