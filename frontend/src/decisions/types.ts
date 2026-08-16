export type DecisionOrigin = 'MANUAL' | 'AI_DETECTED'
export type DecisionStatus = 'PENDING' | 'CONFIRMED' | 'REJECTED'

export type ProjectDecision = {
  id: string
  project_id: string
  title: string
  description: string
  decision_date: string
  origin: DecisionOrigin
  status: DecisionStatus
  source: {
    document_id: string
    filename: string
    chunk_id: string | null
    page_number: number | null
  } | null
  created_by: { id: string; display_name: string }
  confirmed_by: { id: string; display_name: string } | null
  confirmed_at: string | null
  created_at: string
  updated_at: string
}

export type DecisionInput = {
  title: string
  description: string
  decision_date?: string
}
