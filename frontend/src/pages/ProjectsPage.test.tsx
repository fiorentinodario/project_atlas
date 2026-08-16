import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createProject, getProjects } from '../projects/api'
import { useAuth } from '../auth/useAuth'
import { ProjectsPage } from './ProjectsPage'

vi.mock('../auth/useAuth', () => ({ useAuth: vi.fn() }))
vi.mock('../projects/api', () => ({ getProjects: vi.fn(), createProject: vi.fn() }))

const project = {
  id: 'project-id',
  name: 'Merchant Portal',
  description: 'Partner workspace',
  status: 'ACTIVE' as const,
  role: 'OWNER' as const,
  owner: { id: 'user-id', display_name: 'Dario' },
  created_at: '2026-08-16T12:00:00+00:00',
  updated_at: '2026-08-16T12:00:00+00:00',
}

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'user-id', email: 'dario@example.com', display_name: 'Dario' },
      accessToken: 'access-token',
      isInitializing: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })
    vi.mocked(getProjects).mockResolvedValue({
      data: { items: [], pagination: { page: 1, per_page: 20, total: 0, pages: 0 } },
    })
    vi.mocked(createProject).mockResolvedValue({ data: { project } })
  })

  it('creates a project from the empty state', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><ProjectsPage /></MemoryRouter>)
    await screen.findByText('No projects yet')

    await user.click(screen.getByRole('button', { name: 'Create first project' }))
    await user.type(screen.getByLabelText('Project name'), 'Merchant Portal')
    await user.type(screen.getByLabelText('Description'), 'Partner workspace')
    await user.click(screen.getByRole('button', { name: 'Create project' }))

    expect(createProject).toHaveBeenCalledWith(
      { name: 'Merchant Portal', description: 'Partner workspace' },
      'access-token',
    )
    expect(await screen.findByRole('heading', { name: 'Merchant Portal' })).toBeInTheDocument()
  })
})
