from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class NodeTrace:
    node_name: str
    status: str
    summary: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentRunState:
    trace_id: str
    session_id: str
    query: str
    normalized_query: str
    query_type: str = "unknown"
    route: str = "local_rag"
    route_reason: str = "默认走本地知识库检索"
    retrieved_chunks: list[dict[str, Any]] = field(default_factory=list)
    web_results: list[dict[str, Any]] = field(default_factory=list)
    selected_evidence: list[dict[str, Any]] = field(default_factory=list)
    compressed_context: str = ""
    final_answer: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)
    node_history: list[NodeTrace] = field(default_factory=list)
    error: str | None = None
