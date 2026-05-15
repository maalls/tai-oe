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
from src.config import EMAIL_FETCH_MAX_RESULTS
from src.command.email_cli import run_loop as unified_run_loop


def run_loop(
	user_id: str = None,
	interval_seconds: int = 30,
	max_results: int = EMAIL_FETCH_MAX_RESULTS,
	classify_limit: int = 200,
):
	"""Legacy loop entrypoint delegated to unified email CLI."""
	return unified_run_loop(
		user_id=user_id,
		interval_seconds=interval_seconds,
		max_results=max_results,
		classify_limit=classify_limit,
	)


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
		help="Minimum seconds between fetch cycles (default: 30)"
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
