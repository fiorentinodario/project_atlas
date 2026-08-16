import { FileSearch, LoaderCircle, Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useAuth } from '../../auth/useAuth'
import { searchDocuments } from '../../documents/api'
import type { SemanticSearchResult } from '../../documents/types'
import { ApiClientError } from '../../lib/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

export function SemanticSearch({ projectId }: { projectId: string }) {
  const { accessToken } = useAuth()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SemanticSearchResult[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSearching, setSearching] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!accessToken || query.trim().length < 2) return
    setSearching(true)
    setError(null)
    try {
      const response = await searchDocuments(projectId, query.trim(), accessToken)
      setResults(response.data.items)
    } catch (caughtError) {
      setResults(null)
      setError(
        caughtError instanceof ApiClientError
          ? caughtError.message
          : 'Unable to search project documents.',
      )
    } finally {
      setSearching(false)
    }
  }

  return (
    <Card className="mb-6 p-5">
      <div className="flex items-start gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
          <FileSearch size={19} />
        </span>
        <div>
          <h2 className="font-bold">Search your knowledge base</h2>
          <p className="mt-1 text-sm text-ink-500">
            Find relevant passages across the documents in this project.
          </p>
        </div>
      </div>
      <form className="mt-4 flex flex-col gap-2 sm:flex-row" onSubmit={submit}>
        <label className="sr-only" htmlFor="semantic-search">Search documents</label>
        <input
          id="semantic-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="e.g. How does authentication work?"
          className="min-h-10 flex-1 rounded-xl border border-slate-200 px-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
        />
        <Button disabled={isSearching || query.trim().length < 2}>
          {isSearching ? <LoaderCircle className="animate-spin" size={17} /> : <Search size={17} />}
          Search
        </Button>
      </form>
      {error && <p role="alert" className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">{error}</p>}
      {results?.length === 0 && <p className="mt-4 text-sm text-ink-500">No relevant passages found.</p>}
      {results && results.length > 0 && (
        <div className="mt-5 space-y-3">
          {results.map((result) => (
            <article key={result.chunk_id} className="rounded-xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-500">
                <span className="font-semibold text-ink-700">{result.document.filename}{result.page_number ? ` · Page ${result.page_number}` : ''}</span>
                <span>{Math.round(result.score * 100)}% match</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-ink-700">{result.content}</p>
            </article>
          ))}
        </div>
      )}
    </Card>
  )
}
