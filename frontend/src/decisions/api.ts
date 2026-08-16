import { apiRequest } from '../lib/api'
import type { DecisionInput, ProjectDecision } from './types'

export function getDecisions(projectId: string, accessToken: string) {
  return apiRequest<{ data: { items: ProjectDecision[] } }>(
    `/projects/${projectId}/decisions`,
    {},
    accessToken,
  )
}

export function createDecision(projectId: string, data: DecisionInput, accessToken: string) {
  return apiRequest<{ data: { decision: ProjectDecision } }>(
    `/projects/${projectId}/decisions`,
    { method: 'POST', body: JSON.stringify(data) },
    accessToken,
  )
}

export function updateDecision(decisionId: string, data: DecisionInput, accessToken: string) {
  return apiRequest<{ data: { decision: ProjectDecision } }>(
    `/decisions/${decisionId}`,
    { method: 'PATCH', body: JSON.stringify(data) },
    accessToken,
  )
}

export function deleteDecision(decisionId: string, accessToken: string) {
  return apiRequest<void>(`/decisions/${decisionId}`, { method: 'DELETE' }, accessToken)
}

export function reviewDecision(
  decisionId: string,
  action: 'confirm' | 'reject',
  accessToken: string,
) {
  return apiRequest<{ data: { decision: ProjectDecision } }>(
    `/decisions/${decisionId}/${action}`,
    { method: 'POST' },
    accessToken,
  )
}

export function detectDecisions(projectId: string, accessToken: string) {
  return apiRequest<{ data: { items: ProjectDecision[] } }>(
    `/projects/${projectId}/decisions/detect`,
    { method: 'POST' },
    accessToken,
  )
}
