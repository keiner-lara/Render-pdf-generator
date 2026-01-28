--  admins and analysts can manage identity and sessions
-- 0. audit automation function (idempotent)
-- ----------------------------------------------------------
create or replace function public.fn_update_timestamp()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- 1. users table
-- ----------------------------------------------------------
create table if not exists operational.users (
    id uuid primary key default gen_random_uuid(),
    email varchar(255) unique not null,
    name varchar(255) not null,
    city varchar(255),
    role operational.user_role not null,
    auth_provider varchar(50) default 'local',
    last_login_at timestamptz,
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- update trigger for users
drop trigger if exists trg_update_users_timestamp on operational.users;
create trigger trg_update_users_timestamp
before update on operational.users
for each row execute function public.fn_update_timestamp();

-- 2. user credentials (local security)
-- ----------------------------------------------------------
create table if not exists operational.user_credentials (
    user_id uuid primary key references operational.users(id) on delete cascade,
    password_hash text not null,
    last_login timestamptz,
    updated_at timestamptz default now()
);

-- update trigger for credentials
drop trigger if exists trg_update_credentials_timestamp on operational.user_credentials;
create trigger trg_update_credentials_timestamp
before update on operational.user_credentials
for each row execute function public.fn_update_timestamp();

-- 3. user oauth accounts (identidades externas google/github/etc)
-- ----------------------------------------------------------
create table if not exists operational.user_oauth_accounts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references operational.users(id) on delete cascade,
    provider varchar(50) not null check (provider in ('google', 'github', 'azure', 'local')),
    provider_user_id varchar(255) not null,
    email varchar(255),
    email_verified boolean default false,
    access_token text,
    refresh_token text,
    token_expires_at timestamptz,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    constraint unq_provider_user unique (provider, provider_user_id)
);

-- OAuth update trigger
drop trigger if exists trg_update_oauth_timestamp on operational.user_oauth_accounts;
create trigger trg_update_oauth_timestamp
before update on operational.user_oauth_accounts
for each row execute function public.fn_update_timestamp();

-- 4. subjects 
-- ----------------------------------------------------------
create table if not exists operational.subjects (
    subject_id uuid primary key default gen_random_uuid(),
    app_subject_id text not null unique, 
    name text not null,
    email text unique not null,
    age integer,
    gender text,
    city text not null,
    created_at timestamptz default now(),
    updated_at timestamptz default now() -- added for consistency
);

-- Update trigger for subjects
drop trigger if exists trg_update_subjects_timestamp on operational.subjects;
create trigger trg_update_subjects_timestamp
before update on operational.subjects
for each row execute function public.fn_update_timestamp();

-- 5. sessions (instancias de la cámara gessel)
-- ----------------------------------------------------------
create table if not exists operational.sessions (
    session_id uuid primary key default gen_random_uuid(),
    app_session_id text not null unique,
    case_id text not null, -- key to the case cell database
    status operational.session_status default 'created',
    created_by uuid references operational.users(id), 
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
-- update trigger for sessions
drop trigger if exists trg_update_sessions_timestamp on operational.sessions;
create trigger trg_update_sessions_timestamp
before update on operational.sessions
for each row execute function public.fn_update_timestamp();
-- 6. session_subjects (dynamic participant-role-session mapping)
-- ----------------------------------------------------------
create table if not exists operational.session_subjects (
    session_id uuid references operational.sessions(session_id) on delete cascade,
    subject_id uuid references operational.subjects(subject_id) on delete cascade,
    role_in_session text not null, -- 'pm', 'dev', 'qa', 'observer'
    primary key (session_id, subject_id)
);

-- 7. additional performance indicators
-- ----------------------------------------------------------
create index if not exists idx_oauth_user_provider on operational.user_oauth_accounts(user_id, provider);
create index if not exists idx_subjects_app_id on operational.subjects(app_subject_id);