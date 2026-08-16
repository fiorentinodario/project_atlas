import { ArrowRight, CheckCircle2, Clock3, FolderKanban, FolderPlus, ListTodo, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { ProgressBar } from '../components/ui/ProgressBar'
import { getDashboard } from '../dashboard/api'
import type { DashboardData } from '../dashboard/types'
import { ApiClientError } from '../lib/api'

const labels: Record<string, string> = {
  PROJECT_CREATED: 'created the project', DOCUMENT_UPLOADED: 'uploaded a document',
  TASK_CREATED: 'created a task', TASK_COMPLETED: 'completed a task',
  AI_ANALYSIS_COMPLETED: 'completed an AI analysis', AI_TASKS_CREATED: 'created AI tasks',
  DECISION_CREATED: 'recorded a decision', DECISION_CONFIRMED: 'confirmed a decision',
}

export function DashboardPage() {
  const { user, accessToken } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!accessToken) return
    getDashboard(accessToken).then((response) => setData(response.data)).catch((caught) => setError(caught instanceof ApiClientError ? caught.message : 'Unable to load the dashboard.'))
  }, [accessToken])
  if (!data && !error) return <div className="space-y-4" role="status" aria-label="Loading dashboard">{[1, 2, 3].map((item) => <div key={item} className="h-32 animate-pulse rounded-2xl bg-slate-200/70" />)}</div>
  if (error) return <Card className="p-8"><p role="alert" className="text-red-700">{error}</p></Card>
  if (!data) return null
  const stats = [
    ['Active projects', data.stats.active_projects, FolderKanban, 'bg-brand-50 text-brand-700'],
    ['Total tasks', data.stats.total_tasks, ListTodo, 'bg-sky-50 text-sky-700'],
    ['In progress', data.stats.tasks_in_progress, Clock3, 'bg-amber-50 text-amber-700'],
    ['Completed', data.stats.completed_tasks, CheckCircle2, 'bg-emerald-50 text-emerald-700'],
  ] as const
  return <div className="space-y-8">
    <section className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="mb-2 text-sm font-semibold text-brand-600">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p><h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Good morning, {user?.display_name.split(' ')[0] ?? 'there'}</h1><p className="mt-2 text-ink-500">Here’s what’s happening across your projects.</p></div><Button onClick={() => navigate('/projects')}><FolderPlus size={18} /> New project</Button></section>
    <section aria-label="Project statistics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{stats.map(([label, value, Icon, tone]) => <Card key={label} className="p-5"><div className="flex justify-between"><div><p className="text-sm text-ink-500">{label}</p><p className="mt-2 text-3xl font-bold">{value}</p></div><span className={`grid size-11 place-items-center rounded-xl ${tone}`}><Icon size={20} /></span></div></Card>)}</section>
    <section className="rounded-3xl bg-ink-950 px-6 py-7 text-white"><div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between"><div className="flex gap-4"><span className="grid size-11 place-items-center rounded-xl bg-white/10"><Sparkles size={20} /></span><div><h2 className="font-semibold">Ask ProjectAtlas</h2><p className="mt-1 text-sm text-slate-300">Choose a project to ask questions grounded in its knowledge.</p></div></div><Button variant="secondary" onClick={() => navigate('/projects')}>Choose project <ArrowRight size={16} /></Button></div></section>
    <div className="grid gap-6 xl:grid-cols-[1.45fr_0.85fr]">
      <section><div className="mb-4 flex justify-between"><div><h2 className="text-xl font-bold">Recent projects</h2><p className="text-sm text-ink-500">Your recently active workspaces</p></div><Button variant="ghost" onClick={() => navigate('/projects')}>View all <ArrowRight size={16} /></Button></div>{data.recent_projects.length === 0 ? <EmptyState icon={FolderKanban} title="No projects yet" description="Create your first project workspace." /> : <div className="grid gap-4 md:grid-cols-2">{data.recent_projects.map((project) => <Card key={project.id} className="cursor-pointer p-5" onClick={() => navigate(`/projects/${project.id}`)}><div className="flex justify-between"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 font-bold text-brand-700">{project.name.slice(0, 2).toUpperCase()}</span><Badge tone={project.status === 'ACTIVE' ? 'green' : 'slate'}>{project.status}</Badge></div><h3 className="mt-4 font-bold">{project.name}</h3><p className="mt-2 line-clamp-2 text-sm text-ink-500">{project.description ?? 'No description'}</p><div className="mt-4 flex justify-between text-xs"><span>{project.progress}% complete</span><span>{project.task_count} tasks · {project.document_count} docs</span></div><div className="mt-2"><ProgressBar value={project.progress} /></div></Card>)}</div>}</section>
      <section><div className="mb-4"><h2 className="text-xl font-bold">Recent activity</h2><p className="text-sm text-ink-500">Latest workspace updates</p></div><Card className="divide-y divide-slate-100 px-5">{data.recent_activity.length === 0 ? <p className="py-8 text-center text-sm text-ink-500">No activity yet.</p> : data.recent_activity.map((activity) => <button key={activity.id} onClick={() => navigate(`/projects/${activity.project.id}`)} className="flex w-full gap-3 py-4 text-left"><span className="grid size-9 shrink-0 place-items-center rounded-full bg-brand-50 text-xs font-bold text-brand-700">{activity.actor?.display_name.slice(0, 2).toUpperCase() ?? 'AI'}</span><span><span className="block text-sm"><strong>{activity.actor?.display_name ?? 'System'}</strong> {labels[activity.action] ?? activity.action.toLowerCase().replaceAll('_', ' ')}</span><span className="mt-1 block text-xs text-ink-500">{activity.project.name} · {new Date(activity.created_at).toLocaleString()}</span></span></button>)}</Card></section>
    </div>
  </div>
}
