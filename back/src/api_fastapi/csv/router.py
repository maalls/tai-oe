"""FastAPI CSV router for source upload endpoint."""

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from src.api_fastapi.dependencies import get_file_handler
from src.service.csv.file_service import CsvFileService

router = APIRouter(tags=["csv"])


@router.post("/api/csv/source")
async def csv_source_upload(
    file: UploadFile = File(...),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    try:
        file_data = await file.read()
        result = file_handler.handle_uploaded_file(filename=file.filename or "", file_data=file_data)
        return JSONResponse(result, status_code=200)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": f"Upload failed: {exc}"}, status_code=500)
