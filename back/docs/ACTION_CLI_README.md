# Action CLI - Query and Manage Automated Actions

A command-line interface for managing automated actions associated with opportunities. Actions can be configured to run on various schedules (daily, weekly, monthly) and perform tasks like generating quotes, invoices, and sending follow-up emails.

## Overview

The Action CLI provides a complete interface to:

- **List** all actions for a given opportunity
- **Create** new actions with flexible scheduling
- **View** detailed information about actions
- **Control** actions (pause, resume, delete)
- **Execute** actions manually
- **Track** execution history and logs

## Installation

The CLI requires the backend environment to be properly configured:

```bash
cd back
source venv/bin/activate
```

## Usage

### List Actions for an Opportunity

Query all actions associated with a specific opportunity:

```bash
python -m src.command.action_cli list-actions <opportunity_id>
```

**Example:**

```bash
python -m src.command.action_cli list-actions c32c94d9-66ea-427b-8ba0-4946191f4c31
```

**Output:**

```
====================================================================================================
Actions for opportunity: c32c94d9-66ea-427b-8ba0-4946191f4c31
====================================================================================================

1. Action ID: a55c080f-fba7-4568-812e-1b74fadcbb14
   Type: recurring_quote
   Status: active
   Schedule: monthly
   Next execution: 2026-03-01T09:00:00+00:00
   Executions: 0/None
   Created: 2026-02-04T13:07:14.850925+00:00
   Config: {
      "days_valid": 30,
      "template_id": "default"
   }
```

### Create an Action

Create a new action with a specified schedule:

```bash
python -m src.command.action_cli create-action \
  <opportunity_id> \
  <user_id> \
  <action_type> \
  <schedule_type> \
  [schedule_config_json] \
  [config_json] \
  [max_executions]
```

#### Action Types

- `recurring_quote` - Generate recurring quotes
- `recurring_invoice` - Generate recurring invoices
- `follow_up_email` - Send follow-up emails
- `stage_reminder` - Send stage-based reminders

#### Schedule Types

**Monthly:**

```bash
python -m src.command.action_cli create-action \
  c32c94d9-66ea-427b-8ba0-4946191f4c31 \
  393be11f-807f-4f0d-bfbe-5aa93f409b48 \
  recurring_quote \
  monthly \
  '{"day_of_month": 1, "time": "09:00", "timezone": "UTC"}' \
  '{"template_id": "default", "days_valid": 30}'
```

**Weekly:**

```bash
python -m src.command.action_cli create-action \
  c32c94d9-66ea-427b-8ba0-4946191f4c31 \
  393be11f-807f-4f0d-bfbe-5aa93f409b48 \
  follow_up_email \
  weekly \
  '{"day_of_week": 2, "time": "10:00", "timezone": "UTC"}' \
  '{"subject": "Follow up", "email_template_id": "follow_up_001"}' \
  12
```

**Daily:**

```bash
python -m src.command.action_cli create-action \
  c32c94d9-66ea-427b-8ba0-4946191f4c31 \
  393be11f-807f-4f0d-bfbe-5aa93f409b48 \
  recurring_invoice \
  daily \
  '{"time": "08:00", "timezone": "UTC"}' \
  '{"invoice_type": "standard"}'
```

**One-time:**

```bash
python -m src.command.action_cli create-action \
  c32c94d9-66ea-427b-8ba0-4946191f4c31 \
  393be11f-807f-4f0d-bfbe-5aa93f409b48 \
  follow_up_email \
  one_time \
  '{}' \
  '{"subject": "Final reminder"}'
```

### Get Action Details

View comprehensive information about a specific action:

```bash
python -m src.command.action_cli get-action <action_id>
```

**Example:**

```bash
python -m src.command.action_cli get-action a55c080f-fba7-4568-812e-1b74fadcbb14
```

**Output:**

```
====================================================================================================
Action Details: a55c080f-fba7-4568-812e-1b74fadcbb14
====================================================================================================

Type: recurring_quote
Status: active
Opportunity: c32c94d9-66ea-427b-8ba0-4946191f4c31
User: 393be11f-807f-4f0d-bfbe-5aa93f409b48
Schedule Type: monthly
Schedule Config: {
  "time": "09:00",
  "timezone": "UTC",
  "day_of_month": 1
}
Config: {
  "days_valid": 30,
  "template_id": "default"
}
Last executed: None
Next execution: 2026-03-01T09:00:00+00:00
Execution count: 0
Max executions: None
Created: 2026-02-04T13:07:14.850925+00:00
Updated: 2026-02-04T13:07:14.850925+00:00
```

