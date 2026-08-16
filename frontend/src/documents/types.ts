export type DocumentStatus = 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED'

export type ProjectDocument = {
  id: string
  project_id: string
  filename: string
  mime_type: string
  size_bytes: number
  status: DocumentStatus
  processing_error: string | null
  indexed_at: string | null
  indexing_error: string | null
  created_at: string
  updated_at: string
}

export type SemanticSearchResult = {
  chunk_id: string
  content: string
  page_number: number | null
  score: number
  document: {
    id: string
    filename: string
  }
}
