from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from kira_server.tooling.results import tool_error, tool_success


class QuestionField(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    required: bool = False


class AskUserQuestionInput(BaseModel):
    question: str = Field(min_length=1)
    fields: list[QuestionField] = Field(default_factory=list)


def ask_user_question_tool(question: str, fields: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not question.strip():
        return tool_error(code="validation_error", message="question must not be empty")
    parsed_fields = []
    for field in fields or []:
        try:
            parsed_fields.append(QuestionField.model_validate(field).model_dump())
        except Exception as exc:
            return tool_error(
                code="validation_error",
                message="question field is invalid",
                metadata={"error": str(exc)},
            )
    question_id = f"question-{uuid4().hex}"
    return tool_success(
        code="question_pending",
        message="Question is pending human input",
        data={"status": "pending", "question_id": question_id, "question": question, "fields": parsed_fields},
        metadata={"question_id": question_id, "stage": "stage-02-placeholder"},
    )
