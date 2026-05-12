# Action Scheduler Daemon

The Action Scheduler Daemon continuously monitors the database for actions that are due for execution and executes them automatically.

## Overview

The scheduler daemon:

- Runs continuously in the background
- Checks for due actions at regular intervals (default: 60 seconds)
- Executes actions that are past their `next_execution_at` time
- Updates `last_executed_at` and `next_execution_at` after each run
- Increments `execution_count` and marks as complete if `max_executions` reached
- Logs all executions to `action_execution_log` table

## Running the Scheduler

### Development

Run the scheduler in foreground mode:

```bash
cd back
source venv/bin/activate
python src/command/run_action_scheduler.py
```

With custom interval (check every 30 seconds):

```bash
python src/command/run_action_scheduler.py --interval 30
```

### Production

#### Using systemd

1. Edit the service file to set correct paths:

```bash
nano action-scheduler.service
```

Update these paths:

- `WorkingDirectory=/path/to/rkllm-server/external/rag/back`
- `Environment="PATH=/path/to/rkllm-server/external/rag/back/venv/bin"`
- `ExecStart=/path/to/rkllm-server/external/rag/back/venv/bin/python src/command/run_action_scheduler.py --interval 60`
- `User=your-user` (replace www-data)
- `Group=your-group` (replace www-data)

2. Install the service:

```bash
sudo cp action-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
```

3. Start the service:

```bash
sudo systemctl start action-scheduler
```

4. Enable auto-start on boot:

```bash
sudo systemctl enable action-scheduler
```

5. Check status:

```bash
sudo systemctl status action-scheduler
```

6. View logs:

```bash
sudo journalctl -u action-scheduler -f
```

#### Using Supervisor

1. Edit the supervisor config:

```bash
nano action-scheduler.conf
```

Update paths as needed.

2. Install the config:

```bash
sudo cp action-scheduler.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
```

3. Start the daemon:

```bash
sudo supervisorctl start action-scheduler
```

4. Check status:

```bash
sudo supervisorctl status action-scheduler
```

5. View logs:

```bash
sudo tail -f /var/log/action-scheduler/action-scheduler.log
```

## Command Line Options

```
python src/command/run_action_scheduler.py [OPTIONS]

Options:
  --interval SECONDS   Check interval in seconds (default: 60)
  --daemon            Run as daemon in background (not yet implemented)
  --help              Show this help message
```

## How It Works

1. **Initialization**: Loads environment variables and connects to database
2. **Main Loop**:
   - Queries database for actions where `status = 'active'` AND `next_execution_at <= NOW()`
   - For each due action:
     - Calls ActionExecutor to run the action
     - Records execution in `action_execution_log`
     - Updates `execution_count` and `last_executed_at`
     - Calculates and sets new `next_execution_at` based on schedule
     - Marks as 'completed' if `max_executions` reached
   - Waits for interval period before next check

## Monitoring

### Check if running (systemd)

```bash
sudo systemctl is-active action-scheduler
```

### View recent logs

```bash
sudo journalctl -u action-scheduler --since "1 hour ago"
```

### Monitor in real-time

```bash
sudo journalctl -u action-scheduler -f
```

### Check execution logs in database

```sql
SELECT * FROM action_execution_log
ORDER BY executed_at DESC
LIMIT 20;
```

## Troubleshooting

### Service won't start

1. Check the service file has correct paths:

   ```bash
   sudo systemctl cat action-scheduler
   ```

2. Check permissions:

   ```bash
   ls -la /path/to/rkllm-server/external/rag/back/src/command/run_action_scheduler.py
   ```

3. Test manually:

   ```bash
   cd /path/to/rkllm-server/external/rag/back
   source venv/bin/activate
   python src/command/run_action_scheduler.py
   ```

4. Check environment variables:
   ```bash
   cat .env
   ```

### Actions not executing

1. Check if daemon is running:

   ```bash
   sudo systemctl status action-scheduler
   ```

2. Check for due actions:

   ```sql
   SELECT id, action_type, status, next_execution_at
   FROM action
   WHERE status = 'active' AND next_execution_at <= NOW();
   ```

3. Check recent logs for errors:

   ```bash
   sudo journalctl -u action-scheduler --since "10 minutes ago"
   ```

4. Verify action schedule is configured correctly:
   ```sql
   SELECT id, schedule_type, schedule_config, next_execution_at
   FROM action
   WHERE id = 'action-id-here';
   ```

### High CPU usage

- Increase the check interval:

  ```bash
  sudo systemctl edit action-scheduler
  ```

  Add:

  ```ini
  [Service]
  ExecStart=
  ExecStart=/path/to/venv/bin/python src/command/run_action_scheduler.py --interval 120
  ```

- Then reload and restart:
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl restart action-scheduler
  ```

## Testing

### Create a test action with near-immediate execution

```bash
python -m src.command.action_cli create-action \
  <opportunity_id> \
  <user_id> \
  recurring_quote \
  one_time \
  '{}' \
  '{"test": true}'
```

This creates an action that executes immediately. Watch the scheduler logs to see it execute:

```bash
sudo journalctl -u action-scheduler -f
```

### Manually trigger scheduler check

Stop the daemon and run manually to see detailed output:

```bash
sudo systemctl stop action-scheduler
cd /path/to/rkllm-server/external/rag/back
source venv/bin/activate
python src/command/run_action_scheduler.py --interval 10
```

Press Ctrl+C to stop when done, then restart the service:

```bash
sudo systemctl start action-scheduler
```

## Performance Considerations

- **Check Interval**: Default 60 seconds. Lower for faster response, higher for less database load.
- **Concurrent Executions**: Currently executes actions sequentially. For high volumes, consider running multiple instances or implementing async execution.
- **Database Load**: Each check queries the action table. Add database indexes on `status` and `next_execution_at` if not already present.
- **Long-Running Actions**: If actions take longer than the interval, they may overlap. Consider increasing interval or implementing execution locks.

## Security

The scheduler runs with the permissions of the configured user. Ensure:

- The user has read access to the codebase
- The user has write access to logs directory
- Database credentials in `.env` are secure
- The service file is owned by root (for systemd)

## Stopping the Scheduler

### Graceful shutdown (systemd)

```bash
sudo systemctl stop action-scheduler
```

### Force kill (if hung)

```bash
sudo systemctl kill -s SIGKILL action-scheduler
```

### Temporary disable

```bash
sudo systemctl stop action-scheduler
sudo systemctl disable action-scheduler
```

To re-enable:

```bash
sudo systemctl enable action-scheduler
sudo systemctl start action-scheduler
```
