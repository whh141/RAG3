export interface DocumentListItem {
  id: string;
  filename: string;
  display_name: string;
  status: string;
  chunk_strategy: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentListItem {
  file_ext: string;
  mime_type?: string | null;
  file_size: number;
  token_count?: number | null;
  error_message?: string | null;
  storage_path: string;
}

export interface UploadDocumentResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
}
