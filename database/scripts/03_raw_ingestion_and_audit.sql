
--------landing area for raw jsonb data before validation-----------------------
-- 1. ingestion staging (the "waiting room" for the auditor)
-- vision and voice cells push data here first
create table if not exists audit.ingestion_staging (
    staging_id uuid primary key default gen_random_uuid(),
    session_id uuid not null references operational.sessions(session_id),
    source_cell text not null check (source_cell in ('vision', 'voice')),
    raw_payload jsonb not null, -- full technical json landed here
    digest text not null, -- sha-256 hash to prevent duplicate ingestion
    is_validated boolean default false,
    audit_notes text, -- technical notes from the auditor script
    received_at timestamptz default now()
);
-- 2. raw_vision receptions (structured bronze for vision)
-- partitioned by time for high-scale performance
create table if not exists raw_vision.receptions (
    id bigserial,
    session_id uuid not null references operational.sessions(session_id),
    subject_id uuid references operational.subjects(subject_id),
    payload jsonb not null, -- validated technical json
    digest text not null,
    received_at timestamptz not null default now(),
    primary key (id, received_at),
    constraint unq_vision_ingest unique (session_id, digest, received_at)
) partition by range (received_at);
-- 3. raw_voice receptions (structured bronze for voice)
-- partitioned by time for high-scale performance
create table if not exists raw_voice.receptions (
    id bigserial,
    session_id uuid not null references operational.sessions(session_id),
    subject_id uuid references operational.subjects(subject_id),
    payload jsonb not null, -- validated technical json
    digest text not null,
    received_at timestamptz not null default now(),
    primary key (id, received_at),
    constraint unq_voice_ingest unique (session_id, digest, received_at)
) partition by range (received_at);
-- 4. audit logs (tracks the auditor's actions)
create table if not exists audit.quality_checks (
    check_id uuid primary key default gen_random_uuid(),
    session_id uuid not null references operational.sessions(session_id),
    is_validated boolean default false,
    coverage_score numeric(3,2), -- percentage of time covered (0.00 to 1.00)
    audit_message text,          -- "missing vision data in segment x"
    audited_at timestamptz default now()
);
