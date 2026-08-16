import { useState, type FormEvent } from 'react'
import { ApiClientError } from '../../lib/api'
import { createTask, updateTask } from '../../tasks/api'
import type { Task, TaskInput, TaskPriority, TaskStatus } from '../../tasks/types'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Modal } from '../ui/Modal'

type Props = {
  accessToken: string
  projectId: string
  task: Task | null
  onClose: () => void
  onSaved: (task: Task) => void
}

function localDateTime(value: string | null) {
  if (!value) return ''
  const date = new Date(value)
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export function TaskFormModal({ accessToken, onClose, onSaved, projectId, task }: Props) {
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    const data = new FormData(event.currentTarget)
    const dueDate = String(data.get('due_date'))
    const input: TaskInput = {
      title: String(data.get('title')),
      description: String(data.get('description')),
      status: String(data.get('status')) as TaskStatus,
      priority: String(data.get('priority')) as TaskPriority,
      due_date: dueDate ? new Date(dueDate).toISOString() : null,
    }
    try {
      const response = task
        ? await updateTask(task.id, input, accessToken)
        : await createTask(projectId, input, accessToken)
      onSaved(response.data.task)
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to save the task.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal isOpen onClose={onClose} title={task ? 'Edit task' : 'Create a task'} description="Keep the task focused, actionable and easy to prioritize.">
      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <Input id="task-title" name="title" label="Title" defaultValue={task?.title} minLength={2} maxLength={200} required autoFocus />
        <div><label htmlFor="task-description" className="mb-2 block text-sm font-semibold text-ink-700">Description</label><textarea id="task-description" name="description" defaultValue={task?.description ?? ''} rows={3} maxLength={5000} className="w-full resize-none rounded-xl border border-slate-200 px-4 py-3 text-sm" /></div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div><label htmlFor="task-status" className="mb-2 block text-sm font-semibold text-ink-700">Status</label><select id="task-status" name="status" defaultValue={task?.status ?? 'TODO'} className="h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"><option value="TODO">To do</option><option value="IN_PROGRESS">In progress</option><option value="DONE">Done</option></select></div>
          <div><label htmlFor="task-priority" className="mb-2 block text-sm font-semibold text-ink-700">Priority</label><select id="task-priority" name="priority" defaultValue={task?.priority ?? 'MEDIUM'} className="h-12 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="URGENT">Urgent</option></select></div>
        </div>
        <Input id="task-due-date" name="due_date" label="Due date" type="datetime-local" defaultValue={localDateTime(task?.due_date ?? null)} />
        <div className="flex justify-end gap-3 pt-2"><Button type="button" variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : 'Save task'}</Button></div>
      </form>
    </Modal>
  )
}
