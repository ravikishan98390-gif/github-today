from pydantic import BaseModel, field_validator
from typing import Literal, Optional


SUPPORTED_LANGUAGES = {"python", "java"}


class CodeSubmissionRequest(BaseModel):
    """Request body for pasted code submission."""

    code: str
    language: Literal["python", "java"]

    @field_validator("code")
    @classmethod
    def code_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code must not be empty or whitespace only")
        return v


class ValidationResult(BaseModel):
    """Outcome of a single validation pass."""

    valid: bool
    language: str
    source: Literal["body", "file"]
    filename: Optional[str] = None
    message: str
    errors: list[str] = []
