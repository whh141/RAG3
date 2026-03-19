from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_documents(self) -> list[Document]:
        return list(self.db.scalars(select(Document).order_by(Document.created_at.desc())))

    def get_document(self, document_id: str) -> Document | None:
        return self.db.get(Document, document_id)

    def create_placeholder_document(
        self,
        filename: str,
        content_type: str | None,
        size: int,
        chunk_strategy: str,
    ) -> Document:
        suffix = Path(filename).suffix.lower().lstrip(".") or "txt"
        document = Document(
            filename=filename,
            display_name=Path(filename).stem,
            file_ext=suffix,
            mime_type=content_type,
            storage_path=str(Path(settings.upload_dir) / filename),
            file_size=size,
            status="uploaded",
            chunk_strategy=chunk_strategy,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: str) -> bool:
        document = self.get_document(document_id)
        if not document:
            return False
        self.db.delete(document)
        self.db.commit()
        return True
