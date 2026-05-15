"""Legacy wrapper for unified fetch-all email workflow.

Delegates execution to ``src.command.email_cli.fetch_for_all_users`` while
preserving the historical module entrypoint:
	python -m src.command.fetch_all_users_emails [--max-results 50] [--user-id <USER_ID>]
"""

import argparse
import sys

from src.command.email_cli import DEFAULT_MAX_RESULTS, fetch_for_all_users

def main(argv=None):
	parser = argparse.ArgumentParser(description="Legacy wrapper for unified fetch-all email workflow.")
	parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS, help="Max messages to fetch per user")
	parser.add_argument("--user-id", type=str, default=None, help="Optional: Fetch only for specific user")

	args = parser.parse_args(argv)
	# Legacy entrypoint now delegates to the unified email CLI implementation.
	return fetch_for_all_users(max_results=args.max_results, user_id=args.user_id)


if __name__ == "__main__":
	sys.exit(main())
