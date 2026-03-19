from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentDetail, DocumentListItem, UploadDocumentResponse
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    chunk_strategy: str = Form("by_heading_paragraph"),
    db: Session = Depends(get_db),
) -> UploadDocumentResponse:
    payload = await file.read()
    service = DocumentService(db)
    document = service.create_placeholder_document(
        filename=file.filename or "unnamed.txt",
        content_type=file.content_type,
        size=len(payload),
        chunk_strategy=chunk_strategy,
    )
    return UploadDocumentResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        message="上传成功，后台解析链路待接入。",
    )


@router.get("/list", response_model=list[DocumentListItem])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentListItem]:
    return DocumentService(db).list_documents()


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetail:
    document = DocumentService(db).get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    deleted = DocumentService(db).delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document deleted"}
