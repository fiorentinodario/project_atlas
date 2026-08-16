import { AlertCircle, ArrowRight, FolderKanban, Plus } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { ApiClientError } from '../lib/api'
import { createProject, getProjects } from '../projects/api'
import type { Project } from '../projects/types'

export function ProjectsPage() {
  const { accessToken } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setLoading] = useState(true)
  const [isCreating, setCreating] = useState(false)
  const [isModalOpen, setModalOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!accessToken) return
    let ignore = false
    getProjects(accessToken)
      .then((response) => {
        if (!ignore) setProjects(response.data.items)
      })
      .catch((caughtError) => {
        if (!ignore) {
          setError(
            caughtError instanceof ApiClientError ? caughtError.message : 'Unable to load projects.',
          )
        }
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [accessToken])

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!accessToken) return
    setCreating(true)
    setError(null)
    const data = new FormData(event.currentTarget)
    try {
      const response = await createProject({ name: String(data.get('name')), description: String(data.get('description')) }, accessToken)
      setProjects((current) => [response.data.project, ...current])
      setModalOpen(false)
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to create the project.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div><p className="text-sm font-semibold text-brand-600">Workspace</p><h1 className="mt-2 text-3xl font-bold tracking-tight">Projects</h1><p className="mt-2 text-ink-500">Organize knowledge, tasks and decisions in one place.</p></div>
        <Button onClick={() => setModalOpen(true)}><Plus size={18} /> New project</Button>
      </div>

      {error && <div role="alert" className="mt-6 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"><AlertCircle size={18} />{error}</div>}

      {isLoading ? (
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3" role="status" aria-label="Loading projects">{[1, 2, 3].map((item) => <div key={item} className="h-64 animate-pulse rounded-2xl bg-slate-200/70" />)}</div>
      ) : projects.length === 0 ? (
        <div className="mt-8"><EmptyState icon={FolderKanban} title="No projects yet" description="Create your first workspace to organize project documents, tasks and decisions." action={<Button onClick={() => setModalOpen(true)}><Plus size={18} /> Create first project</Button>} /></div>
      ) : (
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => (
            <Card key={project.id} className="flex min-h-64 flex-col p-5 transition hover:-translate-y-0.5 hover:border-brand-500/40">
              <div className="flex items-start justify-between gap-3"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 font-bold text-brand-700">{project.name.slice(0, 2).toUpperCase()}</span><Badge tone={project.status === 'ACTIVE' ? 'green' : 'slate'}>{project.status === 'ACTIVE' ? 'Active' : 'Archived'}</Badge></div>
              <h2 className="mt-5 text-lg font-bold">{project.name}</h2>
              <p className="mt-2 line-clamp-3 flex-1 text-sm leading-6 text-ink-500">{project.description ?? 'No description has been added yet.'}</p>
              <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4"><span className="text-xs font-semibold text-ink-500">{project.role}</span><Link to={`/projects/${project.id}`} className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:underline">Open <ArrowRight size={15} /></Link></div>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setModalOpen(false)} title="Create a project" description="Start with a clear name and short description. You can refine both later.">
        <form className="mt-6 space-y-5" onSubmit={handleCreate}>
          <Input id="project-name" name="name" label="Project name" placeholder="Merchant Portal" minLength={2} maxLength={160} autoFocus required />
          <div><label htmlFor="project-description" className="mb-2 block text-sm font-semibold text-ink-700">Description</label><textarea id="project-description" name="description" rows={4} maxLength={2000} placeholder="What is this project trying to achieve?" className="w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm placeholder:text-slate-400" /></div>
          <div className="flex justify-end gap-3"><Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button><Button type="submit" disabled={isCreating}>{isCreating ? 'Creating...' : 'Create project'}</Button></div>
        </form>
      </Modal>
    </div>
  )
}
