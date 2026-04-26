from typing import Any
from pydantic import BaseModel, Field
from groq import BaseModel


class AskPayload(BaseModel):
    student_metrics: dict[str, Any] | None = None
    question: str = Field(..., min_length=1)