import { apiRequest } from '../lib/api'
import type { ProjectAnalysis } from './types'
import type { Task } from '../tasks/types'

export function getLatestAnalysis(projectId: string, accessToken: string) {
  return apiRequest<{ data: { analysis: ProjectAnalysis | null } }>(
    `/projects/${projectId}/analyses/latest`,
    {},
    accessToken,
  )
}

export function runProjectAnalysis(projectId: string, accessToken: string) {
  return apiRequest<{ data: { analysis: ProjectAnalysis } }>(
    `/projects/${projectId}/analyses`,
    { method: 'POST' },
    accessToken,
  )
}

export function createTasksFromAnalysis(
  analysisId: string,
  suggestionIndices: number[],
  accessToken: string,
) {
  return apiRequest<{ data: { items: Task[] } }>(
    `/analyses/${analysisId}/tasks`,
    { method: 'POST', body: JSON.stringify({ suggestion_indices: suggestionIndices }) },
    accessToken,
  )
}
