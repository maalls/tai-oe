#!/usr/bin/env python3
"""
Quick helper to regenerate Google OAuth token.

Usage:
    python -m src.command.regenerate_google_token              # Gmail token (default)
    python -m src.command.regenerate_google_token --type drive # Google Drive token
"""

import argparse
import sys
from pathlib import Path

BACK_DIR = Path(__file__).resolve().parents[2]

def regenerate_gmail_token():
    """Regenerate Gmail token."""
    from src.google_auth.google_auth import GoogleAPIClient
    
    print("[Gmail Token Regeneration]")
    print("Deleting old token...")
    var_dir = BACK_DIR / "var"
    token_path = var_dir / "token.pickle"
    
    if token_path.exists():
        token_path.unlink()
        print(f"✓ Deleted {token_path}")
    else:
        print(f"  (token not found at {token_path})")
    
    print("\nStarting OAuth flow... A browser window should open.")
    print("Follow the Google login prompts to authorize Gmail access.\n")
    
    try:
        client = GoogleAPIClient()
        client.authenticate('gmail', 'v1')
        print("\n✅ Gmail token regenerated successfully!")
        print(f"   Token saved to: {token_path}")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Ensure credentials.json is at var/credentials.json")
        print("3. Make sure credentials are a valid OAuth client (Desktop app)")
        print("4. Try running again and complete the browser login")
        return 1


def regenerate_drive_token():
    """Regenerate Google Drive token."""
    print("[Google Drive Token Regeneration]")
    print("Deleting old token...")
    var_dir = BACK_DIR / "var" / "gdrive"
    token_path = var_dir / "token.json"
    
    if token_path.exists():
        token_path.unlink()
        print(f"✓ Deleted {token_path}")
    else:
        print(f"  (token not found at {token_path})")
    
    print("\nStarting OAuth flow... A browser window should open.")
    print("Follow the Google login prompts to authorize Drive access.\n")
    
    try:
        from src.google_drive.gdrive_tool import get_credentials
        creds = get_credentials()
        print("\n✅ Google Drive token regenerated successfully!")
        print(f"   Token saved to: {token_path}")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Ensure credentials.json is at var/gdrive/credentials.json")
        print("3. Make sure credentials are a valid OAuth client (Desktop app)")
        print("4. Try running again and complete the browser login")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate Google OAuth tokens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.command.regenerate_google_token              # Regenerate Gmail token
    python -m src.command.regenerate_google_token --type drive # Regenerate Drive token
        """
    )
    parser.add_argument(
        "--type",
        choices=["gmail", "drive"],
        default="gmail",
        help="Token type to regenerate (default: gmail)"
    )
    
    args = parser.parse_args()
    
    if args.type == "gmail":
        exit_code = regenerate_gmail_token()
    else:
        exit_code = regenerate_drive_token()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
