import { AlertTriangle, CheckCircle2, CircleHelp, ClipboardList, LoaderCircle, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import {
  createTasksFromAnalysis,
  getLatestAnalysis,
  runProjectAnalysis,
} from '../../analyses/api'
import type { ProjectAnalysis } from '../../analyses/types'
import { useAuth } from '../../auth/useAuth'
import { ApiClientError } from '../../lib/api'
import type { ProjectRole } from '../../projects/types'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { AnalysisSources } from './AnalysisSources'

const riskTone = { LOW: 'slate', MEDIUM: 'amber', HIGH: 'amber' } as const
const priorityTone = { LOW: 'slate', MEDIUM: 'blue', HIGH: 'amber', URGENT: 'amber' } as const

export function AnalysisPanel({ projectId, role }: { projectId: string; role: ProjectRole }) {
  const { accessToken } = useAuth()
  const [analysis, setAnalysis] = useState<ProjectAnalysis | null>(null)
  const [isLoading, setLoading] = useState(true)
  const [isRunning, setRunning] = useState(false)
  const [isCreatingTasks, setCreatingTasks] = useState(false)
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const canWrite = role !== 'VIEWER'

  useEffect(() => {
    if (!accessToken) return
    let ignore = false
    getLatestAnalysis(projectId, accessToken)
      .then((response) => { if (!ignore) setAnalysis(response.data.analysis) })
      .catch((caughtError) => { if (!ignore) setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to load the project analysis.') })
      .finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [accessToken, projectId])

  async function runAnalysis() {
    if (!accessToken) return
    setRunning(true)
    setError(null)
    try {
      const response = await runProjectAnalysis(projectId, accessToken)
      setAnalysis(response.data.analysis)
      setSelectedSuggestions(new Set())
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to analyze the project.')
    } finally {
      setRunning(false)
    }
  }

  function toggleSuggestion(index: number) {
    setSelectedSuggestions((current) => {
      const next = new Set(current)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  async function createSelectedTasks() {
    if (!accessToken || !analysis || selectedSuggestions.size === 0) return
    setCreatingTasks(true)
    setError(null)
    try {
      const response = await createTasksFromAnalysis(
        analysis.id,
        [...selectedSuggestions],
        accessToken,
      )
      const createdByIndex = new Map(
        response.data.items.map((task) => [task.source_suggestion_index, task.id]),
      )
      setAnalysis({
        ...analysis,
        suggested_tasks: analysis.suggested_tasks.map((suggestion) => ({
          ...suggestion,
          created_task_id: createdByIndex.get(suggestion.index) ?? suggestion.created_task_id,
        })),
      })
      setSelectedSuggestions(new Set())
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to create tasks.')
    } finally {
      setCreatingTasks(false)
    }
  }

  if (isLoading) return <div className="h-96 animate-pulse rounded-2xl bg-slate-200/70" role="status" aria-label="Loading analysis" />

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div><p className="text-sm font-semibold text-brand-600">AI Project Analysis</p><h2 className="mt-1 text-2xl font-bold">Project health and next steps</h2><p className="mt-2 max-w-2xl text-sm text-ink-500">Review requirements, unresolved questions, risks and suggested work grounded in current project data.</p></div>
        {canWrite && <Button disabled={isRunning} onClick={() => void runAnalysis()}>{isRunning ? <LoaderCircle className="animate-spin" size={17} /> : <Sparkles size={17} />}{isRunning ? 'Analyzing…' : analysis ? 'Run new analysis' : 'Analyze project'}</Button>}
      </div>
      {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {!analysis ? <Card className="mt-6 p-10 text-center"><span className="mx-auto grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-700"><Sparkles size={24} /></span><h3 className="mt-5 text-lg font-bold">No analysis available</h3><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-ink-500">Run an analysis to turn documents, tasks and confirmed decisions into a structured project review.</p>{canWrite && <Button className="mt-6" disabled={isRunning} onClick={() => void runAnalysis()}><Sparkles size={17} /> Analyze project</Button>}</Card> : <div className="mt-6 space-y-5">
        <Card className="p-6"><div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700"><Sparkles size={18} /></span><div><h3 className="font-bold">Project summary</h3><p className="mt-2 text-sm leading-6 text-ink-600">{analysis.summary}</p><p className="mt-3 text-xs text-ink-500">Generated {new Date(analysis.created_at).toLocaleString()} by {analysis.requested_by.display_name}</p></div></div></Card>
        <div className="grid gap-5 xl:grid-cols-2">
          <Card className="p-5"><div className="flex items-center gap-2"><CheckCircle2 className="text-emerald-600" size={19} /><h3 className="font-bold">Requirements</h3><Badge>{analysis.requirements.length}</Badge></div><div className="mt-4 space-y-3">{analysis.requirements.length === 0 ? <p className="text-sm text-ink-500">No requirements identified.</p> : analysis.requirements.map((item, index) => <div key={`${index}-${item.text}`} className="rounded-xl bg-slate-50 p-3"><p className="text-sm leading-6 text-ink-700">{item.text}</p><AnalysisSources sources={item.sources} /></div>)}</div></Card>
          <Card className="p-5"><div className="flex items-center gap-2"><AlertTriangle className="text-amber-600" size={19} /><h3 className="font-bold">Risks</h3><Badge tone="amber">{analysis.risks.length}</Badge></div><div className="mt-4 space-y-3">{analysis.risks.length === 0 ? <p className="text-sm text-ink-500">No risks identified.</p> : analysis.risks.map((item, index) => <div key={`${index}-${item.text}`} className="rounded-xl bg-slate-50 p-3"><div className="flex items-start justify-between gap-2"><p className="text-sm leading-6 text-ink-700">{item.text}</p><Badge tone={riskTone[item.severity]}>{item.severity}</Badge></div><AnalysisSources sources={item.sources} /></div>)}</div></Card>
          <Card className="p-5"><div className="flex items-center gap-2"><CircleHelp className="text-sky-600" size={19} /><h3 className="font-bold">Open questions</h3><Badge tone="blue">{analysis.open_questions.length}</Badge></div><div className="mt-4 space-y-3">{analysis.open_questions.length === 0 ? <p className="text-sm text-ink-500">No open questions identified.</p> : analysis.open_questions.map((item, index) => <div key={`${index}-${item.text}`} className="rounded-xl bg-slate-50 p-3"><p className="text-sm font-semibold text-ink-700">{item.text}</p><p className="mt-1 text-xs leading-5 text-ink-500">{item.reason}</p></div>)}</div></Card>
          <Card className="p-5"><div className="flex items-center gap-2"><ClipboardList className="text-brand-600" size={19} /><h3 className="font-bold">Suggested tasks</h3><Badge tone="blue">{analysis.suggested_tasks.length}</Badge></div><div className="mt-4 space-y-3">{analysis.suggested_tasks.length === 0 ? <p className="text-sm text-ink-500">No tasks suggested.</p> : analysis.suggested_tasks.map((item) => <label key={`${item.index}-${item.title}`} className={`block rounded-xl p-3 ${item.created_task_id ? 'bg-emerald-50/60' : 'bg-slate-50'} ${canWrite && !item.created_task_id ? 'cursor-pointer' : ''}`}><div className="flex items-start gap-3">{canWrite && <input type="checkbox" aria-label={`Select ${item.title}`} checked={Boolean(item.created_task_id) || selectedSuggestions.has(item.index)} disabled={Boolean(item.created_task_id) || isCreatingTasks} onChange={() => toggleSuggestion(item.index)} className="mt-1 size-4 rounded border-slate-300 text-brand-600" />}<div className="min-w-0 flex-1"><div className="flex items-start justify-between gap-2"><p className="text-sm font-bold text-ink-700">{item.title}</p><div className="flex gap-2">{item.created_task_id && <Badge tone="green">Created</Badge>}<Badge tone={priorityTone[item.priority]}>{item.priority}</Badge></div></div><p className="mt-1 text-xs leading-5 text-ink-500">{item.description}</p><p className="mt-2 text-xs text-brand-700">Why: {item.reason}</p><AnalysisSources sources={item.sources} /></div></div></label>)}</div>{canWrite && analysis.suggested_tasks.some((item) => !item.created_task_id) && <Button className="mt-4 w-full" disabled={selectedSuggestions.size === 0 || isCreatingTasks} onClick={() => void createSelectedTasks()}>{isCreatingTasks ? <LoaderCircle className="animate-spin" size={17} /> : <ClipboardList size={17} />}{isCreatingTasks ? 'Creating tasks…' : `Create selected tasks (${selectedSuggestions.size})`}</Button>}</Card>
        </div>
      </div>}
    </section>
  )
}
