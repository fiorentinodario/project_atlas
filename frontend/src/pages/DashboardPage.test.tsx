import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuth } from '../auth/useAuth'
import { getDashboard } from '../dashboard/api'
import { DashboardPage } from './DashboardPage'

vi.mock('../auth/useAuth', () => ({ useAuth: vi.fn() }))
vi.mock('../dashboard/api', () => ({ getDashboard: vi.fn() }))

function renderDashboard() {
  return render(<MemoryRouter><DashboardPage /></MemoryRouter>)
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'user-id', email: 'dario@example.com', display_name: 'Dario' },
      accessToken: 'access-token', isInitializing: false,
      login: vi.fn(), register: vi.fn(), logout: vi.fn(),
    })
  })

  it('renders live statistics and recent project activity', async () => {
    vi.mocked(getDashboard).mockResolvedValue({ data: {
      stats: { active_projects: 1, total_tasks: 2, tasks_in_progress: 1, completed_tasks: 1 },
      recent_projects: [{ id: 'project-id', name: 'Atlas', description: 'Knowledge platform', status: 'ACTIVE', task_count: 2, document_count: 1, progress: 50, updated_at: '2026-08-16T12:00:00Z' }],
      recent_activity: [{ id: 'activity-id', action: 'TASK_COMPLETED', metadata: {}, created_at: '2026-08-16T12:00:00Z', project: { id: 'project-id', name: 'Atlas' }, actor: { id: 'user-id', display_name: 'Dario' } }],
    } })
    renderDashboard()

    expect(await screen.findByText('Good morning, Dario')).toBeInTheDocument()
    expect(screen.getByText('Knowledge platform')).toBeInTheDocument()
    expect(screen.getByText(/completed a task/i)).toBeInTheDocument()
  })

  it('shows a useful empty state', async () => {
    vi.mocked(getDashboard).mockResolvedValue({ data: {
      stats: { active_projects: 0, total_tasks: 0, tasks_in_progress: 0, completed_tasks: 0 },
      recent_projects: [], recent_activity: [],
    } })
    renderDashboard()
    expect(await screen.findByText('No projects yet')).toBeInTheDocument()
  })
})
