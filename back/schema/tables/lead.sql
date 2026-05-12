-- LEADS
create table if not exists public.lead (
  id uuid primary key default gen_random_uuid(),

  -- info prospect (pas besoin d'account/contact au départ)
  full_name text,
  email text,
  phone text,
  company_name text,

  -- qualification
  status text not null default 'NEW'
    check (status in ('NEW','CONTACTED','QUALIFIED','DISQUALIFIED','CONVERTED')),
  owner_user_id uuid references auth.users(id) on delete set null,
  -- tracking (même en interne ça aide)
  source text,         -- inbound/outbound/referral...
  notes text,

  -- conversion links
  converted_account_id uuid references public.account(id) on delete set null,
  converted_contact_id uuid references public.contact(id) on delete set null,
  converted_opportunity_id uuid references public.opportunity(id) on delete set null,
  converted_at timestamptz,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_lead_status on public.lead(status);
create index if not exists idx_lead_email on public.lead(email);
