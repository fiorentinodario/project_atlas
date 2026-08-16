export type AnalysisSource = {
  number: number
  chunk_id: string
  document_id: string
  filename: string
  page_number: number | null
  excerpt: string
}

export type ProjectAnalysis = {
  id: string
  project_id: string
  summary: string
  requirements: Array<{ text: string; sources: AnalysisSource[] }>
  risks: Array<{ text: string; severity: 'LOW' | 'MEDIUM' | 'HIGH'; sources: AnalysisSource[] }>
  open_questions: Array<{ text: string; reason: string }>
  suggested_tasks: Array<{
    title: string
    description: string
    priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
    reason: string
    sources: AnalysisSource[]
  }>
  provider: string
  model: string
  requested_by: { id: string; display_name: string }
  created_at: string
}
