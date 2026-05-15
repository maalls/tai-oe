#!/usr/bin/env python3
"""
Google Drive file downloader using the Google Drive API.
Supports Sheets, Docs, Slides, and other file types with proper authentication.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs
import io

from src.infrastructure.clients.oauth.google_client import GoogleAPIClient

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError


class GoogleDriveDownloader(GoogleAPIClient):
    """Download Google Sheets, Docs, Slides, etc. using the Google Drive API."""

    # MIME type mappings for export
    EXPORT_MIMES = {
        "spreadsheet": {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
            "ods": "application/vnd.oasis.opendocument.spreadsheet",
            "pdf": "application/pdf",
        },
        "document": {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
            "odt": "application/vnd.oasis.opendocument.text",
            "txt": "text/plain",
        },
        "presentation": {
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "pdf": "application/pdf",
            "odp": "application/vnd.oasis.opendocument.presentation",
        },
        "drawing": {
            "png": "image/png",
            "pdf": "application/pdf",
            "svg": "image/svg+xml",
            "jpg": "image/jpeg",
        },
    }

    # Default export formats
    DEFAULT_FORMATS = {
        "spreadsheet": "xlsx",
        "document": "docx",
        "presentation": "pptx",
        "drawing": "png",
    }

    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """Initialize Google Drive downloader with OAuth2 authentication.

        Parameters
        ----------
        credentials_path : Optional[str]
            Path to OAuth2 credentials JSON from Google Cloud Console.
            If None, uses var/credentials.json relative to project root.
        token_path : Optional[str]
            Path to store/load authentication token.
            If None, uses var/token.pickle relative to project root.
        """
        super().__init__(credentials_path, token_path)
        self.authenticate()

    def authenticate(self) -> None:
        """Authenticate with Google Drive API using OAuth2."""
        super().authenticate("drive", "v3")

    def extract_file_id(self, url: str) -> Optional[str]:
        """Extract Google file ID from various URL formats.

        Supports:
        - https://docs.google.com/spreadsheets/d/{FILE_ID}/edit...
        - https://docs.google.com/document/d/{FILE_ID}/edit...
        - https://docs.google.com/presentation/d/{FILE_ID}/edit...
        - https://drive.google.com/file/d/{FILE_ID}/view
        - https://drive.google.com/open?id={FILE_ID}

        Parameters
        ----------
        url : str
            Google Docs/Drive URL

        Returns
        -------
        Optional[str]
            File ID if found, else None
        """
        # Pattern 1: docs.google.com/TYPE/d/{FILE_ID}/edit...
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if match:
            return match.group(1)

        # Pattern 2: drive.google.com/open?id={FILE_ID}
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "id" in params:
            return params["id"][0]

        return None

    def get_file_type(self, file_id: str) -> Optional[str]:
        """Determine Google file type from API.

        Returns one of: "spreadsheet", "document", "presentation", "drawing"
        """
        try:
            file = self.service.files().get(fileId=file_id, fields="mimeType").execute()
            mime = file.get("mimeType", "")

            if "spreadsheet" in mime:
                return "spreadsheet"
            elif "document" in mime:
                return "document"
            elif "presentation" in mime:
                return "presentation"
            elif "drawing" in mime:
                return "drawing"
        except HttpError:
            pass

        return None

    def download(
        self,
        url: str,
        output_path: Optional[str] = None,
        format_type: Optional[str] = None,
    ) -> Path:
        """Download a Google file from URL.

        Supports both native Google files (export) and uploaded files (download).

        Parameters
        ----------
        url : str
            Google Docs/Drive URL
        output_path : Optional[str]
            Where to save the file. If None, uses file name from Drive.
        format_type : Optional[str]
            Export format ("xlsx" for sheets, "docx" for docs, etc.).
            Only used for native Google files. Ignored for uploaded files.

        Returns
        -------
        Path
            Path to downloaded file

        Raises
        ------
        ValueError
            If file ID cannot be extracted or file type unknown
        HttpError
            If download fails
        """
        file_id = self.extract_file_id(url)
        if not file_id:
            raise ValueError(f"Could not extract file ID from URL: {url}")

        # Get file metadata
        file_metadata = self.service.files().get(fileId=file_id, fields="name,mimeType").execute()
        file_name = file_metadata.get("name", file_id)
        mime_type = file_metadata.get("mimeType", "")

        # Determine output path
        if output_path is None:
            output_path = Path("var/downloads") / file_name
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        try:
            is_native_google = "google-apps" in mime_type

            if is_native_google:
                # Native Google file - need to export to requested format
                file_type = self.get_file_type(file_id)
                if not file_type:
                    raise ValueError(f"Could not determine file type for: {file_id}")

                # Determine export format
                if format_type is None:
                    format_type = self.DEFAULT_FORMATS.get(file_type, "xlsx")

                if file_type not in self.EXPORT_MIMES or format_type not in self.EXPORT_MIMES[file_type]:
                    raise ValueError(f"Unsupported format: {format_type} for {file_type}")

                export_mime = self.EXPORT_MIMES[file_type][format_type]

                # Export native Google file
                request = self.service.files().export(fileId=file_id, mimeType=export_mime)
                file_data = io.BytesIO()
                downloader = MediaIoBaseDownload(file_data, request)

                done = False
                while not done:
                    _, done = downloader.next_chunk()

                content = file_data.getvalue()
            else:
                # Uploaded file - download original
                request = self.service.files().get_media(fileId=file_id)
                file_data = io.BytesIO()
                downloader = MediaIoBaseDownload(file_data, request)

                done = False
                while not done:
                    _, done = downloader.next_chunk()

                content = file_data.getvalue()

            # Write to disk
            with open(output_path, "wb") as f:
                f.write(content)

            return output_path
        except HttpError as error:
            raise error

    def download_sheets_as_csv(self, url: str, sheet_name: Optional[int] = None, output_path: Optional[str] = None) -> Path:
        """Download a Google Sheet as CSV.

        Parameters
        ----------
        url : str
            Google Sheets URL
        sheet_name : Optional[int]
            Sheet index (0-based). If None, downloads first sheet.
        output_path : Optional[str]
            Where to save the CSV file

        Returns
        -------
        Path
            Path to downloaded CSV file
        """
        return self.download(url, output_path=output_path, format_type="csv")


def main():
    """Command-line interface for Google Drive downloader."""
    parser = argparse.ArgumentParser(
        description="Download files from Google Drive (Sheets, Docs, etc.)"
    )
    parser.add_argument(
        "url",
        help="Google Drive file URL"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: var/downloads/<filename>)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["xlsx", "csv", "docx", "pdf", "txt", "pptx", "png"],
        help="Export format (for native Google files only)"
    )

    args = parser.parse_args()

    print("🚀 Initializing Google Drive downloader...")
    downloader = GoogleDriveDownloader()

    print(f"\n📄 Extracting file ID from URL...")
    file_id = downloader.extract_file_id(args.url)
    if not file_id:
        print(f"❌ Could not extract file ID from URL: {args.url}")
        return 1

    print(f"   File ID: {file_id}")

    file_type = downloader.get_file_type(file_id)
    if file_type:
        print(f"   File type: {file_type}")

    try:
        print(f"\n📥 Downloading...")
        file_path = downloader.download(
            args.url,
            output_path=args.output,
            format_type=args.format
        )
        print(f"   ✅ Saved to: {file_path}")
        print(f"   📊 Size: {file_path.stat().st_size / 1024:.1f} KB")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
