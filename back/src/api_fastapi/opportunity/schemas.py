"""Pydantic schemas for FastAPI opportunity endpoints."""

from pydantic import BaseModel


class OpportunityQuery(BaseModel):
    opportunity_id: str | None = None


class OpportunityAdvanceQuery(BaseModel):
    opportunity_id: str | None = None
    stage: str | None = None


class OpportunityAdvanceRequest(BaseModel):
    opportunity_id: str
    stage: str
