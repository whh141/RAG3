from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evaluation import EvalRecordDTO, EvalRunDTO, StartEvalRequest
from app.services.evaluation_service import EvaluationService

router = APIRouter()


@router.post("/run", response_model=EvalRunDTO, status_code=status.HTTP_201_CREATED)
def create_eval_run(payload: StartEvalRequest, db: Session = Depends(get_db)) -> EvalRunDTO:
    return EvaluationService(db).create_run(payload)


@router.get("/runs", response_model=list[EvalRunDTO])
def list_eval_runs(db: Session = Depends(get_db)) -> list[EvalRunDTO]:
    return EvaluationService(db).list_runs()


@router.get("/run/{eval_run_id}", response_model=EvalRunDTO)
def get_eval_run(eval_run_id: str, db: Session = Depends(get_db)) -> EvalRunDTO:
    run = EvaluationService(db).get_run(eval_run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")
    return run


@router.get("/run/{eval_run_id}/records", response_model=list[EvalRecordDTO])
def list_eval_records(eval_run_id: str, db: Session = Depends(get_db)) -> list[EvalRecordDTO]:
    service = EvaluationService(db)
    if not service.get_run(eval_run_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")
    return service.list_records(eval_run_id)
