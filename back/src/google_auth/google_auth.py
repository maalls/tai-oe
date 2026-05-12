"""
Base class for Google API authentication.
Provides shared OAuth2 authentication logic for Gmail, Drive, and other Google services.
"""

import pickle
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Default paths relative to project root
_DEFAULT_VAR_DIR = Path(__file__).parent.parent.parent / "var"
DEFAULT_CREDENTIALS_PATH = _DEFAULT_VAR_DIR / "credentials.json"
DEFAULT_TOKEN_PATH = _DEFAULT_VAR_DIR / "token.pickle"


class GoogleAPIClient:
    """Base class for Google API clients with OAuth2 authentication."""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        redirect_url: Optional[str] = None,
        token_bytes: Optional[bytes] = None,
        token_saver=None,
    ):
        """Initialize Google API client.

        Parameters
        ----------
        credentials_path : Optional[str]
            Path to OAuth2 credentials JSON file from Google Cloud Console.
            If None, uses var/credentials.json relative to project root.
        token_path : Optional[str]
            Path to store/load authentication token for reuse.
            If None, uses var/token.pickle relative to project root.
        scopes : Optional[List[str]]
            API scopes required. If None, uses combined Gmail + Drive scopes.
        redirect_url : Optional[str]
            URL to redirect to after successful OAuth authorization.
            If None, uses default localhost:5173
        """
        self.credentials_path = Path(credentials_path) if credentials_path else DEFAULT_CREDENTIALS_PATH
        self.token_path = Path(token_path) if token_path else DEFAULT_TOKEN_PATH
        self.scopes = scopes or [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        self.redirect_url = redirect_url or "http://localhost:5173"
        self.service = None
        self._token_bytes = token_bytes
        self._token_saver = token_saver

    def _persist_token(self, creds) -> None:
        if self._token_saver:
            try:
                self._token_saver(creds)
                return
            except Exception:
                pass

        with open(self.token_path, "wb") as token:
            pickle.dump(creds, token)

    def authenticate(self, service_name: str, version: str) -> None:
        """Authenticate with Google API using OAuth2.

        Parameters
        ----------
        service_name : str
            Google service name (e.g., 'gmail', 'drive')
        version : str
            API version (e.g., 'v1', 'v3')
        """
        creds = None

        # Load token from bytes or file if it exists
        if self._token_bytes:
            try:
                creds = pickle.loads(self._token_bytes)
            except Exception:
                creds = None
        elif self.token_path.exists():
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)

        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._persist_token(creds)
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Please download OAuth2 credentials from Google Cloud Console:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Enable the required APIs (Gmail, Drive, etc.)\n"
                        "3. Create OAuth2 credentials (Desktop app)\n"
                        "4. Download and save to var/credentials.json"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.scopes
                )
                
                # Custom success message with auto-redirect to frontend
                success_message = f"""
                <html>
                <head>
                    <title>Authorization Successful</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 400px;
                        }}
                        h1 {{
                            color: #10b981;
                            margin: 0 0 10px 0;
                            font-size: 24px;
                        }}
                        p {{
                            color: #6b7280;
                            margin: 10px 0;
                            line-height: 1.5;
                        }}
                        .checkmark {{
                            width: 60px;
                            height: 60px;
                            margin: 0 auto 20px;
                            border-radius: 50%;
                            background: #10b981;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 36px;
                            color: white;
                        }}
                    </style>
                    <script>
                        // Attempt to close the window
                        window.close();
                    </script>
                </head>
                <body>
                    <div class="container">
                        <div class="checkmark">✓</div>
                        <h1>Authorization Successful!</h1>
                        <p>Gmail permissions have been granted.</p>
                        <p style="font-size: 14px;">You can close this window now.</p>
                    </div>
                </body>
                </html>
                """
                
                creds = flow.run_local_server(port=0, success_message=success_message)

            # Save credentials for next run
            self._persist_token(creds)

        self.service = build(service_name, version, credentials=creds)
