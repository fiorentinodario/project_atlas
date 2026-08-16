import { apiRequest } from '../lib/api'
import type { AssistantSource } from './types'

export function askProjectAssistant(
  projectId: string,
  question: string,
  history: Array<{ role: 'user' | 'assistant'; content: string }>,
  accessToken: string,
) {
  return apiRequest<{
    data: { message: { role: 'assistant'; content: string; sources: AssistantSource[] } }
  }>(
    `/projects/${projectId}/assistant/messages`,
    { method: 'POST', body: JSON.stringify({ question, history: history.slice(-10) }) },
    accessToken,
  )
}
