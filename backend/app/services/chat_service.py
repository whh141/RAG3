import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.chat import ChatMessage, ChatSession
from app.schemas.chat import CreateSessionRequest


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(self, payload: CreateSessionRequest) -> ChatSession:
        title = payload.title or "新建会话"
        session = ChatSession(
            title=title,
            model_provider=payload.model_provider,
            agent_mode=payload.agent_mode,
            last_message_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions(self) -> list[ChatSession]:
        return list(self.db.scalars(select(ChatSession).order_by(ChatSession.updated_at.desc())))

    def get_session(self, session_id: str) -> ChatSession | None:
        return self.db.get(ChatSession, session_id)

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        return list(self.db.scalars(stmt))

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        citations: list[dict] | None = None,
        trace_id: str | None = None,
        latency_ms: int | None = None,
        message_status: str = "completed",
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            citations_json=json.dumps(citations or [], ensure_ascii=False),
            trace_id=trace_id,
            latency_ms=latency_ms,
            message_status=message_status,
        )
        self.db.add(message)
        session = self.get_session(session_id)
        if session:
            session.last_message_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        self.db.delete(session)
        self.db.commit()
        return True
