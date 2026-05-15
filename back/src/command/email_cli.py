#!/usr/bin/env python3
"""
Unified CLI for email fetching workflows.

Usage:
    python -m src.command.email_cli fetch --user-id <USER_ID> [--max-results 50] [--classify-limit 200] [--after-date YYYY/MM/DD]
    python -m src.command.email_cli fetch-all [--max-results 50] [--user-id <USER_ID>]
    python -m src.command.email_cli loop [--user-id <USER_ID>] [--interval 120] [--max-results 50] [--classify-limit 30]
"""

import argparse
import atexit
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List

from dotenv import load_dotenv, find_dotenv
from src.infrastructure.clients.supabase import get_supabase_service
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import EMAIL_FETCH_MAX_RESULTS
from src.repository.email_repository import EmailRepository

# Load .env if available
try:
	_env_file = find_dotenv(usecwd=True)
	if _env_file:
		load_dotenv(_env_file, override=False)
except Exception:
	pass

default_user_id = os.environ.get("SUPABASE_USER_ID") or os.environ.get("DEFAULT_USER_ID")

DEFAULT_MAX_RESULTS = EMAIL_FETCH_MAX_RESULTS
DEFAULT_CLASSIFY_LIMIT = 200
DEFAULT_LOOP_CLASSIFY_LIMIT = 30
DEFAULT_INTERVAL_SECONDS = 120

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
	try:
		supabase = get_supabase_service()
		response = supabase.table("profile").select("id, email").execute()
		return response.data or []
	except Exception as exc:
		print(f"[email-cli] Error getting users: {exc}")
		return []


def run_fetch_emails(
	user_id: str,
	max_results: int = DEFAULT_MAX_RESULTS,
	classify_limit: int = DEFAULT_CLASSIFY_LIMIT,
	after_date: str | None = None,
) -> int:
	"""Fetch emails from Gmail, classify them, and link to contacts/accounts."""
	repo = EmailRepository()

	try:
		result = repo.fetch_and_process_emails(
			user_id=user_id,
			max_results=max_results,
			classify_limit=classify_limit,
			after_date=after_date,
			auto_resolve_date=True,
		)

		print(f"\n[email-cli] Summary:")
		print(f"  Status: {result.get('status')}")
		print(f"  Emails fetched: {result.get('emails_fetched', 0)}")
		print(f"  Emails classified: {result.get('emails_classified', 0)}")
		print(f"  Contacts created: {result.get('contacts_created', 0)}")
		print(f"  Accounts created: {result.get('accounts_created', 0)}")
		print(f"  RFQ processed: {result.get('rfq_processed', 0)}")
		print(f"  Opportunities created: {result.get('opportunities_created', 0)}")
		print(f"  Quotes generated: {result.get('quotes_generated', 0)}")

		errors = result.get("errors") or []
		if errors:
			print(f"\n[email-cli] Errors ({len(errors)}):")
			for err in errors[:5]:
				print(f"  - {err}")
			if len(errors) > 5:
				print(f"  ... and {len(errors) - 5} more errors")

		return 0 if result.get("status") == "ok" else 1
	except Exception as exc:
		print(f"[email-cli] Failed: {exc}")
		import traceback
		traceback.print_exc()
		return 1


def fetch_for_all_users(max_results: int = DEFAULT_MAX_RESULTS, user_id: str | None = None) -> int:
	print("\n" + "=" * 60)
	print("📧 Fetching Emails")
	print("=" * 60 + "\n")

	start_time = datetime.now()

	if user_id:
		user_ids = [user_id]
		print(f"Fetching emails for specific user: {user_id}\n")
	else:
		users = get_all_users()
		if not users:
			print("❌ No users found")
			return 1
		user_ids = [u["id"] for u in users]
		print(f"Found {len(user_ids)} users")
		for user in users:
			print(f"  - {user.get('email')} ({user.get('id')})")
		print(f"\nFetching emails for {len(user_ids)} users...\n")

	failed_users: List[str] = []
	for i, uid in enumerate(user_ids, 1):
		print(f"[{i}/{len(user_ids)}] Processing {uid}...")
		exit_code = run_fetch_emails(user_id=uid, max_results=max_results)
		if exit_code != 0:
			failed_users.append(uid)
		print()

	elapsed = (datetime.now() - start_time).total_seconds()

	print("=" * 60)
	print(f"✅ Successfully processed: {len(user_ids) - len(failed_users)}/{len(user_ids)} users")
	print(f"⏱️  Total time: {elapsed:.1f} seconds")
	if failed_users:
		print(f"❌ Failed users: {', '.join(failed_users)}")
	print("=" * 60 + "\n")

	return 0 if not failed_users else 1


