import { useState, type FormEvent } from 'react'
import { createDecision, updateDecision } from '../../decisions/api'
import type { ProjectDecision } from '../../decisions/types'
import { ApiClientError } from '../../lib/api'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Modal } from '../ui/Modal'

type Props = {
  accessToken: string
  projectId: string
  decision: ProjectDecision | null
  onClose: () => void
  onSaved: (decision: ProjectDecision) => void
}

export function DecisionFormModal({ accessToken, projectId, decision, onClose, onSaved }: Props) {
  const [title, setTitle] = useState(decision?.title ?? '')
  const [description, setDescription] = useState(decision?.description ?? '')
  const [date, setDate] = useState(
    decision ? new Date(decision.decision_date).toISOString().slice(0, 16) : '',
  )
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setSaving] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    const data = {
      title: title.trim(),
      description: description.trim(),
      ...(date ? { decision_date: new Date(date).toISOString() } : {}),
    }
    try {
      const response = decision
        ? await updateDecision(decision.id, data, accessToken)
        : await createDecision(projectId, data, accessToken)
      onSaved(response.data.decision)
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiClientError
          ? caughtError.message
          : 'Unable to save the decision.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      isOpen
      onClose={onClose}
      title={decision ? 'Edit decision' : 'Record a decision'}
      description="Store an explicit project choice so the team and AI assistant can rely on it."
    >
      <form className="mt-5 space-y-4" onSubmit={(event) => void submit(event)}>
        <Input
          id="decision-title"
          label="Title"
          value={title}
          minLength={2}
          maxLength={200}
          required
          onChange={(event) => setTitle(event.target.value)}
          placeholder="e.g. PostgreSQL selected as primary database"
        />
        <div>
          <label htmlFor="decision-description" className="mb-2 block text-sm font-semibold text-ink-700">Description</label>
          <textarea
            id="decision-description"
            value={description}
            minLength={2}
            maxLength={5000}
            required
            rows={5}
            onChange={(event) => setDescription(event.target.value)}
            className="w-full resize-y rounded-xl border border-slate-200 px-4 py-3 text-sm"
            placeholder="Explain what was decided and why."
          />
        </div>
        <Input
          id="decision-date"
          label="Decision date (optional)"
          type="datetime-local"
          value={date}
          onChange={(event) => setDate(event.target.value)}
        />
        {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button disabled={isSaving || title.trim().length < 2 || description.trim().length < 2}>
            {isSaving ? 'Saving…' : 'Save decision'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
