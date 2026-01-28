---------------------unified jsonb repository for ai processing------------------
create table if not exists cleansed.biometric_events (
    event_id uuid primary key default gen_random_uuid(),
    session_id uuid not null references operational.sessions(session_id),
    subject_id uuid references operational.subjects(subject_id),
    -- discriminator to identify the data origin
    source_type text not null check (source_type in ('vision', 'voice')),
    -- technical data unified in a single jsonb column
    -- this stores the refined, duplicate-free payload
    processed_payload jsonb not null, 
    -- timestamp for chronological sorting
    t_start_ms bigint not null,
    cleansed_at timestamptz default now()
);
