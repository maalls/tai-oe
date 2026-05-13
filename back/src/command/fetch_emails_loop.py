"""Continuously fetch emails for all users with a minimum refresh interval.

This script runs fetch_emails for all users in a loop with a minimum 2-minute refresh time.
If processing takes longer than 2 minutes, the next fetch starts immediately.

When a user has IMAP configured and enabled, the collection uses IMAP.
Otherwise it falls back to Gmail.

Usage:
	python -m src.command.fetch_emails_loop [--interval 120] [--max-results 50] [--classify-limit 200]
	python -m src.command.fetch_emails_loop --user-id <USER_ID>  # Single user mode (optional)
"""

import argparse
import os
import sys
import time
import json
import atexit
from pathlib import Path
from typing import List
from src.config import EMAIL_FETCH_MAX_RESULTS
from src.command.fetch_emails import run as fetch_emails_run
from src.repository.email_repository import EmailRepository

# Load .env if available
try:
	from dotenv import load_dotenv, find_dotenv
	env_file = find_dotenv(usecwd=True)
	if env_file:
		load_dotenv(env_file, override=False)
except Exception:
	pass

STATUS_PATH = Path(__file__).resolve().parents[3] / "var" / "email_fetch_loop.json"


def _write_status(payload: dict):
	try:
		STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
		STATUS_PATH.write_text(json.dumps(payload), encoding="utf-8")
	except Exception:
		pass


def _clear_status():
	try:
		if STATUS_PATH.exists():
			STATUS_PATH.unlink()
	except Exception:
		pass


def get_all_users() -> List[dict]:
	"""Get all users from the profile table."""
	from src.supabase import get_supabase_service
	
	try:
		supabase = get_supabase_service()
		response = supabase.table("profile").select("id, email").execute()
		
		if response.data:
			return response.data
		return []
	except Exception as e:
		print(f"[fetch-emails-loop] Error getting users: {e}")
		return []


def get_user_fetch_provider(user_id: str) -> str:
	"""Return the active email provider for a user.

	Uses IMAP when configured and enabled, Gmail when authorized, and returns
	None when no provider is available.
	"""
	repo = EmailRepository()
	return repo.get_available_fetch_provider(user_id)


