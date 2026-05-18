from pathlib import Path

from src.api.file.handler import FileHandler
from src.lib.readers.csv import CSVReader


def _multipart_body(boundary: str, filename: str, content_type: str, content: bytes) -> bytes:
    header = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
    ).encode("utf-8")
    return header + content + f"\r\n--{boundary}--".encode("utf-8")


def test_upload_csv_saves_file_in_storage(tmp_path: Path):
    file_handler = FileHandler(storage_dir=tmp_path, csv_reader=CSVReader())
    boundary = "----pytest-boundary"
    file_content = b"name,value\ntest1,100\ntest2,200"

    body = _multipart_body(
        boundary=boundary,
        filename="test_upload.csv",
        content_type="text/csv",
        content=file_content,
    )

    result = file_handler.handle_file_upload(
        content_type=f"multipart/form-data; boundary={boundary}",
        content_length=len(body),
        body=body,
    )

    assert result["status"] == "ok"
    saved_path = Path(result["path"])
    assert saved_path.exists()
    assert saved_path.read_bytes() == file_content
