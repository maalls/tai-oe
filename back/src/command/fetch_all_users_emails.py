"""Fetch emails for all users with Gmail authorization.

This script:
1) Gets all users who have authorized Gmail access
2) Fetches their latest emails
3) Classifies unclassified emails
4) Creates/updates contacts from sender information
5) Creates/links accounts based on sender domain
6) Updates sender verification records
7) Outputs summary report

Usage:
	python -m src.command.fetch_all_users_emails [--max-results 50]
"""

import argparse
import sys

from src.config import EMAIL_FETCH_MAX_RESULTS
from src.command.email_cli import fetch_for_all_users




def main(argv=None):
	parser = argparse.ArgumentParser(description="Fetch Gmail emails for all authorized users.")
	parser.add_argument("--max-results", type=int, default=EMAIL_FETCH_MAX_RESULTS, help="Max messages to fetch per user")
	parser.add_argument("--user-id", type=str, default=None, help="Optional: Fetch only for specific user")

	args = parser.parse_args(argv)
	# Legacy entrypoint now delegates to the unified email CLI implementation.
	return fetch_for_all_users(max_results=args.max_results, user_id=args.user_id)


if __name__ == "__main__":
	sys.exit(main())
