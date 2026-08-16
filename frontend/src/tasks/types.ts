export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'DONE'
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'

export type Task = {
  id: string
  project_id: string
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  due_date: string | null
  assigned_user: { id: string; display_name: string } | null
  created_by: { id: string; display_name: string }
  source: 'MANUAL' | 'AI_GENERATED'
  source_analysis_id: string | null
  source_suggestion_index: number | null
  created_at: string
  updated_at: string
}

export type TaskInput = {
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  due_date: string | null
}
