from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    version: str
    language: str
    job_description: str


class Change(BaseModel):
    section: str
    field_path: str
    original_value: Any
    adapted_value: Any
    reason: str


class AnalyzeResponse(BaseModel):
    job_title: str
    original_data: dict[str, Any]
    adapted_data: dict[str, Any]
    changes: list[Change]


class FinalizeRequest(BaseModel):
    version: str
    language: str
    job_description: str
    job_title: str
    original_data: dict[str, Any]
    adapted_data: dict[str, Any]
    changes: list[Change]
    accepted_paths: list[str]
    company_name: str | None = None
    position_title: str | None = None
    application_date: str | None = None
    offer_link: str | None = None
