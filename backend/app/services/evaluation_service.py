from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.evaluation import EvalRecord, EvalRun
from app.schemas.evaluation import StartEvalRequest


class EvaluationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(self, payload: StartEvalRequest) -> EvalRun:
        run = EvalRun(
            name=payload.name,
            dataset_name=payload.dataset_name,
            question_count=payload.question_count,
            status="pending",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_runs(self) -> list[EvalRun]:
        return list(self.db.scalars(select(EvalRun).order_by(EvalRun.created_at.desc())))

    def get_run(self, eval_run_id: str) -> EvalRun | None:
        return self.db.get(EvalRun, eval_run_id)

    def list_records(self, eval_run_id: str) -> list[EvalRecord]:
        stmt = select(EvalRecord).where(EvalRecord.eval_run_id == eval_run_id)
        return list(self.db.scalars(stmt))