def run_loop(
	user_id: str | None = None,
	interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
	max_results: int = DEFAULT_MAX_RESULTS,
	classify_limit: int = DEFAULT_LOOP_CLASSIFY_LIMIT,
):
	"""Run email fetching in a loop with minimum refresh interval."""
	if user_id:
		user_ids = [user_id]
		mode = "single user"
	else:
		mode = "all users"

	print(f"[email-cli] Starting continuous email fetching ({mode})")
	if user_id:
		print(f"[email-cli] User ID: {user_id}")
	print(f"[email-cli] Minimum interval: {interval_seconds} seconds ({interval_seconds / 60:.1f} minutes)")
	print(f"[email-cli] Max results per fetch per user: {max_results}")
	print(f"[email-cli] Classify limit per cycle per user: {classify_limit}")
	print(f"[email-cli] Press Ctrl+C to stop\n")

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
			print(f"[email-cli] Cycle #{cycle_count} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
			print(f"{'='*60}")

			if not user_id:
				users = get_all_users()
				if not users:
					print("[email-cli] No users found, skipping cycle")
					user_ids = []
				else:
					user_ids = [u["id"] for u in users]
					print(f"[email-cli] Found {len(users)} users")

			total_errors = 0
			for i, uid in enumerate(user_ids, 1):
				if len(user_ids) > 1:
					print(f"\n[{i}/{len(user_ids)}] Processing user {uid}...")

				exit_code = run_fetch_emails(
					user_id=uid,
					max_results=max_results,
					classify_limit=classify_limit,
					after_date=None,
				)
				if exit_code != 0:
					print(f"[email-cli] Warning: fetch returned exit code {exit_code} for user {uid}")
					total_errors += 1

			elapsed_time = time.time() - start_time
			sleep_time = max(0, interval_seconds - elapsed_time)

			print(f"\n[email-cli] Cycle completed in {elapsed_time:.2f} seconds")
			if total_errors > 0:
				print(f"[email-cli] Encountered {total_errors} error(s) during cycle")

			if sleep_time > 0:
				print(f"[email-cli] Sleeping for {sleep_time:.2f} seconds until next cycle...")
				time.sleep(sleep_time)
			else:
				print(f"[email-cli] Processing took longer than interval ({elapsed_time:.2f}s > {interval_seconds}s)")
				print("[email-cli] Starting next cycle immediately")

	except KeyboardInterrupt:
		print("\n\n[email-cli] Stopped by user (Ctrl+C)")
		print(f"[email-cli] Total cycles completed: {cycle_count}")
		_clear_status()
		sys.exit(0)


def main(argv=None):
	parser = argparse.ArgumentParser(description="Unified CLI for Gmail email fetching workflows.")
	sub = parser.add_subparsers(dest="command", required=True)

	fetch_parser = sub.add_parser("fetch", help="Fetch emails for a single user")
	fetch_parser.add_argument("--user-id", required=False, help="Supabase user ID")
	fetch_parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
	fetch_parser.add_argument("--classify-limit", type=int, default=DEFAULT_CLASSIFY_LIMIT)
	fetch_parser.add_argument("--after-date", type=str, default=None)

	fetch_all_parser = sub.add_parser("fetch-all", help="Fetch emails for all users")
	fetch_all_parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
	fetch_all_parser.add_argument("--user-id", required=False, help="Supabase user ID")

	loop_parser = sub.add_parser("loop", help="Continuously fetch emails")
	loop_parser.add_argument("--user-id", required=False, help="Supabase user ID")
	loop_parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS)
	loop_parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
	loop_parser.add_argument("--classify-limit", type=int, default=DEFAULT_LOOP_CLASSIFY_LIMIT)

	args = parser.parse_args(argv)

	if args.command == "fetch":
		user_id = args.user_id or default_user_id
		if not user_id:
			print("[email-cli] Missing user id. Provide --user-id or set SUPABASE_USER_ID in .env")
			return 2
		return run_fetch_emails(
			user_id=user_id,
			max_results=args.max_results,
			classify_limit=args.classify_limit,
			after_date=args.after_date,
		)

	if args.command == "fetch-all":
		return fetch_for_all_users(max_results=args.max_results, user_id=args.user_id)

	if args.command == "loop":
		user_id = args.user_id or default_user_id
		run_loop(
			user_id=user_id,
			interval_seconds=args.interval,
			max_results=args.max_results,
			classify_limit=args.classify_limit,
		)
		return 0

	print("Unknown command")
	return 2


if __name__ == "__main__":
	sys.exit(main())
