from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from config import CV_VERSIONS, CV_LANGUAGES
from database import init_db, save_history, list_history, get_pdf, delete_history
from models import AnalyzeRequest, FinalizeRequest
from services import load_cv, analyze_cv, apply_changes, generate_pdf


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CV Adapter", lifespan=lifespan)


@app.get("/api/versions")
async def versions():
    return {"versions": CV_VERSIONS, "languages": CV_LANGUAGES}


@app.get("/api/cv/{version}/{language}")
async def get_cv(version: str, language: str):
    if version not in CV_VERSIONS:
        raise HTTPException(400, f"Invalid version. Available: {CV_VERSIONS}")
    if language not in CV_LANGUAGES:
        raise HTTPException(400, f"Invalid language. Available: {CV_LANGUAGES}")
    data = load_cv(version)
    return data.get(language, {})


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    if request.version not in CV_VERSIONS:
        raise HTTPException(400, f"Invalid version. Available: {CV_VERSIONS}")
    if request.language not in CV_LANGUAGES:
        raise HTTPException(400, f"Invalid language. Available: {CV_LANGUAGES}")

    cv_data = load_cv(request.version)
    result = await analyze_cv(cv_data, request.language, request.job_description)
    return result.model_dump()


@app.post("/api/finalize")
async def finalize(request: FinalizeRequest):
    merged_data = apply_changes(
        request.original_data,
        request.adapted_data,
        request.language,
        request.accepted_paths,
    )

    try:
        pdf_bytes = await generate_pdf(merged_data, request.language)
    except Exception as e:
        raise HTTPException(502, f"PDF generation failed: {e}")

    record_id = save_history(
        cv_version=request.version,
        language=request.language,
        job_title=request.job_title,
        job_description=request.job_description,
        original_data=request.original_data,
        adapted_data=request.adapted_data,
        changes=[c.model_dump() for c in request.changes],
        accepted_paths=request.accepted_paths,
        pdf_blob=pdf_bytes,
        company_name=request.company_name,
        position_title=request.position_title,
        application_date=request.application_date,
        offer_link=request.offer_link,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cv_adapted_{record_id[:8]}.pdf"',
            "X-History-Id": record_id,
        },
    )


@app.get("/api/history")
async def history():
    return list_history()


@app.get("/api/history/{record_id}/pdf")
async def history_pdf(record_id: str):
    pdf_bytes = get_pdf(record_id)
    if not pdf_bytes:
        raise HTTPException(404, "Record not found")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="cv_{record_id[:8]}.pdf"'},
    )


@app.delete("/api/history/{record_id}")
async def delete_history_record(record_id: str):
    if not delete_history(record_id):
        raise HTTPException(404, "Record not found")
    return {"ok": True}


@app.get("/")
async def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
