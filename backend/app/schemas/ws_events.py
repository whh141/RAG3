from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AskEvent(BaseModel):
    action: Literal["ask"]
    request_id: str
    query: str
    model_provider: Literal["zhipuai", "openai"] = "zhipuai"
    agent_mode: Literal["baseline_rag", "agentic_rag"] = "agentic_rag"


class AgentStateEvent(BaseModel):
    type: Literal["agent_state"] = "agent_state"
    request_id: str
    trace_id: str
    node: str
    status: str
    summary: str
    extra: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class ChunkEvent(BaseModel):
    type: Literal["chunk"] = "chunk"
    request_id: str
    trace_id: str
    content: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    request_id: str
    trace_id: str
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    latency_ms: int


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    request_id: str
    trace_id: str
    message: str
    code: str