def run_loop(user_id: str = None, interval_seconds: int = 30, max_results: int = EMAIL_FETCH_MAX_RESULTS, classify_limit: int = 200):
	"""Run email fetching in a loop with minimum refresh interval.
	
	Args:
		user_id: Optional specific user ID. If None, fetches for all users.
		interval_seconds: Minimum time between fetch cycles (default: 120 seconds / 2 minutes)
		max_results: Max messages to fetch from the active provider per cycle per user
		classify_limit: Max unclassified emails to classify per cycle per user
	"""
	# Determine mode
	if user_id:
		user_ids = [user_id]
		mode = "single user"
	else:
		mode = "all users"
	
	print(f"[fetch-emails-loop] Starting continuous email fetching ({mode})")
	if user_id:
		print(f"[fetch-emails-loop] User ID: {user_id}")
	print(f"[fetch-emails-loop] Minimum interval: {interval_seconds} seconds ({interval_seconds / 60:.1f} minutes)")
	print(f"[fetch-emails-loop] Max results per fetch per user: {max_results}")
	print(f"[fetch-emails-loop] Classify limit per cycle per user: {classify_limit}")
	print(f"[fetch-emails-loop] Press Ctrl+C to stop\n")
	
	cycle_count = 0
	
	started_at = time.time()
	_write_status({
		"pid": os.getpid(),
		"started_at": started_at,
		"last_heartbeat": started_at,
		"mode": "single" if user_id else "all",
	})
	atexit.register(_clear_status)

	try:
		while True:
			cycle_count += 1
			start_time = time.time()
			_write_status({
				"pid": os.getpid(),
				"started_at": started_at,
				"last_heartbeat": start_time,
				"mode": "single" if user_id else "all",
			})
			
			print(f"\n{'='*60}")
			print(f"[fetch-emails-loop] Cycle #{cycle_count} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
			print(f"{'='*60}")
			
			# Get user list (refresh each cycle in case users are added/removed)
			if not user_id:
				users = get_all_users()
				if not users:
					print(f"[fetch-emails-loop] No users found, skipping cycle")
				else:
					available_user_ids = []
					skipped_users = 0
					for user in users:
						uid = user['id']
						provider = get_user_fetch_provider(uid)
						if provider is None:
							skipped_users += 1
							print(f"[fetch-emails-loop] Skipping user {uid}: no IMAP or Gmail provider configured")
							continue
						available_user_ids.append(uid)

					user_ids = available_user_ids
					print(f"[fetch-emails-loop] Found {len(users)} users, {len(user_ids)} eligible, {skipped_users} skipped")
					if not user_ids:
						print(f"[fetch-emails-loop] No eligible users for this cycle")
			
			# Process each user
			total_errors = 0
			for i, uid in enumerate(user_ids, 1):
				provider = get_user_fetch_provider(uid)
				if provider is None:
					print(f"[fetch-emails-loop] Skipping user {uid}: no provider available")
					continue
				if len(user_ids) > 1:
					print(f"\n[{i}/{len(user_ids)}] Processing user {uid} via {provider.upper()}...")
				else:
					print(f"[fetch-emails-loop] Processing user {uid} via {provider.upper()}...")
				
				try:
					exit_code = fetch_emails_run(
						user_id=uid,
						max_results=max_results,
						classify_limit=classify_limit,
						after_date=None  # Auto-resolve to latest email date
					)
					
					if exit_code != 0:
						print(f"[fetch-emails-loop] Warning: fetch_emails returned exit code {exit_code} for user {uid}")
						total_errors += 1
						
				except Exception as exc:
					print(f"[fetch-emails-loop] Error fetching for user {uid}: {exc}")
					import traceback
					traceback.print_exc()
					total_errors += 1
			
			# Calculate elapsed time and sleep if needed
			elapsed_time = time.time() - start_time
			sleep_time = max(0, interval_seconds - elapsed_time)
			
			print(f"\n[fetch-emails-loop] Cycle completed in {elapsed_time:.2f} seconds")
			if total_errors > 0:
				print(f"[fetch-emails-loop] Encountered {total_errors} error(s) during cycle")
			
			if sleep_time > 0:
				print(f"[fetch-emails-loop] Sleeping for {sleep_time:.2f} seconds until next cycle...")
				time.sleep(sleep_time)
			else:
				print(f"[fetch-emails-loop] Processing took longer than interval ({elapsed_time:.2f}s > {interval_seconds}s)")
				print(f"[fetch-emails-loop] Starting next cycle immediately")
	
	except KeyboardInterrupt:
		print(f"\n\n[fetch-emails-loop] Stopped by user (Ctrl+C)")
		print(f"[fetch-emails-loop] Total cycles completed: {cycle_count}")
		_clear_status()
		sys.exit(0)


def main(argv=None):
	parser = argparse.ArgumentParser(
		description="Continuously fetch emails for all users (or a specific user), using IMAP when configured and Gmail otherwise."
	)
	parser.add_argument(
		"--user-id",
		required=False,
		help="Optional: Fetch only for specific user. If omitted, fetches for all users."
	)
	parser.add_argument(
		"--interval",
		type=int,
		default=30,
		help="Minimum seconds between fetch cycles (default: 120 = 2 minutes)"
	)
	parser.add_argument(
		"--max-results",
		type=int,
		default=EMAIL_FETCH_MAX_RESULTS,
		help="Max messages to fetch from the active provider per cycle per user"
	)
	parser.add_argument(
		"--classify-limit",
		type=int,
		default=30,
		help="Max unclassified emails to classify per cycle per user"
	)

	args = parser.parse_args(argv)

	user_id = args.user_id  # None = all users mode

	run_loop(
		user_id=user_id,
		interval_seconds=args.interval,
		max_results=args.max_results,
		classify_limit=args.classify_limit,
	)


if __name__ == "__main__":
	main()
