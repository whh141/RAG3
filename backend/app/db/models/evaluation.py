from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    baseline_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="baseline_rag")
    agent_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="agentic_rag")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    records: Mapped[list["EvalRecord"]] = relationship(back_populates="eval_run", cascade="all, delete-orphan")


class EvalRecord(Base):
    __tablename__ = "eval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    eval_run_id: Mapped[str] = mapped_column(ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    agent_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    agent_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_expected: Mapped[str | None] = mapped_column(String(32), nullable=True)
    route_actual: Mapped[str | None] = mapped_column(String(32), nullable=True)
    route_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    eval_run: Mapped[EvalRun] = relationship(back_populates="records")
