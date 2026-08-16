import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { createTask } from '../../tasks/api'
import { TaskFormModal } from './TaskFormModal'

vi.mock('../../tasks/api', () => ({ createTask: vi.fn(), updateTask: vi.fn() }))

describe('TaskFormModal', () => {
  it('creates a task with validated form values', async () => {
    const user = userEvent.setup()
    const onSaved = vi.fn()
    const task = {
      id: 'task-id',
      project_id: 'project-id',
      title: 'Build task API',
      description: '',
      status: 'TODO' as const,
      priority: 'HIGH' as const,
      due_date: null,
      assigned_user: null,
      created_by: { id: 'user-id', display_name: 'Dario' },
      source: 'MANUAL' as const,
      source_analysis_id: null,
      source_suggestion_index: null,
      created_at: '2026-08-16T12:00:00Z',
      updated_at: '2026-08-16T12:00:00Z',
    }
    vi.mocked(createTask).mockResolvedValue({ data: { task } })

    render(
      <TaskFormModal
        accessToken="access-token"
        projectId="project-id"
        task={null}
        onClose={vi.fn()}
        onSaved={onSaved}
      />,
    )
    await user.type(screen.getByLabelText('Title'), 'Build task API')
    await user.selectOptions(screen.getByLabelText('Priority'), 'HIGH')
    await user.click(screen.getByRole('button', { name: 'Save task' }))

    expect(createTask).toHaveBeenCalledWith(
      'project-id',
      {
        title: 'Build task API',
        description: '',
        status: 'TODO',
        priority: 'HIGH',
        due_date: null,
      },
      'access-token',
    )
    expect(onSaved).toHaveBeenCalledWith(task)
  })
})
