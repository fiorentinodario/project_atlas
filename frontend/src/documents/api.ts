import { apiRequest } from '../lib/api'
import type { ProjectDocument } from './types'

export function getDocuments(projectId: string, accessToken: string) {
  return apiRequest<{ data: { items: ProjectDocument[] } }>(
    `/projects/${projectId}/documents`,
    {},
    accessToken,
  )
}

export function uploadDocument(projectId: string, file: File, accessToken: string) {
  const body = new FormData()
  body.append('file', file)
  return apiRequest<{ data: { document: ProjectDocument } }>(
    `/projects/${projectId}/documents`,
    { method: 'POST', body },
    accessToken,
  )
}

export function deleteDocument(documentId: string, accessToken: string) {
  return apiRequest<void>(`/documents/${documentId}`, { method: 'DELETE' }, accessToken)
}
