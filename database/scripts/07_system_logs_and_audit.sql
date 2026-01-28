
------------track ai costs, system errors, and data movement
-- 1. llm_runs: tracks every interaction with openai
create table if not exists logs.llm_runs (
    run_id uuid primary key default gen_random_uuid(),
    session_id uuid not null references operational.sessions(session_id),
    subject_id uuid references operational.subjects(subject_id), -- null for group reports
    model_used text not null,       -- e.g., 'gpt-4o'
    prompt_tokens integer,          -- for cost analysis
    completion_tokens integer,      -- for cost analysis
    total_tokens integer,
    
    latency_ms integer,             -- how long openai took
    status text not null,           -- 'success', 'failed'
    error_message text,             -- details if it failed
    
    created_at timestamptz default now()
);
-- 2. execution_audit: tracks internal data movement (audit -> raw -> cleansed)
create table if not exists logs.execution_audit (
    audit_id uuid primary key default gen_random_uuid(),
    session_id uuid not null references operational.sessions(session_id),
    step_name text not null,        -- 'data_validation', 'refinery_promotion'
    result_status text not null,    -- 'ok', 'warning', 'error'
    metadata jsonb,                 -- record counts or technical details
    
    executed_at timestamptz default now()
);

-- 3. performance indices for logs
create index if not exists idx_logs_session_id on logs.llm_runs (session_id);
create index if not exists idx_audit_session_id on logs.execution_audit (session_id);

-- 4. grant permissions to the orchestrator
grant usage on schema logs to role_orchestrator;
grant all privileges on all tables in schema logs to role_orchestrator;