-- Action table for automated opportunity tasks
CREATE TABLE IF NOT EXISTS action (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  opportunity_id        uuid NOT NULL REFERENCES opportunity(id) ON DELETE CASCADE,
  
  -- Action type and configuration
  action_type           varchar(50) NOT NULL,
  status                varchar(20) NOT NULL DEFAULT 'active',
  
  -- Scheduling
  schedule_type         varchar(20) NOT NULL,
  schedule_config       jsonb,
  
  -- Action-specific configuration
  config                jsonb,
  
  -- Execution tracking
  last_executed_at      timestamptz,
  next_execution_at     timestamptz,
  execution_count       integer NOT NULL DEFAULT 0,
  max_executions        integer,
  
  -- Metadata
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  created_by            uuid REFERENCES auth.users(id),
  
  CONSTRAINT valid_action_type CHECK (action_type IN ('recurring_quote', 'recurring_invoice', 'follow_up_email', 'stage_reminder')),
  CONSTRAINT valid_status CHECK (status IN ('active', 'paused', 'completed', 'failed', 'cancelled')),
  CONSTRAINT valid_schedule_type CHECK (schedule_type IN ('monthly', 'weekly', 'daily', 'one_time', 'custom_cron'))
);

CREATE INDEX IF NOT EXISTS idx_action_user_id ON action(user_id);
CREATE INDEX IF NOT EXISTS idx_action_opportunity_id ON action(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_action_next_execution ON action(next_execution_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_action_type ON action(action_type);

-- Action execution log table
CREATE TABLE IF NOT EXISTS action_execution_log (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  action_id             uuid NOT NULL REFERENCES action(id) ON DELETE CASCADE,
  
  -- Execution details
  executed_at           timestamptz NOT NULL DEFAULT now(),
  status                varchar(20) NOT NULL,
  
  -- Results
  result_data           jsonb,
  error_message         text,
  
  -- Metadata
  duration_ms           integer,
  
  CONSTRAINT valid_execution_status CHECK (status IN ('success', 'failed', 'skipped'))
);

CREATE INDEX IF NOT EXISTS idx_action_execution_log_action_id ON action_execution_log(action_id);
CREATE INDEX IF NOT EXISTS idx_action_execution_log_executed_at ON action_execution_log(executed_at);
