"""Continuously fetch emails for all users with a minimum refresh interval.

This script runs fetch_emails for all users in a loop with a minimum 2-minute refresh time.
If processing takes longer than 2 minutes, the next fetch starts immediately.

When a user has IMAP configured and enabled, the collection uses IMAP.
Otherwise it falls back to Gmail.

Usage:
	python -m src.command.fetch_emails_loop [--interval 120] [--max-results 50] [--classify-limit 30]
	python -m src.command.fetch_emails_loop --user-id <USER_ID>  # Single user mode (optional)
"""

import argparse
from src.command.email_cli import (
	DEFAULT_INTERVAL_SECONDS,
	DEFAULT_LOOP_CLASSIFY_LIMIT,
	DEFAULT_MAX_RESULTS,
	run_loop as unified_run_loop,
)


def run_loop(
	user_id: str = None,
	interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
	max_results: int = DEFAULT_MAX_RESULTS,
	classify_limit: int = DEFAULT_LOOP_CLASSIFY_LIMIT,
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
		default=DEFAULT_INTERVAL_SECONDS,
		help=f"Minimum seconds between fetch cycles (default: {DEFAULT_INTERVAL_SECONDS})"
	)
	parser.add_argument(
		"--max-results",
		type=int,
		default=DEFAULT_MAX_RESULTS,
		help="Max messages to fetch from the active provider per cycle per user"
	)
	parser.add_argument(
		"--classify-limit",
		type=int,
		default=DEFAULT_LOOP_CLASSIFY_LIMIT,
		help=f"Max unclassified emails to classify per cycle per user (default: {DEFAULT_LOOP_CLASSIFY_LIMIT})"
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
