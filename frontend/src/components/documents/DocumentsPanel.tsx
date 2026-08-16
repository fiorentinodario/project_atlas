import { AlertCircle, CheckCircle2, FileText, LoaderCircle, Trash2, UploadCloud } from 'lucide-react'
import { useEffect, useRef, useState, type DragEvent } from 'react'
import { useAuth } from '../../auth/useAuth'
import { deleteDocument, getDocuments, uploadDocument } from '../../documents/api'
import type { ProjectDocument } from '../../documents/types'
import { ApiClientError } from '../../lib/api'
import type { ProjectRole } from '../../projects/types'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const statusConfig = {
  UPLOADED: { label: 'Uploaded', tone: 'blue', icon: UploadCloud },
  PROCESSING: { label: 'Processing', tone: 'blue', icon: LoaderCircle },
  READY: { label: 'Ready', tone: 'green', icon: CheckCircle2 },
  FAILED: { label: 'Failed', tone: 'amber', icon: AlertCircle },
} as const

export function DocumentsPanel({ projectId, role }: { projectId: string; role: ProjectRole }) {
  const { accessToken } = useAuth()
  const inputRef = useRef<HTMLInputElement>(null)
  const [documents, setDocuments] = useState<ProjectDocument[]>([])
  const [isLoading, setLoading] = useState(true)
  const [isUploading, setUploading] = useState(false)
  const [isDragging, setDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canWrite = role !== 'VIEWER'

  useEffect(() => {
    if (!accessToken) return
    let ignore = false
    getDocuments(projectId, accessToken)
      .then((response) => { if (!ignore) setDocuments(response.data.items) })
      .catch((caughtError) => { if (!ignore) setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to load documents.') })
      .finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [accessToken, projectId])

  async function addFile(file: File | undefined) {
    if (!file || !accessToken) return
    setUploading(true)
    setError(null)
    try {
      const response = await uploadDocument(projectId, file, accessToken)
      setDocuments((current) => [response.data.document, ...current])
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to upload the document.')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    void addFile(event.dataTransfer.files[0])
  }

  async function remove(document: ProjectDocument) {
    if (!accessToken || !window.confirm(`Delete “${document.filename}”?`)) return
    try {
      await deleteDocument(document.id, accessToken)
      setDocuments((current) => current.filter((item) => item.id !== document.id))
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to delete the document.')
    }
  }

  return (
    <section>
      {canWrite && <div onDragEnter={(event) => { event.preventDefault(); setDragging(true) }} onDragOver={(event) => event.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={handleDrop} className={`rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${isDragging ? 'border-brand-500 bg-brand-50' : 'border-slate-300 bg-white'}`}><input ref={inputRef} type="file" aria-label="Upload document" accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown" className="sr-only" id="document-upload" onChange={(event) => void addFile(event.target.files?.[0])} /><span className="mx-auto grid size-12 place-items-center rounded-xl bg-brand-50 text-brand-700"><UploadCloud size={22} /></span><h2 className="mt-4 font-bold">Drop a project document here</h2><p className="mt-2 text-sm text-ink-500">PDF, TXT or Markdown · maximum 10 MB</p><Button type="button" variant="secondary" className="mt-5" onClick={() => inputRef.current?.click()} disabled={isUploading}>{isUploading ? 'Uploading and processing...' : 'Choose a file'}</Button></div>}
      {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {isLoading ? <div className="mt-6 space-y-3" role="status">{[1, 2].map((item) => <div key={item} className="h-20 animate-pulse rounded-xl bg-slate-200/70" />)}</div> : documents.length === 0 ? <div className="mt-6"><EmptyState icon={FileText} title="No documents yet" description="Upload project documents to start building your AI knowledge base." /></div> : <Card className="mt-6 divide-y divide-slate-100 overflow-hidden">{documents.map((document) => { const config = statusConfig[document.status]; const StatusIcon = config.icon; return <div key={document.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-slate-100 text-ink-700"><FileText size={20} /></span><div className="min-w-0 flex-1"><p className="truncate text-sm font-bold">{document.filename}</p><p className="mt-1 text-xs text-ink-500">{formatSize(document.size_bytes)} · Uploaded {new Date(document.created_at).toLocaleDateString()}</p>{document.processing_error && <p className="mt-1 text-xs text-red-600">{document.processing_error}</p>}</div><div className="flex items-center justify-between gap-3 sm:justify-end"><Badge tone={config.tone}><StatusIcon className={document.status === 'PROCESSING' ? 'mr-1 animate-spin' : 'mr-1'} size={12} />{config.label}</Badge>{canWrite && <button onClick={() => void remove(document)} className="rounded-lg p-2 text-ink-500 hover:bg-red-50 hover:text-red-600" aria-label={`Delete ${document.filename}`}><Trash2 size={17} /></button>}</div></div> })}</Card>}
    </section>
  )
}