### Pause an Action

Temporarily disable an action without deleting it:

```bash
python -m src.command.action_cli pause-action <action_id>
```

### Resume an Action

Re-enable a paused action:

```bash
python -m src.command.action_cli resume-action <action_id>
```

### Delete an Action

Permanently remove an action:

```bash
python -m src.command.action_cli delete-action <action_id>
```

### Manually Execute an Action

Trigger an action to execute immediately outside its normal schedule:

```bash
python -m src.command.action_cli execute-action <action_id>
```

**Output:**

```
====================================================================================================
Action Execution Result
====================================================================================================

Action ID: a55c080f-fba7-4568-812e-1b74fadcbb14
Status: success
Duration: 234ms
Result: {
  "quote_id": "Q-2026-001",
  "customer": "Acme Inc"
}
```

### View Execution Logs

Retrieve the execution history for an action:

```bash
python -m src.command.action_cli get-logs <action_id> [limit]
```

**Example:**

```bash
python -m src.command.action_cli get-logs a55c080f-fba7-4568-812e-1b74fadcbb14 10
```

## Test Files

### Basic Test

Run a simple test to list actions for a specific opportunity:

```bash
python test_action_cli.py
```

### Comprehensive Test Suite

Run all CLI operations with example data:

```bash
python test_action_cli_comprehensive.py
```

This test creates multiple actions, retrieves details, pauses/resumes, and demonstrates all CLI features.

## Configuration

The CLI uses the same environment configuration as the backend. Ensure you have `.env` configured with:

```
SUPABASE_URL=...
SUPABASE_KEY=...
```

## Schedule Configuration Details

### Monthly Schedule

```json
{
  "day_of_month": 1, // Day of month (1-31, or "last" for last day)
  "time": "09:00", // Time in HH:MM format (UTC)
  "timezone": "UTC" // Timezone identifier
}
```

### Weekly Schedule

```json
{
  "day_of_week": 2, // Day number (0=Sunday, 1=Monday, ..., 6=Saturday)
  "time": "10:00", // Time in HH:MM format
  "timezone": "UTC"
}
```

### Daily Schedule

```json
{
  "time": "08:00", // Time in HH:MM format
  "timezone": "UTC"
}
```

### One-time Schedule

```json
{} // Executes immediately or at specified next_execution_at
```

## Action Configuration Examples

### Recurring Quote

```json
{
  "template_id": "default",
  "days_valid": 30,
  "auto_send": false
}
```

### Recurring Invoice

```json
{
  "invoice_type": "standard",
  "payment_terms": "NET_30"
}
```

### Follow-up Email

```json
{
  "subject": "Follow up on your inquiry",
  "email_template_id": "follow_up_001",
  "include_attachment": true
}
```

### Stage Reminder

```json
{
  "message": "Time to move this opportunity forward",
  "reminder_type": "internal"
}
```

## Status Values

- `active` - Action is enabled and will execute according to schedule
- `paused` - Action is temporarily disabled
- `completed` - Action has reached max executions
- `error` - Action encountered an error during last execution

## Exit Codes

- `0` - Success
- `1` - Error (check output for details)

## Troubleshooting

### Foreign Key Error

If you get a "foreign key constraint" error, ensure:

1. The opportunity ID exists
2. The user ID is a valid auth.users ID

Get a valid user ID:

```bash
python -c "from src.supabase.supabase_client import get_supabase_service; client = get_supabase_service(); print(client.auth.admin.list_users()[0].id)"
```

### Environment Issues

Make sure the virtual environment is activated and `.env` is properly configured:

```bash
source venv/bin/activate
```

### Permission Denied

Make the CLI executable:

```bash
chmod +x src/command/action_cli.py
```

## Architecture

The CLI is built on top of:

- **ActionRepository** (`src/repository/action_repository.py`) - Database access layer
- **ActionScheduler** (`src/service/action_scheduler.py`) - Scheduling and execution management
- **ActionExecutor** (`src/service/action_executor.py`) - Business logic for different action types

For details on the implementation, see [PLAN.md](PLAN.md) in the project root.
