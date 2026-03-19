from datetime import datetime

from pydantic import BaseModel


class UploadDocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class DocumentListItem(BaseModel):
    id: str
    filename: str
    display_name: str
    status: str
    chunk_strategy: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentListItem):
    file_ext: str
    mime_type: str | None = None
    file_size: int
    token_count: int | None = None
    error_message: str | None = None
    storage_path: str
