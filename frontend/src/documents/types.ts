export type DocumentStatus = 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED'

export type ProjectDocument = {
  id: string
  project_id: string
  filename: string
  mime_type: string
  size_bytes: number
  status: DocumentStatus
  processing_error: string | null
  created_at: string
  updated_at: string
}
