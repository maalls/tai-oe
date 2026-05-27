"""FastAPI CSV router."""

from datetime import date, datetime
from decimal import Decimal
import json

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import JSONResponse, Response

from src.api.authz.route_access import build_route_access_dependency
from src.api.dependencies import get_database_repository, get_file_handler
from src.repository.repository import DatabaseRepository
from src.service.csv.file_service import CsvFileService

router = APIRouter(tags=["csv"])


def _serialize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_row(row: dict) -> dict:
    return {key: _serialize_value(value) for key, value in row.items()}

_csv_access = build_route_access_dependency(
    route_key="csv.access",
    unauthorized_body={"error": "Unauthorized"},
    forbidden_body={"error": "Forbidden"},
)


@router.get("/api/csv/sources")
def csv_sources(
    requester_id: str | JSONResponse = Depends(_csv_access),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    return JSONResponse(file_handler.list_sources(), status_code=200)


@router.get("/api/csv/files")
def csv_files(
    source: str = Query(...),
    requester_id: str | JSONResponse = Depends(_csv_access),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    return JSONResponse({"files": file_handler.list_files_for_source(source)}, status_code=200)


@router.get("/api/csv/preview")
def csv_preview(
    source: str = Query(...),
    file: str = Query(...),
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    filter: str | None = Query(default=None),
    requester_id: str | JSONResponse = Depends(_csv_access),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    try:
        filters = json.loads(filter) if filter else None
        if filters is not None and not isinstance(filters, dict):
            raise ValueError("filter must be a JSON object")

        target = file_handler.safe_file_from_query(source, file)
        result = file_handler.csv_reader.read(
            target,
            offset=max(0, offset),
            limit=max(1, min(limit, 1000)),
            filters=filters,
        )
        return JSONResponse(result, status_code=200)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": f"Preview failed: {exc}"}, status_code=500)


@router.get("/api/csv/source")
def csv_source_download(
    source: str = Query(...),
    requester_id: str | JSONResponse = Depends(_csv_access),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    try:
        content = file_handler.read_source_file(source)
        ext = source.lower().split(".")[-1] if "." in source else ""
        content_type_map = {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
        }
        content_type = content_type_map.get(ext, "application/octet-stream")
        return Response(
            content=content,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{source}"'},
        )
    except Exception as exc:
        return JSONResponse({"error": f"Error streaming source: {exc}"}, status_code=500)


@router.get("/api/csv/raw")
def csv_raw(
    file: str = Query(...),
    source: str = Query(default=""),
    requester_id: str | JSONResponse = Depends(_csv_access),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    try:
        csv_path = file_handler.safe_file_from_query(source, file)
        return Response(
            content=csv_path.read_bytes(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{file}"'},
        )
    except Exception as exc:
        return JSONResponse({"error": f"Error streaming CSV: {exc}"}, status_code=500)


@router.get("/api/csv/download")
def csv_download(
    source: str = Query(...),
    file: str = Query(...),
    requester_id: str | JSONResponse = Depends(_csv_access),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    try:
        csv_path = file_handler.safe_file_from_query(source, file)
        return Response(
            content=csv_path.read_bytes(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{file}"'},
        )
    except Exception as exc:
        return JSONResponse({"error": f"Error streaming CSV: {exc}"}, status_code=500)


@router.get("/api/csv/query")
def csv_query(
    table: str | None = Query(default=None),
    tables: str | None = Query(default=None),
    columns: str = Query(default="*"),
    where: str = Query(default=""),
    sortBy: str = Query(default=""),
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    requester_id: str | JSONResponse = Depends(_csv_access),
    database_repository: DatabaseRepository = Depends(get_database_repository),
):
    try:
        if isinstance(requester_id, JSONResponse):
            return requester_id

        if tables is not None:
            rows = database_repository.list_public_tables_with_columns()
            tables_map: dict[str, dict] = {}
            for row in rows:
                table_name = row["table_name"]
                if table_name not in tables_map:
                    tables_map[table_name] = {"name": table_name, "columns": []}
                if row.get("column_name"):
                    tables_map[table_name]["columns"].append(
                        {
                            "name": row["column_name"],
                            "type": row["data_type"],
                            "nullable": row["is_nullable"] == "YES",
                            "default": row["column_default"],
                            "max_length": row["character_maximum_length"],
                            "precision": row["numeric_precision"],
                            "scale": row["numeric_scale"],
                        }
                    )
            return JSONResponse({"tables": list(tables_map.values())}, status_code=200)

        if not table:
            return JSONResponse({"error": "Missing 'table' parameter"}, status_code=400)

        rows = database_repository.query_table(
            table=table,
            columns_raw=columns,
            where_clause=where,
            sort_by=sortBy,
            limit=max(1, min(limit, 1000)),
            offset=max(0, offset),
        )
        serialized_rows = [_serialize_row(row) for row in rows]
        payload = {
            "columns": list(serialized_rows[0].keys()) if serialized_rows else [],
            "rows": serialized_rows,
            "count": len(serialized_rows),
            "offset": max(0, offset),
            "limit": max(1, min(limit, 1000)),
        }
        return JSONResponse(payload, status_code=200)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@router.post("/api/csv/source")
async def csv_source_upload(
    file: UploadFile = File(...),
    requester_id: str | JSONResponse = Depends(_csv_access),
    file_handler: CsvFileService = Depends(get_file_handler),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    try:
        file_data = await file.read()
        result = file_handler.handle_uploaded_file(filename=file.filename or "", file_data=file_data)
        return JSONResponse(result, status_code=200)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": f"Upload failed: {exc}"}, status_code=500)
