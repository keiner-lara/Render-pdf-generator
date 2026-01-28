
-----------------------------------base infrastructure and typing--------------
-- pgcrypto It is vital to validate the integrity of the jsonb (digest)
create extension if not exists "pgcrypto";
-- 2. creation of schemes (simplified architecture)
create schema if not exists operational; --users, subjects and sessions (app)
create schema if not exists raw_vision; --gross landing video
create schema if not exists raw_voice; -- gross audio landing
create schema if not exists audit; -- waiting room and quality verdict
create schema if not exists cleansed; -- the "main table" with clean data
create schema if not exists artifacts;  -- persistence of json and pdf reports
create schema if not exists logs; -- process traceability and AI

-- 3. definition of custom types (enums)
do $$ begin
    -- user roles for the app
    if not exists (select 1 from pg_type where typname = 'user_role') then
        create type operational.user_role as enum (
            'admin', 
            'scientist', 
            'analyst'
        );
    end if;
    --processing flow states
    if not exists (select 1 from pg_type where typname = 'session_status') then
        create type operational.session_status as enum (
            'created',           -- admin or analyst creates the session
            'ingesting',         -- receiving telemetry
            'ready_for_audit',   -- Data ready in staging for review
            'cleansed',          -- Data approved and moved to the main table
            'analyzed',          -- report successfully generated
            'error'              -- audit or processing failure
        );
    end if;

    -- distinction of n+1 reports
    if not exists (select 1 from pg_type where typname = 'report_kind') then
        create type operational.report_kind as enum (
            'individual', 
            'group'
        );
    end if;
end $$;
