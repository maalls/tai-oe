# Development Server (dev.py)

## Quick Start

```bash
# Start with automatic hot-reload (watches files for changes)
python dev.py

# Start without watching (normal mode, no auto-restart)
python dev.py --no-watch

# View help
python dev.py --help
```

## Features

### Hot-Reload Mode (Default)

When you run `python dev.py`, the server will:

- 🧹 Clean up any existing process on port 8088
- 🚀 Start the RAG server
- 🔍 Watch for file changes in:
  - `src/`
  - `script/`
  - `config.yml`
  - `.env`
- 🔄 Automatically restart the server when changes are detected
- ⛔ Gracefully shutdown on Ctrl+C

### Watch Output

```
🧹 Cleaning up port 8088...
   Killed existing process on port 8088 (PID: 12345)
🔍 Starting hot-reload watcher...
   Backend: watchfiles
   Watching: src, script, config.yml, .env

============================================================
🚀 Starting RAG server...
============================================================

CSV server on http://127.0.0.1:8088
Storage dir: /Users/malo/Documents/Projects/rkllm-server/external/rag/back/var/storage
```

### Making Changes

1. Edit any file in `src/`, `script/`, or `config.yml`
2. Save the file
3. Watch for output:
   ```
   📝 Changes detected: src/rag/rag.py
   🔄 Restarting server...
   ```
4. Server restarts automatically within ~1 second

### How It Works

### Port Management

- Uses `lsof` to find any existing process on port 8088
- Kills the old process before starting a new one
- Waits 1 second for port to be released (prevents "Address already in use" errors)
- Server already has `SO_REUSEADDR` enabled for immediate reuse

### File Watching

- Uses `watchfiles` library for efficient file monitoring
- Monitors modifications to `.py`, `.yml`, and `.env` files
- Implements **debounce logic** to prevent multiple restarts within 2 seconds
- This prevents cascade restarts when file editors save multiple times
- Triggers restart on any change in watched directories

### Debouncing

The watcher has a 2-second cooldown between restarts. This prevents issues when:

- File editors perform multiple writes (auto-save, formatting, etc.)
- Multiple files change at nearly the same time
- Watchfiles reports duplicate change events

This ensures only ONE server instance runs at a time.

### Signal Handling

- Responds to Ctrl+C with graceful shutdown
- Properly terminates child server process
- Forces kill if graceful termination takes >3 seconds

## Troubleshooting

### Port Already in Use

If you see `Address already in use` error:

```bash
# The kill_port_process function in dev.py should handle this
# But if it persists, manually find and kill the process:
lsof -i :8088
kill -9 <PID>
```

### File Not Being Watched

- Ensure the file is in `src/`, `script/`, or is `config.yml`/`.env` in the root
- The watcher only monitors these directories

### Server Not Restarting

- Check that you're editing files, not just viewing them
- Some editors may not trigger file system events properly
- Try saving again or restarting dev.py

## Development Workflow

```bash
# Terminal 1: Start dev server
cd back
python dev.py

# Terminal 2: Make code changes and save
# dev.py will auto-restart the server
# Terminal 2: Test API endpoints
curl http://localhost:8088/api/csv/sources
```

## Production Deployment

For production, run without dev.py:

```bash
python src/rag/rag.py
```

Or use a production ASGI server like Gunicorn or uvicorn if migrating to async.
