# Action CLI Quick Reference

## Most Common Commands

### List all actions for an opportunity

```bash
python -m src.command.action_cli list-actions c32c94d9-66ea-427b-8ba0-4946191f4c31
```

### Create a monthly recurring quote

```bash
python -m src.command.action_cli create-action \
  c32c94d9-66ea-427b-8ba0-4946191f4c31 \
  393be11f-807f-4f0d-bfbe-5aa93f409b48 \
  recurring_quote \
  monthly \
  '{"day_of_month": 1, "time": "09:00", "timezone": "UTC"}' \
  '{"template_id": "default", "days_valid": 30}'
```

### Create a weekly follow-up email (max 12 times)

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

### Create a daily recurring invoice

```bash
python -m src.command.action_cli create-action \
  c32c94d9-66ea-427b-8ba0-4946191f4c31 \
  393be11f-807f-4f0d-bfbe-5aa93f409b48 \
  recurring_invoice \
  daily \
  '{"time": "08:00", "timezone": "UTC"}' \
  '{"invoice_type": "standard"}'
```

### Get details of a specific action

```bash
python -m src.command.action_cli get-action <action_id>
```

### Pause an action

```bash
python -m src.command.action_cli pause-action <action_id>
```

### Resume a paused action

```bash
python -m src.command.action_cli resume-action <action_id>
```

### Delete an action

```bash
python -m src.command.action_cli delete-action <action_id>
```

### Manually execute an action now

```bash
python -m src.command.action_cli execute-action <action_id>
```

### View execution logs (last 10)

```bash
python -m src.command.action_cli get-logs <action_id> 10
```

## Test Data

**Test Opportunity ID:** `c32c94d9-66ea-427b-8ba0-4946191f4c31`

**Test User ID:** `393be11f-807f-4f0d-bfbe-5aa93f409b48`

## Run Test Suite

```bash
python test_action_cli_comprehensive.py
```

## Get Current User ID

```bash
python -c "from src.supabase.supabase_client import get_supabase_service; client = get_supabase_service(); print(client.auth.admin.list_users()[0].id)"
```

## Day of Week Reference

- 0 = Sunday
- 1 = Monday
- 2 = Tuesday
- 3 = Wednesday
- 4 = Thursday
- 5 = Friday
- 6 = Saturday

## Status States

- `active` - Running normally
- `paused` - Temporarily disabled
- `completed` - Reached max executions
- `error` - Last execution failed

## Timezone Examples

- `UTC`
- `Europe/Paris` (CET/CEST)
- `Europe/London` (GMT/BST)
- `America/New_York` (EST/EDT)
- `America/Los_Angeles` (PST/PDT)
- `Asia/Tokyo` (JST)
- `Australia/Sydney` (AEDT/AEST)
