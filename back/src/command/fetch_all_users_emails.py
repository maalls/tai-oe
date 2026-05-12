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
from datetime import datetime

from src.command.fetch_emails import run as run_fetch_emails




def main(argv=None):
	parser = argparse.ArgumentParser(description="Fetch Gmail emails for all authorized users.")
	parser.add_argument("--max-results", type=int, default=50, help="Max messages to fetch per user")
	parser.add_argument("--user-id", type=str, default=None, help="Optional: Fetch only for specific user")
	
	args = parser.parse_args(argv)
	
	from src.supabase import get_supabase_service
	
	print("\n" + "="*60)
	print("📧 Fetching Emails for All Users")
	print("="*60 + "\n")
	
	start_time = datetime.now()
	
	# Get users to fetch for
	if args.user_id:
		user_ids = [args.user_id]
		print(f"Fetching emails for specific user: {args.user_id}\n")
	else:
		# Get all users from profile table
		try:
			supabase = get_supabase_service()
			response = supabase.table("profile").select("id, email").execute()
			
			if response.data:
				user_ids = [user["id"] for user in response.data]
				print(f"Found {len(user_ids)} users:")
				for user in response.data:
					print(f"  - {user['email']} ({user['id']})")
			else:
				user_ids = []
		except Exception as e:
			print(f"Error getting users: {e}")
			return 1
		
		if not user_ids:
			print("❌ No users found")
			return 1
		
		print(f"\nFetching emails for {len(user_ids)} users...\n")
	
	# Fetch for each user
	results = []
	
	for i, user_id in enumerate(user_ids, 1):
		print(f"[{i}/{len(user_ids)}] Processing {user_id}...")
		
		exit_code = run_fetch_emails(user_id=user_id, max_results=args.max_results)
		results.append({
			"user_id": user_id,
			"status": "ok" if exit_code == 0 else "error",
			"exit_code": exit_code,
			"errors": [] if exit_code == 0 else ["fetch_emails failed"],
		})
		print()
	
	# Print summary
	print("\n" + "="*60)
	print("📊 Summary Report")
	print("="*60 + "\n")
	
	total_fetched = 0
	total_classified = 0
	total_contacts = 0
	total_accounts = 0
	total_errors = 0
	failed_users = []
	
	for result in results:
		status_icon = "✅" if result.get("status") == "ok" else "❌"
		print(f"{status_icon} {result['user_id']}")
		print(f"   Status: {result.get('status', 'unknown')}")
		print(f"   Exit code: {result.get('exit_code', 0)}")
		
		if result["errors"]:
			print(f"   Errors: {len(result['errors'])}")
			for error in result["errors"]:
				print(f"     - {error}")
			failed_users.append(result["user_id"])
			total_errors += len(result["errors"])
		print()
		
		total_fetched += 1
		# Aggregates not available from fetch_emails
	
	elapsed = (datetime.now() - start_time).total_seconds()
	
	print("="*60)
	print(f"✅ Successfully processed: {len(user_ids) - len(failed_users)}/{len(user_ids)} users")
	print(f"📧 Total emails classified: {total_classified}")
	print(f"👥 Total contacts created: {total_contacts}")
	print(f"🏢 Total accounts created: {total_accounts}")
	print(f"⏱️  Total time: {elapsed:.1f} seconds")
	
	if failed_users:
		print(f"❌ Failed users: {', '.join(failed_users)}")
		print(f"⚠️  Total errors: {total_errors}")
	
	print("="*60 + "\n")
	
	return 0 if len(failed_users) == 0 else 1


if __name__ == "__main__":
	sys.exit(main())
