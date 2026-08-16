import { Bot, FileText, LoaderCircle, Send, Sparkles, UserRound } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { askProjectAssistant } from '../../assistant/api'
import type { AssistantMessage } from '../../assistant/types'
import { useAuth } from '../../auth/useAuth'
import { ApiClientError } from '../../lib/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

const suggestions = [
  'What are the main project requirements?',
  'Which tasks are still open?',
  'Summarize the authentication requirements.',
]

export function AssistantPanel({ projectId }: { projectId: string }) {
  const { accessToken } = useAuth()
  const [messages, setMessages] = useState<AssistantMessage[]>([])
  const [question, setQuestion] = useState('')
  const [isSending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function sendQuestion(event?: FormEvent, suggestedQuestion?: string) {
    event?.preventDefault()
    const content = (suggestedQuestion ?? question).trim()
    if (!accessToken || content.length < 2 || isSending) return

    const userMessage: AssistantMessage = { id: crypto.randomUUID(), role: 'user', content }
    setMessages((current) => [...current, userMessage])
    setQuestion('')
    setSending(true)
    setError(null)
    try {
      const history = messages.map(({ role, content: messageContent }) => ({
        role,
        content: messageContent,
      }))
      const response = await askProjectAssistant(projectId, content, history, accessToken)
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), ...response.data.message },
      ])
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiClientError
          ? caughtError.message
          : 'The AI assistant could not answer right now.',
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <Card className="flex min-h-[36rem] flex-col overflow-hidden">
      <header className="border-b border-slate-200 px-5 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-xl bg-brand-50 text-brand-700">
            <Sparkles size={19} />
          </span>
          <div>
            <h2 className="font-bold">Project AI Assistant</h2>
            <p className="text-xs text-ink-500">Answers are grounded in this project’s data.</p>
          </div>
        </div>
      </header>

      <div className="flex-1 space-y-5 overflow-y-auto p-5 sm:p-6" aria-live="polite">
        {messages.length === 0 && (
          <div className="mx-auto max-w-2xl py-10 text-center">
            <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-700">
              <Bot size={25} />
            </span>
            <h3 className="mt-5 text-lg font-bold">Ask about this project</h3>
            <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-ink-500">
              I’ll search uploaded documents and combine them with project tasks and decisions.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => void sendQuestion(undefined, suggestion)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs font-semibold text-ink-700 hover:border-brand-300 hover:bg-brand-50"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((message) => (
          <article
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}
          >
            {message.role === 'assistant' && (
              <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
                <Bot size={17} />
              </span>
            )}
            <div className={`max-w-3xl rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === 'user' ? 'bg-ink-950 text-white' : 'bg-slate-100 text-ink-700'}`}>
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.sources && message.sources.length > 0 && (
                <div className="mt-4 border-t border-slate-200 pt-3">
                  <p className="mb-2 text-xs font-bold uppercase tracking-wide text-ink-500">
                    Sources
                  </p>
                  <div className="space-y-2">
                    {message.sources.map((source) => (
                      <details key={source.chunk_id} className="rounded-xl bg-white p-3">
                        <summary className="flex cursor-pointer list-none items-center gap-2 text-xs font-semibold text-ink-700">
                          <span className="grid size-6 place-items-center rounded-lg bg-brand-50 text-brand-700">
                            {source.number}
                          </span>
                          <FileText size={14} />
                          <span className="min-w-0 flex-1 truncate">{source.filename}</span>
                          {source.page_number && <span className="text-ink-500">Page {source.page_number}</span>}
                        </summary>
                        <p className="mt-2 border-l-2 border-brand-200 pl-3 text-xs leading-5 text-ink-500">
                          {source.excerpt}
                        </p>
                      </details>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {message.role === 'user' && (
              <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-ink-950 text-white">
                <UserRound size={17} />
              </span>
            )}
          </article>
        ))}
        {isSending && (
          <div className="flex items-center gap-3 text-sm text-ink-500" role="status">
            <span className="grid size-9 place-items-center rounded-xl bg-brand-50 text-brand-700">
              <LoaderCircle className="animate-spin" size={17} />
            </span>
            Searching project knowledge…
          </div>
        )}
        {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </div>

      <form className="border-t border-slate-200 p-4 sm:p-5" onSubmit={(event) => void sendQuestion(event)}>
        <label htmlFor="assistant-question" className="sr-only">Ask the project assistant</label>
        <div className="flex items-end gap-2">
          <textarea
            id="assistant-question"
            rows={2}
            maxLength={1000}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question about this project…"
            className="min-h-12 flex-1 resize-none rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <Button aria-label="Send question" disabled={isSending || question.trim().length < 2}>
            <Send size={17} />
            <span className="hidden sm:inline">Send</span>
          </Button>
        </div>
        <p className="mt-2 text-xs text-ink-500">AI responses may be incomplete. Verify important project decisions.</p>
      </form>
    </Card>
  )
}
