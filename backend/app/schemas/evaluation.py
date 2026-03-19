from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class StartEvalRequest(BaseModel):
    name: str
    dataset_name: str
    question_count: int = 100
    model_provider: Literal["zhipuai", "openai"] = "zhipuai"


class EvalRunDTO(BaseModel):
    id: str
    name: str
    dataset_name: str
    status: str
    question_count: int
    created_at: datetime
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class EvalRecordDTO(BaseModel):
    id: str
    question: str
    reference_answer: str | None = None
    baseline_answer: str | None = None
    agent_answer: str | None = None
    baseline_latency_ms: int | None = None
    agent_latency_ms: int | None = None
    baseline_score: float | None = None
    agent_score: float | None = None
    route_expected: str | None = None
    route_actual: str | None = None
    route_correct: bool

    model_config = {"from_attributes": True}
