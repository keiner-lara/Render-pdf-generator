
-- ----------------------------------------------------------
\set on_error_stop on

create schema if not exists auth;

create or replace function auth.uid() 
returns uuid 
language sql 
stable
as $$
    -- simulation: locally returns null to activate the default rls lock
    select null::uuid;
$$;

-- 1.service role creation (rbac)
-- ----------------------------------------------------------
do $$ begin
    if not exists (select from pg_roles where rolname = 'role_staff_user') then 
        create role role_staff_user; -- admin y analysts
    end if;
    if not exists (select from pg_roles where rolname = 'role_orchestrator') then 
        create role role_orchestrator; -- motor python (auditor/ia)
    end if;
    if not exists (select from pg_roles where rolname = 'role_ingestion_service') then 
        create role role_ingestion_service; -- cámaras y micrófonos
    end if;
exception when others then raise notice 'roles ya configurados.'; end $$;

-- 2. permission management (grants)
-- ----------------------------------------------------------

-- a. cleaning: nobody uses the public scheme
revoke all on schema public from public;

-- b. staff permits (operational management)
grant usage on schema operational, artifacts to role_staff_user;
--The staff can do full CRUD in the planning phase
grant select, insert, update, delete on all tables in schema operational to role_staff_user;
grant usage, select on all sequences in schema operational to role_staff_user;
-- Staff can only read the final reports
grant select on all tables in schema artifacts to role_staff_user;

-- c. permissions for the orchestrator (the system engine)
grant usage on schema audit, operational, cleansed, artifacts, logs to role_orchestrator;
grant all privileges on all tables in schema audit, operational, cleansed, artifacts, logs to role_orchestrator;
grant all privileges on all sequences in schema audit, operational, cleansed, artifacts, logs to role_orchestrator;

-- d. intake permits (technical entry)
grant usage on schema audit to role_ingestion_service;
grant insert on audit.ingestion_staging to role_ingestion_service;

-- 5. high-performance indices
-- ----------------------------------------------------------
do $$ begin
    -- session search
    if not exists (select 1 from pg_class where relname = 'idx_sessions_status') then
        create index idx_sessions_status on operational.sessions (status);
    end if;

    -- subject search
    if not exists (select 1 from pg_class where relname = 'idx_subjects_app_id') then
        create index idx_subjects_app_id on operational.subjects (app_subject_id);
    end if;

    -- search n+1 (session participants)
    if not exists (select 1 from pg_class where relname = 'idx_ss_session_lookup') then
        create index idx_ss_session_lookup on operational.session_subjects (session_id);
    end if;

    -- chronological search in Silver (timeline for AI)
    if not exists (select 1 from pg_class where relname = 'idx_silver_chronology') then
        create index idx_silver_chronology on cleansed.biometric_events (session_id, t_start_ms);
    end if;

    -- gin search for deep jsonb analysis
    if not exists (select 1 from pg_class where relname = 'idx_cleansed_json_search') then
        create index idx_cleansed_json_search on cleansed.biometric_events using gin (processed_payload);
    end if;
end $$;

-- 6. row-level security (rls)
-- ----------------------------------------------------------

-- Activate protection on key tables
alter table operational.subjects enable row level security;
alter table operational.sessions enable row level security;
alter table operational.session_subjects enable row level security;
alter table artifacts.reports enable row level security;

-- Teacher policy: Only staff with admin/analyst roles can view/edit
drop policy if exists "staff_management_policy" on operational.subjects;
create policy "staff_management_policy"
on operational.subjects for all
using (
  auth.uid() in (select id from operational.users where role in ('admin', 'analyst'))
  or current_user = 'postgres'
);

drop policy if exists "staff_session_policy" on operational.sessions;
create policy "staff_session_policy"
on operational.sessions for all
using (
  auth.uid() in (select id from operational.users where role in ('admin', 'analyst'))
  or current_user = 'postgres'
);

drop policy if exists "staff_report_policy" on artifacts.reports;
create policy "staff_report_policy"
on artifacts.reports for select
using (
  auth.uid() in (select id from operational.users where role in ('admin', 'analyst'))
  or current_user = 'postgres'
);

-- 7. audit security (logs)
-- ----------------------------------------------------------
grant usage on schema logs to role_staff_user;
grant select on all tables in schema logs to role_staff_user;
revoke delete, truncate on all tables in schema logs from role_staff_user;

-- 8. default privileges
-- ----------------------------------------------------------
alter default privileges in schema artifacts grant select on tables to role_staff_user;
alter default privileges in schema operational, cleansed, artifacts, logs grant all privileges on tables to role_orchestrator;