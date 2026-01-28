create table if not exists artifacts.reports (
    report_id uuid primary key default gen_random_uuid(),
    session_id uuid not null references operational.sessions(session_id),
    subject_id uuid references operational.subjects(subject_id), -- null si es reporte grupal
    
    kind operational.report_kind not null, -- 'individual' o 'group'
    content_markdown text not null,      
    content_json jsonb not null,        
    model_version text,                  
    prompt_hash text,                   
    generated_at timestamptz default now(),
    
    constraint unq_report_per_subject unique (session_id, subject_id, kind)
);

create table if not exists artifacts.pdf_artifacts (
    artifact_id uuid primary key default gen_random_uuid(),
    report_id uuid not null references artifacts.reports(report_id) on delete cascade,
    blob_path text not null,       
    sha256_hash text not null,     
    generated_at timestamptz default now(),
    constraint unq_pdf_hash unique (sha256_hash)
);

-- Índices para búsqueda rápida desde el Backend
create index if not exists idx_reports_json on artifacts.reports using gin (content_json);
create index if not exists idx_reports_session on artifacts.reports (session_id);