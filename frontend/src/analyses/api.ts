import { apiRequest } from '../lib/api'
import type { ProjectAnalysis } from './types'

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
