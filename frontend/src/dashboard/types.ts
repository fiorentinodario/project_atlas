export type DashboardData = {
  stats: { active_projects: number; total_tasks: number; tasks_in_progress: number; completed_tasks: number }
  recent_projects: Array<{ id: string; name: string; description: string | null; status: 'ACTIVE' | 'ARCHIVED'; task_count: number; document_count: number; progress: number; updated_at: string }>
  recent_activity: Array<{ id: string; action: string; metadata: Record<string, unknown>; created_at: string; project: { id: string; name: string }; actor: { id: string; display_name: string } | null }>
}
