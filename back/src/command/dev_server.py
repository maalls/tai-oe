#!/usr/bin/env python3
"""
Hot-reload server: automatically restart when Python files or config changes.

Usage:
    python -m src.command.dev_server          # Start with auto-reload
    python -m src.command.dev_server --no-watch   # Run without watching (normal start)

Watches:
    - src/rag/*.py
    - src/**/*.py
    - script/text/*.py
    - config.yml
    - .env
"""

import subprocess
import sys
import signal
import os
import time
import socket
from pathlib import Path
from collections import deque

BACK_DIR = Path(__file__).resolve().parents[2]

# Try to use watchfiles, fallback to watchdog
try:
    from watchfiles import watch, run_process
    WATCH_BACKEND = "watchfiles"
except ImportError:
    print("Installing watchfiles for auto-reload....")
    subprocess.run([sys.executable, "-m", "pip", "install", "watchfiles"])
    from watchfiles import watch, run_process
    WATCH_BACKEND = "watchfiles"


def is_port_available(port=8088, timeout=0.1):
    """Check if a port is available for binding on all interfaces."""
    try:
        # Check both localhost and all interfaces (0.0.0.0)
        for addr in ['127.0.0.1', '']:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                # Try to bind to the port (all interfaces or localhost)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if hasattr(socket, 'SO_REUSEPORT'):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                sock.bind((addr, port))
                sock.close()
            except OSError:
                sock.close()
                return False  # Port is in use
        return True  # Port is available on all interfaces
    except Exception:
        return True  # Assume available if we can't check


def wait_for_port_available(port=8088, max_wait=10, interval=0.5):
    """Wait for port to become available with exponential backoff."""
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait:
        if is_port_available(port):
            print(f"   ✓ Port {port} is now available")
            return True
        
        attempt += 1
        wait_time = min(interval * (1.2 ** attempt), 2.0)  # Exponential backoff, max 2s
        print(f"   ⏳ Waiting for port {port} to be available... ({attempt} attempts)")
        time.sleep(wait_time)
    
    print(f"   ✗ Port {port} still in use after {max_wait}s")
    return False


def kill_port_process(port=8088):
    """Kill only the RAG server process on the specified port."""
    try:
        # Find processes using the port
        result = subprocess.run(
            f"lsof -ti:{port}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        pids = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
        
        for pid in pids:
            try:
                # Check if it's actually our Python RAG process
                cmd_result = subprocess.run(
                    f"ps -p {pid} -o command=",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                cmd = cmd_result.stdout.strip()
                
                # Only kill if it's the current API server module.
                if "src.api.server" in cmd:
                    os.kill(int(pid), signal.SIGTERM)  # SIGTERM (graceful) not SIGKILL
                    print(f"   Killed RAG process on port {port} (PID: {pid})")
                    time.sleep(0.2)
            except (ValueError, ProcessLookupError, OSError):
                pass
        
        if pids:
            time.sleep(1.0)
    except subprocess.TimeoutExpired:
        pass  # Port kill is best-effort
    except Exception:
        pass  # Port kill is best-effort


def get_watched_paths():
    """Get list of paths to watch for changes."""
    back_dir = BACK_DIR
    
    watched = [
        back_dir / "src",
        back_dir / "script",
        back_dir / "config.yml",
        back_dir / ".env",
    ]
    
    return [str(p) for p in watched if p.exists()]


def get_server_port(default=8088):
    """Resolve server port from env first, then from local .env file."""
    env_port = os.environ.get("PORT")
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass

    env_file = BACK_DIR / ".env"
    if env_file.exists():
        try:
            for raw_line in env_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("PORT="):
                    try:
                        return int(line.split("=", 1)[1].strip())
                    except ValueError:
                        break
        except Exception:
            pass

    return default


def run_server(server_port):
    """Start the RAG server."""
    print("\n" + "="*60)
    print("🚀 Starting RAG server...")
    print(f"   Port: {server_port}")
    print("="*60 + "\n")

    back_dir = BACK_DIR
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{back_dir}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(back_dir)
    )
    env["PORT"] = str(server_port)

    process = subprocess.Popen(
        [sys.executable, "-m", "src.api.server"],
        cwd=str(back_dir),
        env=env,
    )
    
    return process


def main():
    """Main hot-reload loop."""
    no_watch = "--no-watch" in sys.argv
    server_port = get_server_port()
    
    # Kill any existing process on configured server port
    print(f"🧹 Cleaning up port {server_port}...")
    kill_port_process(server_port)
    
    if no_watch:
        print("Starting server without auto-reload...")
        back_dir = BACK_DIR
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{back_dir}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(back_dir)
        )
        env["PORT"] = str(server_port)
        process = subprocess.run(
            [sys.executable, "-m", "src.api.server"],
            cwd=str(back_dir),
            env=env,
        )
        sys.exit(process.returncode)
    
    print("🔍 Starting hot-reload watcher...")
    print(f"   Backend: {WATCH_BACKEND}")
    print(f"   Watching: {', '.join(get_watched_paths())}\n")
    
    process = None
    last_restart_time = 0  # Debounce restarts
    RESTART_COOLDOWN = 3.0  # Minimum seconds between restarts
    
    def signal_handler(sig, frame):
        """Handle interrupt gracefully."""
        print("\n\n⛔ Shutting down...")
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure port is available before starting
    wait_for_port_available(server_port, max_wait=5, interval=0.3)
    
    process = run_server(server_port)
    
    try:
        for changes in watch(*get_watched_paths()):
            # Debounce: skip if restarted too recently
            current_time = time.time()
            if current_time - last_restart_time < RESTART_COOLDOWN:
                continue
            
            # Get relative paths for display
            changed_files = []
            for change_type, path in changes:
                rel_path = Path(path).relative_to(BACK_DIR)
                changed_files.append(str(rel_path))
            
            print(f"\n📝 Changes detected: {', '.join(changed_files)}")
            print("🔄 Restarting server...\n")
            
            # Kill existing process
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            
            # Clean up port before restarting
            time.sleep(0.5)
            kill_port_process(server_port)
            
            # Wait for port to actually become available (longer timeout for safety)
            if not wait_for_port_available(server_port, max_wait=20, interval=0.3):
                print("   ⚠️  Port still in use, forcing kill and retrying...")
                kill_port_process(server_port)
                time.sleep(3.0)
            
            # Start new process
            process = run_server(server_port)
            last_restart_time = time.time()
    
    except KeyboardInterrupt:
        print("\n⛔ Shutting down...")
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        sys.exit(0)


if __name__ == "__main__":
    main()
