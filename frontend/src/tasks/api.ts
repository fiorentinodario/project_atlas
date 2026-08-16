import { apiRequest } from '../lib/api'
import type { Task, TaskInput, TaskPriority, TaskStatus } from './types'

export function getTasks(
  projectId: string,
  accessToken: string,
  filters: { search?: string; priority?: TaskPriority | '' },
) {
  const query = new URLSearchParams()
  if (filters.search) query.set('search', filters.search)
  if (filters.priority) query.set('priority', filters.priority)
  const suffix = query.size ? `?${query}` : ''
  return apiRequest<{ data: { items: Task[] } }>(
    `/projects/${projectId}/tasks${suffix}`,
    {},
    accessToken,
  )
}

export function createTask(projectId: string, input: TaskInput, accessToken: string) {
  return apiRequest<{ data: { task: Task } }>(
    `/projects/${projectId}/tasks`,
    { method: 'POST', body: JSON.stringify(input) },
    accessToken,
  )
}

export function updateTask(taskId: string, input: Partial<TaskInput>, accessToken: string) {
  return apiRequest<{ data: { task: Task } }>(
    `/tasks/${taskId}`,
    { method: 'PATCH', body: JSON.stringify(input) },
    accessToken,
  )
}

export function updateTaskStatus(taskId: string, status: TaskStatus, accessToken: string) {
  return updateTask(taskId, { status }, accessToken)
}

export function deleteTask(taskId: string, accessToken: string) {
  return apiRequest<void>(`/tasks/${taskId}`, { method: 'DELETE' }, accessToken)
}
