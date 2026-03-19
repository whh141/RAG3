from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.agent.graph import SimpleAgentGraph
from app.db.session import get_db
from app.services.chat_service import ChatService

router = APIRouter()


@router.websocket("/ws/chat/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)) -> None:
    await websocket.accept()
    chat_service = ChatService(db)
    if not chat_service.get_session(session_id):
        await websocket.send_json({"type": "error", "message": "Session not found", "code": "SESSION_NOT_FOUND"})
        await websocket.close()
        return

    graph = SimpleAgentGraph()

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("action") != "ask":
                await websocket.send_json({"type": "error", "message": "Unsupported action", "code": "INVALID_ACTION"})
                continue

            query = str(payload.get("query", "")).strip()
            request_id = str(payload.get("request_id", "request-unknown"))
            if not query:
                await websocket.send_json({"type": "error", "message": "Query is required", "code": "EMPTY_QUERY"})
                continue

            chat_service.add_message(session_id, role="user", content=query)
            final_answer = ""
            trace_id = None
            citations: list[dict] = []

            async for event in graph.run(session_id=session_id, request_id=request_id, query=query):
                data = event.model_dump(mode="json")
                trace_id = data.get("trace_id", trace_id)
                if data.get("type") == "chunk":
                    final_answer += data["content"]
                if data.get("type") == "done":
                    citations = data.get("citations", [])
                await websocket.send_json(data)

            chat_service.add_message(
                session_id,
                role="assistant",
                content=final_answer,
                citations=citations,
                trace_id=trace_id,
                latency_ms=1,
            )
    except WebSocketDisconnect:
        return
