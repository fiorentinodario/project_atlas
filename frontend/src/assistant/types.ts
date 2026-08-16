export type AssistantSource = {
  number: number
  chunk_id: string
  document_id: string
  filename: string
  page_number: number | null
  excerpt: string
  score: number
}

export type AssistantMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: AssistantSource[]
}
