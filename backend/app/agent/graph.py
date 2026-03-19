import uuid
from datetime import datetime, timezone

from app.agent.state import AgentRunState, NodeTrace
from app.schemas.ws_events import AgentStateEvent, ChunkEvent, DoneEvent


class SimpleAgentGraph:
    """A bootstrap agent runtime that mimics the future LangGraph workflow."""

    async def run(self, session_id: str, request_id: str, query: str):
        trace_id = str(uuid.uuid4())
        state = AgentRunState(
            trace_id=trace_id,
            session_id=session_id,
            query=query,
            normalized_query=query.strip(),
        )

        trace = NodeTrace(
            node_name="router",
            status="completed",
            summary="当前骨架版本默认路由到本地知识库模式。",
            finished_at=datetime.now(timezone.utc),
            extra={"route": state.route, "query_type": state.query_type},
        )
        state.node_history.append(trace)
        yield AgentStateEvent(
            request_id=request_id,
            trace_id=trace_id,
            node="router",
            status="completed",
            summary=trace.summary,
            extra=trace.extra,
            timestamp=datetime.now(timezone.utc),
        )

        answer = f"[bootstrap] 已收到问题：{query}。当前工程已打通 WebSocket 骨架，下一步将接入真实检索与生成链路。"
        state.final_answer = answer
        state.citations = []
        yield ChunkEvent(request_id=request_id, trace_id=trace_id, content=answer)
        yield DoneEvent(
            request_id=request_id,
            trace_id=trace_id,
            answer=answer,
            citations=state.citations,
            latency_ms=1,
        )
