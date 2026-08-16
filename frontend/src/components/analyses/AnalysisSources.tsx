import { FileText } from 'lucide-react'
import type { AnalysisSource } from '../../analyses/types'

export function AnalysisSources({ sources }: { sources: AnalysisSource[] }) {
  if (sources.length === 0) return null
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {sources.map((source) => (
        <details key={source.chunk_id} className="group rounded-lg bg-white ring-1 ring-slate-200">
          <summary className="flex cursor-pointer list-none items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-ink-500">
            <FileText size={12} />
            [{source.number}] {source.filename}{source.page_number ? ` · p. ${source.page_number}` : ''}
          </summary>
          <p className="max-w-lg border-t border-slate-100 px-3 py-2 text-xs leading-5 text-ink-500">
            {source.excerpt}
          </p>
        </details>
      ))}
    </div>
  )
}
