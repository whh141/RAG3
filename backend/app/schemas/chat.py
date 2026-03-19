from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str | None = None
    model_provider: Literal["zhipuai", "openai"] = "zhipuai"
    agent_mode: Literal["baseline_rag", "agentic_rag"] = "agentic_rag"


class CreateSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime


class SessionDTO(BaseModel):
    id: str
    title: str
    description: str | None = None
    model_provider: str
    agent_mode: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None

    model_config = {"from_attributes": True}


class CitationDTO(BaseModel):
    source_type: str
    source_name: str
    chunk_id: str | None = None
    score: float | None = None
    url: str | None = None


class MessageDTO(BaseModel):
    id: str
    role: Literal["system", "user", "assistant"]
    content: str
    content_format: str
    message_status: str
    citations: list[CitationDTO] = Field(default_factory=list)
    trace_id: str | None = None
    latency_ms: int | None = None
    created_at: datetime
