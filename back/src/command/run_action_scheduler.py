#!/usr/bin/env python3
"""
Action Scheduler Daemon

Continuously monitors and executes actions based on their schedules.

Usage:
    python src/command/run_action_scheduler.py [--interval SECONDS]
    
Options:
    --interval SECONDS   Check interval in seconds (default: 60)
    --daemon            Run as daemon in background
    --help              Show this help message
"""

import sys
import time
import argparse
import signal
from datetime import datetime
from src.service.action_scheduler import ActionScheduler
from src.infrastructure.runtime.env_loader import load_runtime_env

load_runtime_env(current_file=__file__)


class ActionSchedulerDaemon:
    """Daemon to run the action scheduler continuously."""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.scheduler = ActionScheduler()
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        print(f"\n[ActionSchedulerDaemon] Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self):
        """Start the daemon."""
        print(f"[ActionSchedulerDaemon] Starting action scheduler daemon")
        print(f"[ActionSchedulerDaemon] Check interval: {self.interval} seconds")
        print(f"[ActionSchedulerDaemon] Press Ctrl+C to stop")
        print("-" * 80)
        
        self.running = True
        
        while self.running:
            try:
                # Run the scheduler check
                now = datetime.now()
                print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Checking for due actions...")
                
                # Execute due actions
                results = self.scheduler._check_and_execute()
                
                if results:
                    print(f"[ActionSchedulerDaemon] Executed {len(results)} action(s)")
                    for result in results:
                        action_id = result.get('action_id')
                        status = result.get('status')
                        duration = result.get('duration_ms', 0)
                        print(f"  - Action {action_id}: {status} ({duration}ms)")
                else:
                    print(f"[ActionSchedulerDaemon] No actions due")
                
                # Wait for next interval
                if self.running:
                    print(f"[ActionSchedulerDaemon] Sleeping for {self.interval} seconds...")
                    time.sleep(self.interval)
                    
            except KeyboardInterrupt:
                print(f"\n[ActionSchedulerDaemon] Interrupted, shutting down...")
                break
            except Exception as e:
                print(f"[ActionSchedulerDaemon] Error during execution: {e}")
                import traceback
                traceback.print_exc()
                # Continue running even if one iteration fails
                if self.running:
                    print(f"[ActionSchedulerDaemon] Continuing after error, sleeping {self.interval}s...")
                    time.sleep(self.interval)
        
        print(f"[ActionSchedulerDaemon] Daemon stopped")


def main(argv=None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Action Scheduler Daemon - Continuously execute scheduled actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with default 60 second interval
    python src/command/run_action_scheduler.py
    
    # Run with 30 second interval
    python src/command/run_action_scheduler.py --interval 30
    
    # Run with 5 minute interval
    python src/command/run_action_scheduler.py --interval 300
        """
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon in background (not yet implemented)'
    )
    
    args = parser.parse_args(argv)

    if args.interval <= 0:
        parser.error("--interval must be a positive integer")
    
    if args.daemon:
        print("Error: Daemon mode not yet implemented. Run in foreground for now.")
        sys.exit(1)
    
    # Create and start the daemon
    daemon = ActionSchedulerDaemon(interval=args.interval)
    daemon.start()


if __name__ == '__main__':
    main()
