import { apiRequest } from '../lib/api'
import type { Project, ProjectListResponse } from './types'

export function getProjects(accessToken: string) {
  return apiRequest<ProjectListResponse>('/projects', {}, accessToken)
}

export function getProject(projectId: string, accessToken: string) {
  return apiRequest<{ data: { project: Project } }>(`/projects/${projectId}`, {}, accessToken)
}

export function createProject(
  data: { name: string; description: string },
  accessToken: string,
) {
  return apiRequest<{ data: { project: Project } }>(
    '/projects',
    { method: 'POST', body: JSON.stringify(data) },
    accessToken,
  )
}

export function deleteProject(projectId: string, accessToken: string) {
  return apiRequest<void>(`/projects/${projectId}`, { method: 'DELETE' }, accessToken)
}
