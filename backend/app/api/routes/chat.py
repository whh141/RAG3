import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import CreateSessionRequest, CreateSessionResponse, MessageDTO, SessionDTO
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/session", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: CreateSessionRequest, db: Session = Depends(get_db)) -> CreateSessionResponse:
    session = ChatService(db).create_session(payload)
    return CreateSessionResponse(session_id=session.id, title=session.title, created_at=session.created_at)


@router.get("/sessions", response_model=list[SessionDTO])
def list_sessions(db: Session = Depends(get_db)) -> list[SessionDTO]:
    return ChatService(db).list_sessions()


@router.get("/{session_id}/history", response_model=list[MessageDTO])
def get_history(session_id: str, db: Session = Depends(get_db)) -> list[MessageDTO]:
    service = ChatService(db)
    if not service.get_session(session_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = []
    for message in service.list_messages(session_id):
        messages.append(
            MessageDTO(
                id=message.id,
                role=message.role,
                content=message.content,
                content_format=message.content_format,
                message_status=message.message_status,
                citations=json.loads(message.citations_json or "[]"),
                trace_id=message.trace_id,
                latency_ms=message.latency_ms,
                created_at=message.created_at,
            )
        )
    return messages


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    deleted = ChatService(db).delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"message": "Session deleted"}
