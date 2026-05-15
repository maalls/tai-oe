"""Legacy wrapper for the unified single-user fetch workflow.

Delegates to ``src.command.email_cli.run_fetch_emails`` while preserving the
historical module entrypoint:
	python -m src.command.fetch_emails --user-id <USER_ID> [--max-results 50] [--classify-limit 200] [--after-date YYYY/MM/DD]
"""

import argparse
import os
import sys
from src.command.email_cli import (
	DEFAULT_CLASSIFY_LIMIT,
	DEFAULT_MAX_RESULTS,
	run_fetch_emails as unified_run_fetch_emails,
)

# Load .env if available
try:
	from dotenv import load_dotenv, find_dotenv
	env_file = find_dotenv(usecwd=True)
	if env_file:
		load_dotenv(env_file, override=False)
except Exception:
	pass

default_user_id = os.environ.get("SUPABASE_USER_ID") or os.environ.get("DEFAULT_USER_ID")


def run(
	user_id: str,
	max_results: int = DEFAULT_MAX_RESULTS,
	classify_limit: int = DEFAULT_CLASSIFY_LIMIT,
	after_date: str = None,
	workflow=None,
) -> int:
	"""Run email fetch/classification through the unified email CLI workflow."""
	# Keep workflow in signature for backward compatibility with older call sites.
	_ = workflow
	return unified_run_fetch_emails(
		user_id=user_id,
		max_results=max_results,
		classify_limit=classify_limit,
		after_date=after_date,
	)


def main(argv=None):
	parser = argparse.ArgumentParser(description="Legacy wrapper for the unified single-user fetch workflow.")
	parser.add_argument("--user-id", required=False, help="Supabase user ID")
	parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS, help="Max messages to fetch from Gmail")
	parser.add_argument("--classify-limit", type=int, default=DEFAULT_CLASSIFY_LIMIT, help="Max unclassified emails to classify")
	parser.add_argument(
		"--after-date",
		type=str,
		default=None,
		help="Fetch emails after this date (YYYY/MM/DD or Unix seconds). Defaults to latest email timestamp (or yesterday if none).",
	)
	args = parser.parse_args(argv)

	user_id = args.user_id or default_user_id
	if not user_id:
		print("[fetch-emails] Missing user id. Provide --user-id or set SUPABASE_USER_ID in .env")
		sys.exit(2)

	exit_code = run(
		user_id=user_id,
		max_results=args.max_results,
		classify_limit=args.classify_limit,
		after_date=args.after_date,  # Pass through, will be auto-resolved if None
	)
	sys.exit(exit_code)


if __name__ == "__main__":
	main()
