"""
POST /submit-code  — Code Submission Router
============================================

Accepts code in **two mutually exclusive ways**:

1. **JSON body** (Content-Type: application/json)
   ```json
   { "code": "<source>", "language": "python" | "java" }
   ```

2. **File upload** (Content-Type: multipart/form-data)
   - Field name : ``file``
   - Accepted extensions: ``.py`` (Python) or ``.java`` (Java)

Only one of the two inputs must be provided per request.  Providing both
or neither results in a 422 error.
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from models.schemas import CodeSubmissionRequest, ValidationResult
from validators.java_validator import validate_java
from validators.python_validator import validate_python


router = APIRouter()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB
_EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".java": "java",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_validation(
    code: str,
    language: str,
    source: str,
    filename: str | None = None,
) -> ValidationResult:
    """Dispatch to the correct validator and build a ValidationResult."""
    if language == "python":
        result = validate_python(code)
    elif language == "java":
        result = validate_java(code, filename=filename)
    else:
        # Should never reach here — guarded upstream.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported language '{language}'. Supported: python, java.",
        )

    return ValidationResult(
        valid=result.valid,
        language=language,
        source=source,
        filename=filename,
        message="Code is valid." if result.valid else "Validation failed.",
        errors=result.errors,
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/submit-code",
    response_model=ValidationResult,
    summary="Submit code for validation",
    description=(
        "Accepts either a JSON body `{code, language}` **or** a `.py`/`.java` "
        "file upload and returns a structured validation result."
    ),
    responses={
        200: {"description": "Code accepted and validated (may still be invalid)."},
        400: {"description": "Bad request — missing input or unsupported file type."},
        413: {"description": "Uploaded file exceeds the 1 MB size limit."},
        422: {"description": "Request body failed schema validation."},
    },
)
async def submit_code(request: Request) -> JSONResponse:
    """
    Unified handler that inspects the incoming Content-Type and delegates
    to JSON body parsing **or** multipart file parsing accordingly.
    """
    content_type: str = request.headers.get("content-type", "")

    # ------------------------------------------------------------------ #
    # Branch A — JSON body submission
    # ------------------------------------------------------------------ #
    if "application/json" in content_type:
        try:
            raw = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is not valid JSON.",
            )

        # Validate with Pydantic; re-raise validation errors as 422.
        try:
            payload = CodeSubmissionRequest.model_validate(raw)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=json.loads(exc.json()) if hasattr(exc, "json") else str(exc),
            )

        validation = _run_validation(
            code=payload.code,
            language=payload.language,
            source="body",
        )
        status_code = status.HTTP_200_OK if validation.valid else status.HTTP_200_OK
        return JSONResponse(content=validation.model_dump(), status_code=status_code)

    # ------------------------------------------------------------------ #
    # Branch B — Multipart file upload
    # ------------------------------------------------------------------ #
    if "multipart/form-data" in content_type:
        form = await request.form()
        file: UploadFile | None = form.get("file")  # type: ignore[assignment]

        if file is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file field found in the multipart form. Use field name 'file'.",
            )

        filename: str = file.filename or ""
        # Determine language from extension.
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        language = _EXTENSION_TO_LANGUAGE.get(ext)

        if language is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type '{ext or '(no extension)'}'. "
                    "Only .py (Python) and .java (Java) files are accepted."
                ),
            )

        # Read file content with size guard.
        raw_bytes = await file.read()
        if len(raw_bytes) > _MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File size {len(raw_bytes):,} bytes exceeds the "
                    f"{_MAX_FILE_SIZE_BYTES:,}-byte (1 MB) limit."
                ),
            )

        try:
            code = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be UTF-8 encoded text.",
            )

        if not code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        validation = _run_validation(
            code=code,
            language=language,
            source="file",
            filename=filename,
        )
        return JSONResponse(content=validation.model_dump(), status_code=status.HTTP_200_OK)

    # ------------------------------------------------------------------ #
    # Neither JSON nor multipart → explain how to use the endpoint
    # ------------------------------------------------------------------ #
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Unsupported Content-Type. "
            "Send 'application/json' for pasted code or "
            "'multipart/form-data' with a 'file' field for file upload."
        ),
    )
