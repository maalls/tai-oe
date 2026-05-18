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


class OpportunitySearchQuery(BaseModel):
    source_reference_id: str | None = None
    name: str | None = None


class OpportunityCreateManualRequest(BaseModel):
    name: str


class OpportunityCreateFromEmailRequest(BaseModel):
    message_id: str


class OpportunityUpdateNameRequest(BaseModel):
    name: str


class OpportunityExtractAuthorContactRequest(BaseModel):
    from_email: str
    from_name: str | None = None
