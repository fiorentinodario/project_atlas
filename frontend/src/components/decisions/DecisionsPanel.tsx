import { Bot, CalendarDays, Check, FileText, Gavel, Pencil, Plus, Sparkles, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/useAuth'
import {
  deleteDecision,
  detectDecisions,
  getDecisions,
  reviewDecision,
} from '../../decisions/api'
import type { ProjectDecision } from '../../decisions/types'
import { ApiClientError } from '../../lib/api'
import type { ProjectRole } from '../../projects/types'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'
import { DecisionFormModal } from './DecisionFormModal'

const statusTone = { PENDING: 'amber', CONFIRMED: 'green', REJECTED: 'slate' } as const

export function DecisionsPanel({ projectId, role }: { projectId: string; role: ProjectRole }) {
  const { accessToken } = useAuth()
  const [decisions, setDecisions] = useState<ProjectDecision[]>([])
  const [editing, setEditing] = useState<ProjectDecision | null | undefined>(undefined)
  const [isLoading, setLoading] = useState(true)
  const [isDetecting, setDetecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canWrite = role !== 'VIEWER'

  useEffect(() => {
    if (!accessToken) return
    let ignore = false
    getDecisions(projectId, accessToken)
      .then((response) => { if (!ignore) setDecisions(response.data.items) })
      .catch((caughtError) => { if (!ignore) setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to load decisions.') })
      .finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [accessToken, projectId])

  function save(decision: ProjectDecision) {
    setDecisions((current) => current.some((item) => item.id === decision.id)
      ? current.map((item) => item.id === decision.id ? decision : item)
      : [decision, ...current])
    setEditing(undefined)
  }

  async function detect() {
    if (!accessToken) return
    setDetecting(true)
    setError(null)
    try {
      const response = await detectDecisions(projectId, accessToken)
      const detectedIds = new Set(response.data.items.map((item) => item.id))
      setDecisions((current) => [
        ...response.data.items,
        ...current.filter((item) => !detectedIds.has(item.id)),
      ])
      if (response.data.items.length === 0) setError('No new explicit decisions were detected.')
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to detect decisions.')
    } finally {
      setDetecting(false)
    }
  }

  async function review(decision: ProjectDecision, action: 'confirm' | 'reject') {
    if (!accessToken) return
    try {
      const response = await reviewDecision(decision.id, action, accessToken)
      save(response.data.decision)
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to review the decision.')
    }
  }

  async function remove(decision: ProjectDecision) {
    if (!accessToken || !window.confirm(`Delete “${decision.title}”?`)) return
    try {
      await deleteDecision(decision.id, accessToken)
      setDecisions((current) => current.filter((item) => item.id !== decision.id))
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to delete the decision.')
    }
  }

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div><h2 className="text-xl font-bold">Project decisions</h2><p className="mt-1 max-w-2xl text-sm text-ink-500">Track confirmed choices and review suggestions detected in project documents.</p></div>
        {canWrite && <div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={isDetecting} onClick={() => void detect()}><Sparkles size={17} />{isDetecting ? 'Detecting…' : 'Detect with AI'}</Button><Button onClick={() => setEditing(null)}><Plus size={17} /> Add decision</Button></div>}
      </div>
      {error && <p role="alert" className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">{error}</p>}
      {isLoading ? <div className="mt-6 space-y-3" role="status">{[1, 2].map((item) => <div key={item} className="h-36 animate-pulse rounded-2xl bg-slate-200/70" />)}</div> : decisions.length === 0 ? <div className="mt-6"><EmptyState icon={Gavel} title="No project decisions yet" description="Record an important choice manually or detect candidates from indexed documents." action={canWrite ? <Button onClick={() => setEditing(null)}><Plus size={17} /> Record first decision</Button> : undefined} /></div> : <div className="mt-6 space-y-4">{decisions.map((decision) => <Card key={decision.id} className={`p-5 ${decision.status === 'PENDING' ? 'border-amber-200' : ''}`}><div className="flex flex-col gap-4 sm:flex-row sm:items-start"><span className={`grid size-11 shrink-0 place-items-center rounded-xl ${decision.origin === 'AI_DETECTED' ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-ink-700'}`}>{decision.origin === 'AI_DETECTED' ? <Bot size={20} /> : <Gavel size={20} />}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="font-bold">{decision.title}</h3><Badge tone={statusTone[decision.status]}>{decision.status}</Badge><Badge tone={decision.origin === 'AI_DETECTED' ? 'blue' : 'slate'}>{decision.origin === 'AI_DETECTED' ? 'AI detected' : 'Manual'}</Badge></div><p className="mt-2 text-sm leading-6 text-ink-500">{decision.description}</p><div className="mt-3 flex flex-wrap gap-4 text-xs text-ink-500"><span className="flex items-center gap-1"><CalendarDays size={13} />{new Date(decision.decision_date).toLocaleDateString()}</span>{decision.source && <span className="flex items-center gap-1"><FileText size={13} />{decision.source.filename}{decision.source.page_number ? ` · Page ${decision.source.page_number}` : ''}</span>}</div>{decision.status === 'PENDING' && <p className="mt-3 text-xs font-semibold text-amber-700">AI suggestion — confirmation is required before the assistant treats this as a project fact.</p>}</div>{canWrite && <div className="flex shrink-0 flex-wrap gap-1">{decision.status === 'PENDING' && <><button onClick={() => void review(decision, 'confirm')} className="rounded-lg p-2 text-emerald-700 hover:bg-emerald-50" aria-label={`Confirm ${decision.title}`}><Check size={17} /></button><button onClick={() => void review(decision, 'reject')} className="rounded-lg p-2 text-amber-700 hover:bg-amber-50" aria-label={`Reject ${decision.title}`}><X size={17} /></button></>}<button onClick={() => setEditing(decision)} className="rounded-lg p-2 text-ink-500 hover:bg-slate-100" aria-label={`Edit ${decision.title}`}><Pencil size={17} /></button><button onClick={() => void remove(decision)} className="rounded-lg p-2 text-ink-500 hover:bg-red-50 hover:text-red-600" aria-label={`Delete ${decision.title}`}><Trash2 size={17} /></button></div>}</div></Card>)}</div>}
      {editing !== undefined && accessToken && <DecisionFormModal accessToken={accessToken} projectId={projectId} decision={editing} onClose={() => setEditing(undefined)} onSaved={save} />}
    </section>
  )
}
