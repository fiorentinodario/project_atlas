import { AlertCircle, ArrowLeft, CalendarDays, FileText, ListTodo, MoreHorizontal, Settings, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { ApiClientError } from '../lib/api'
import { deleteProject, getProject } from '../projects/api'
import type { Project } from '../projects/types'
import { TasksPanel } from '../components/tasks/TasksPanel'
import { DocumentsPanel } from '../components/documents/DocumentsPanel'
import { AssistantPanel } from '../components/assistant/AssistantPanel'
import { DecisionsPanel } from '../components/decisions/DecisionsPanel'

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'documents', label: 'Documents' },
  { id: 'tasks', label: 'Tasks' },
  { id: 'decisions', label: 'Decisions' },
  { id: 'assistant', label: 'AI Assistant' },
  { id: 'analysis', label: 'AI Analysis' },
  { id: 'settings', label: 'Settings' },
]

export function ProjectWorkspacePage() {
  const { projectId } = useParams()
  const { accessToken } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') ?? 'overview'
  const [project, setProject] = useState<Project | null>(null)
  const [isLoading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!accessToken || !projectId) return
    getProject(projectId, accessToken).then((response) => setProject(response.data.project)).catch((caughtError) => setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to load this project.')).finally(() => setLoading(false))
  }, [accessToken, projectId])

  async function handleDelete() {
    if (!accessToken || !projectId || !project) return
    if (!window.confirm(`Delete “${project.name}”? This action cannot be undone.`)) return
    await deleteProject(projectId, accessToken)
    navigate('/projects', { replace: true })
  }

  if (isLoading) return <div className="h-96 animate-pulse rounded-2xl bg-slate-200/70" role="status" aria-label="Loading project" />
  if (error || !project) return <Card className="p-8"><div role="alert" className="flex gap-3 text-red-700"><AlertCircle /> <div><h1 className="font-bold">Project unavailable</h1><p className="mt-1 text-sm">{error ?? 'The project could not be found.'}</p><Link to="/projects" className="mt-4 inline-block text-sm font-semibold underline">Back to projects</Link></div></div></Card>

  return (
    <div>
      <Link to="/projects" className="inline-flex items-center gap-2 text-sm font-semibold text-ink-500 hover:text-ink-950"><ArrowLeft size={16} /> All projects</Link>
      <div className="mt-5 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div><div className="flex flex-wrap items-center gap-3"><h1 className="text-3xl font-bold tracking-tight">{project.name}</h1><Badge tone={project.status === 'ACTIVE' ? 'green' : 'slate'}>{project.status}</Badge></div><p className="mt-3 max-w-3xl text-sm leading-6 text-ink-500">{project.description ?? 'No project description yet.'}</p><div className="mt-3 flex flex-wrap gap-4 text-xs text-ink-500"><span className="flex items-center gap-1.5"><CalendarDays size={14} /> Created {new Date(project.created_at).toLocaleDateString()}</span><span>Owner: {project.owner.display_name}</span><span>Your role: {project.role}</span></div></div>
        {project.role === 'OWNER' && <Button variant="secondary" onClick={() => void handleDelete()} className="text-red-600"><MoreHorizontal size={18} /> Delete project</Button>}
      </div>

      <nav className="mt-8 flex gap-1 overflow-x-auto border-b border-slate-200" aria-label="Project sections">{tabs.map((tab) => <button key={tab.id} onClick={() => setSearchParams(tab.id === 'overview' ? {} : { tab: tab.id })} className={`shrink-0 border-b-2 px-4 py-3 text-sm font-semibold ${activeTab === tab.id ? 'border-brand-500 text-brand-700' : 'border-transparent text-ink-500 hover:text-ink-950'}`}>{tab.label}</button>)}</nav>

      {activeTab === 'decisions' ? <div className="mt-7"><DecisionsPanel projectId={project.id} role={project.role} /></div> : activeTab === 'assistant' ? <div className="mt-7"><AssistantPanel projectId={project.id} /></div> : activeTab === 'tasks' ? <div className="mt-7"><TasksPanel projectId={project.id} role={project.role} /></div> : activeTab === 'documents' ? <div className="mt-7"><DocumentsPanel projectId={project.id} role={project.role} /></div> : activeTab === 'overview' ? <><div className="mt-7 grid gap-4 sm:grid-cols-3">
        {[{ label: 'Documents', value: '0', icon: FileText }, { label: 'Open tasks', value: '0', icon: ListTodo }, { label: 'AI insights', value: 'Not analyzed', icon: Sparkles }].map(({ icon: Icon, label, value }) => <Card key={label} className="p-5"><div className="flex items-center justify-between"><div><p className="text-sm text-ink-500">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p></div><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-700"><Icon size={20} /></span></div></Card>)}
      </div>
      <Card className="mt-6 p-6"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-slate-100 text-ink-700"><Settings size={19} /></span><div><h2 className="font-bold">Workspace ready</h2><p className="mt-1 text-sm text-ink-500">Documents and AI tools will be activated in their dedicated milestones.</p></div></div></Card></> : <Card className="mt-7 p-8 text-center"><h2 className="font-bold">{tabs.find((tab) => tab.id === activeTab)?.label}</h2><p className="mt-2 text-sm text-ink-500">This section will be introduced in its dedicated milestone.</p></Card>}
    </div>
  )
}
