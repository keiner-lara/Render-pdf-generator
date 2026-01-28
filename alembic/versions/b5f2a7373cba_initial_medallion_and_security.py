"""initial medallion and security

Revision ID: 034fa4544ad9
Revises: 
Create Date: 2026-01-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '034fa4544ad9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. SCHEMATIC CREATION (Security Order)
    schemas = ['operational', 'audit', 'cleansed', 'artifacts', 'logs', 'auth']
    for schema in schemas:
        op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

    # 2. SUPABASE COMPATIBILITY PATCH (Mock auth.uid)
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$
            SELECT NULL::uuid;
        $$;
    """))

    # 3.ROLE CREATION (RBAC)
    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_staff_user') THEN CREATE ROLE role_staff_user; END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_orchestrator') THEN CREATE ROLE role_orchestrator; END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_ingestion_service') THEN CREATE ROLE role_ingestion_service; END IF;
        EXCEPTION WHEN OTHERS THEN RAISE NOTICE 'Roles ya existen'; END $$;
    """))

    # 4. IDENTITY AND BUSINESS TABLES (Silver Layer)
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        schema='operational'
    )

    op.create_table(
        'user_credentials',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['operational.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
        schema='operational'
    )

    op.create_table(
        'cases',
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('case_id'),
        schema='operational'
    )

    op.create_table(
        'subjects',
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('app_subject_id', sa.String(length=200), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(length=50), nullable=True),
        sa.Column('city', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('subject_id'),
        sa.UniqueConstraint('app_subject_id'),
        sa.UniqueConstraint('email'),
        schema='operational'
    )

    op.create_table(
        'sessions',
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('app_session_id', sa.String(length=200), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='created'),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['operational.cases.case_id']),
        sa.ForeignKeyConstraint(['created_by'], ['operational.users.id']),
        sa.PrimaryKeyConstraint('session_id'),
        sa.UniqueConstraint('app_session_id'),
        schema='operational'
    )

    op.create_table(
        'session_subjects',
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('role_in_session', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['operational.sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['operational.subjects.subject_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id', 'subject_id'),
        schema='operational'
    )

    # 5. BRONZE LAYER (AUDIT STAGING)
    op.create_table(
        'ingestion_staging',
        sa.Column('staging_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('source_cell', sa.String(length=50), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_validated', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['session_id'], ['operational.sessions.session_id']),
        sa.PrimaryKeyConstraint('staging_id'),
        schema='audit'
    )

    # 6. CAPA SILVER (CLEANSED UNIFIED)
    op.create_table(
        'biometric_events',
        sa.Column('event_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('processed_payload', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('t_start_ms', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['operational.sessions.session_id']),
        sa.ForeignKeyConstraint(['subject_id'], ['operational.subjects.subject_id']),
        sa.PrimaryKeyConstraint('event_id'),
        schema='cleansed'
    )

    # 7.CAPA GOLD (REPORTS & ARTIFACTS)
    op.create_table(
        'reports',
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=True),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('model_version', sa.String(length=100)),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['operational.sessions.session_id']),
        sa.ForeignKeyConstraint(['subject_id'], ['operational.subjects.subject_id']),
        sa.PrimaryKeyConstraint('report_id'),
        schema='artifacts'
    )

    op.create_table(
        'pdf_artifacts',
        sa.Column('artifact_id', sa.UUID(), nullable=False),
        sa.Column('report_id', sa.UUID(), nullable=False),
        sa.Column('blob_path', sa.Text(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['artifacts.reports.report_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('artifact_id'),
        sa.UniqueConstraint('sha256_hash'),
        schema='artifacts'
    )

    # 8.RLS SECURITY (Applied directly)
    op.execute(sa.text("ALTER TABLE operational.subjects ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("ALTER TABLE operational.sessions ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY staff_access ON operational.subjects FOR ALL
        USING (auth.uid() IN (SELECT id FROM operational.users WHERE role IN ('admin', 'analyst')) OR current_user = 'postgres');
    """))

def downgrade() -> None:
    # Rollback en cascada
    op.execute(sa.text("DROP SCHEMA IF EXISTS auth CASCADE"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS artifacts CASCADE"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS cleansed CASCADE"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS audit CASCADE"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS operational CASCADE"))