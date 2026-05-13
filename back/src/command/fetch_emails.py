"""Fetch new Gmail emails and classify unclassified ones.

This script reuses EmailRepository to:
1) Pull latest messages from Gmail (forcing API fetch)
2) Classify any emails that are still unclassified

Usage:
	python -m src.command.fetch_emails --user-id <USER_ID> [--max-results 50] [--classify-limit 200]
"""

import argparse
import os
import sys
from src.config import EMAIL_FETCH_MAX_RESULTS

# Load .env if available
try:
	from dotenv import load_dotenv, find_dotenv
	env_file = find_dotenv(usecwd=True)
	if env_file:
		load_dotenv(env_file, override=False)
except Exception:
	pass

default_user_id = os.environ.get("SUPABASE_USER_ID") or os.environ.get("DEFAULT_USER_ID")
default_use_new_workflow = os.environ.get("USE_NEW_EMAIL_WORKFLOW", "0") in {"1", "true", "True"}


def _get_legacy_repo():
	"""Create the legacy repository lazily to avoid import-time side effects."""
	from src.repository.email_repository import EmailRepository

	return EmailRepository()


def _run_new_workflow(user_id: str, classify_limit: int = 200) -> int:
	"""Run the new DDD workflow (classification only) in opt-in mode."""
	from src.infrastructure.factory import ServiceFactory

	factory = ServiceFactory()
	workflow = factory.create_email_workflow_service()
	emails = workflow.email_service.get_all_unclassified(limit=classify_limit, user_id=user_id)

	classified = 0
	errors = 0
	for email in emails:
		try:
			workflow.process_new_email(email.id)
			classified += 1
		except Exception as exc:
			errors += 1
			print(f"[fetch-emails:new-workflow] Failed on {email.id}: {exc}")

	print("\n[fetch-emails] Summary:")
	print("  Status: ok" if errors == 0 else "  Status: partial")
	print("  Workflow: new")
	print("  Emails fetched: 0 (classification-only mode)")
	print(f"  Emails classified: {classified}")
	print(f"  Errors: {errors}")

	return 0 if errors == 0 else 1


def run(
	user_id: str,
	max_results: int = EMAIL_FETCH_MAX_RESULTS,
	classify_limit: int = 200,
	after_date: str = None,
	use_new_workflow: bool = False,
) -> int:
	"""Fetch emails from Gmail, classify them, and link to contacts/accounts.
	
	This is a thin wrapper around EmailRepository.fetch_and_process_emails().
	"""
	if use_new_workflow:
		try:
			return _run_new_workflow(user_id=user_id, classify_limit=classify_limit)
		except Exception as exc:
			print(f"[fetch-emails] New workflow failed, falling back to legacy: {exc}")

	repo = _get_legacy_repo()
	
	try:
		# Use the repository's comprehensive workflow method
		result = repo.fetch_and_process_emails(
			user_id=user_id,
			max_results=max_results,
			classify_limit=classify_limit,
			after_date=after_date,
			auto_resolve_date=True  # Enable smart date resolution if after_date not provided
		)
		
		# Print summary
		print(f"\n[fetch-emails] Summary:")
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
			print(f"\n[fetch-emails] Errors ({len(errors)}):")
			for err in errors[:5]:  # Show first 5 errors
				if isinstance(err, dict):
					print(f"  - {err}")
				else:
					print(f"  - {err}")
			if len(errors) > 5:
				print(f"  ... and {len(errors) - 5} more errors")
		
		return 0 if result.get('status') == 'ok' else 1
		
	except Exception as exc:
		print(f"[fetch-emails] Failed: {exc}")
		import traceback
		traceback.print_exc()
		return 1


def main(argv=None):
	parser = argparse.ArgumentParser(description="Fetch Gmail emails and classify unclassified ones.")
	parser.add_argument("--user-id", required=False, help="Supabase user ID")
	parser.add_argument("--max-results", type=int, default=EMAIL_FETCH_MAX_RESULTS, help="Max messages to fetch from Gmail")
	parser.add_argument("--classify-limit", type=int, default=200, help="Max unclassified emails to classify")
	parser.add_argument(
		"--after-date",
		type=str,
		default=None,
		help="Fetch emails after this date (YYYY/MM/DD or Unix seconds). Defaults to latest email timestamp (or yesterday if none).",
	)
	parser.add_argument(
		"--use-new-workflow",
		action="store_true",
		help="Use new DDD workflow for classification (opt-in, with legacy fallback).",
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
		use_new_workflow=args.use_new_workflow or default_use_new_workflow,
	)
	sys.exit(exit_code)


if __name__ == "__main__":
	main()
