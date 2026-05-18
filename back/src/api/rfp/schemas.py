"""Pydantic schemas for FastAPI RFP endpoints."""

from pydantic import BaseModel


class RfpQuery(BaseModel):
    rfp_id: str | None = None


class RfpSubmitRequest(BaseModel):
    rfp_id: str
