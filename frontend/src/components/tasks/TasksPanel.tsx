import { CalendarDays, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { useAuth } from '../../auth/useAuth'
import { ApiClientError } from '../../lib/api'
import { deleteTask, getTasks, updateTaskStatus } from '../../tasks/api'
import type { Task, TaskPriority, TaskStatus } from '../../tasks/types'
import type { ProjectRole } from '../../projects/types'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'
import { TaskFormModal } from './TaskFormModal'
import { ListTodo } from 'lucide-react'

const columns: { status: TaskStatus; label: string }[] = [
  { status: 'TODO', label: 'To do' },
  { status: 'IN_PROGRESS', label: 'In progress' },
  { status: 'DONE', label: 'Done' },
]

const priorityTone = { LOW: 'slate', MEDIUM: 'blue', HIGH: 'amber', URGENT: 'amber' } as const

export function TasksPanel({ projectId, role }: { projectId: string; role: ProjectRole }) {
  const { accessToken } = useAuth()
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingTask, setEditingTask] = useState<Task | null | undefined>(undefined)
  const [search, setSearch] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [priority, setPriority] = useState<TaskPriority | ''>('')
  const canWrite = role !== 'VIEWER'

  useEffect(() => {
    if (!accessToken) return
    let ignore = false
    getTasks(projectId, accessToken, { search: appliedSearch, priority })
      .then((response) => { if (!ignore) setTasks(response.data.items) })
      .catch((caughtError) => { if (!ignore) setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to load tasks.') })
      .finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [accessToken, appliedSearch, priority, projectId])

  function handleSearch(event: FormEvent) {
    event.preventDefault()
    setAppliedSearch(search.trim())
  }

  function saveTask(saved: Task) {
    setTasks((current) => current.some((task) => task.id === saved.id) ? current.map((task) => task.id === saved.id ? saved : task) : [saved, ...current])
    setEditingTask(undefined)
  }

  async function changeStatus(task: Task, status: TaskStatus) {
    if (!accessToken) return
    try {
      const response = await updateTaskStatus(task.id, status, accessToken)
      saveTask(response.data.task)
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to update the task.')
    }
  }

  async function removeTask(task: Task) {
    if (!accessToken || !window.confirm(`Delete “${task.title}”?`)) return
    try {
      await deleteTask(task.id, accessToken)
      setTasks((current) => current.filter((item) => item.id !== task.id))
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to delete the task.')
    }
  }

  return (
    <section>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <form className="flex max-w-lg flex-1 gap-2" onSubmit={handleSearch}><label htmlFor="task-search" className="sr-only">Search tasks</label><div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500" size={17} /><input id="task-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tasks..." className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-10 pr-3 text-sm" /></div><Button type="submit" variant="secondary">Search</Button></form>
        <div className="flex gap-2"><select aria-label="Filter by priority" value={priority} onChange={(event) => setPriority(event.target.value as TaskPriority | '')} className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm"><option value="">All priorities</option><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="URGENT">Urgent</option></select>{canWrite && <Button onClick={() => setEditingTask(null)}><Plus size={17} /> Add task</Button>}</div>
      </div>
      {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {isLoading ? <div className="mt-6 grid gap-4 lg:grid-cols-3" role="status">{columns.map((column) => <div key={column.status} className="h-64 animate-pulse rounded-2xl bg-slate-200/70" />)}</div> : tasks.length === 0 ? <div className="mt-6"><EmptyState icon={ListTodo} title="No tasks found" description="Create a task or adjust the current search and priority filters." action={canWrite ? <Button onClick={() => setEditingTask(null)}><Plus size={17} /> Create task</Button> : undefined} /></div> : <div className="mt-6 grid items-start gap-4 lg:grid-cols-3">{columns.map((column) => <div key={column.status} className="rounded-2xl bg-slate-100/70 p-3"><div className="mb-3 flex items-center justify-between px-1"><h3 className="text-sm font-bold">{column.label}</h3><span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-ink-500">{tasks.filter((task) => task.status === column.status).length}</span></div><div className="space-y-3">{tasks.filter((task) => task.status === column.status).map((task) => <Card key={task.id} className="p-4 shadow-sm"><div className="flex items-start justify-between gap-2"><Badge tone={priorityTone[task.priority]}>{task.priority}</Badge>{canWrite && <div className="flex"><button onClick={() => setEditingTask(task)} className="rounded-lg p-1.5 text-ink-500 hover:bg-slate-100" aria-label={`Edit ${task.title}`}><Pencil size={15} /></button><button onClick={() => void removeTask(task)} className="rounded-lg p-1.5 text-ink-500 hover:bg-red-50 hover:text-red-600" aria-label={`Delete ${task.title}`}><Trash2 size={15} /></button></div>}</div><h4 className="mt-3 text-sm font-bold">{task.title}</h4>{task.description && <p className="mt-1 line-clamp-2 text-xs leading-5 text-ink-500">{task.description}</p>}{task.due_date && <p className="mt-3 flex items-center gap-1 text-xs text-ink-500"><CalendarDays size={13} /> {new Date(task.due_date).toLocaleDateString()}</p>}{canWrite && <select aria-label={`Change status for ${task.title}`} value={task.status} onChange={(event) => void changeStatus(task, event.target.value as TaskStatus)} className="mt-3 h-9 w-full rounded-lg border border-slate-200 bg-white px-2 text-xs"><option value="TODO">To do</option><option value="IN_PROGRESS">In progress</option><option value="DONE">Done</option></select>}</Card>)}</div></div>)}</div>}
      {editingTask !== undefined && accessToken && <TaskFormModal accessToken={accessToken} projectId={projectId} task={editingTask} onClose={() => setEditingTask(undefined)} onSaved={saveTask} />}
    </section>
  )
}
