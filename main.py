"""
Code Submission Module — FastAPI entry point
============================================

Run locally:
    uvicorn main:app --reload

Interactive docs:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.submit import router as submit_router


app = FastAPI(
    title="Code Submission Module",
    version="1.0.0",
    description=(
        "Accepts Python (.py) or Java (.java) code — either as a JSON body "
        "or as an uploaded file — and validates it structurally before "
        "returning a detailed JSON report."
    ),
    contact={"name": "Code Submission API"},
    license_info={"name": "MIT"},
)

# Allow all origins during local development; tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(submit_router, tags=["Code Submission"])


@app.get("/", tags=["Health"])
async def health_check() -> dict:
    """Quick health-check endpoint."""
    return {"status": "ok", "service": "Code Submission Module"}
