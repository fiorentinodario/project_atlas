import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getLatestAnalysis, runProjectAnalysis } from '../../analyses/api'
import type { ProjectAnalysis } from '../../analyses/types'
import { useAuth } from '../../auth/useAuth'
import { AnalysisPanel } from './AnalysisPanel'

vi.mock('../../analyses/api', () => ({
  getLatestAnalysis: vi.fn(),
  runProjectAnalysis: vi.fn(),
}))
vi.mock('../../auth/useAuth', () => ({ useAuth: vi.fn() }))

const analysis: ProjectAnalysis = {
  id: 'analysis-id',
  project_id: 'project-id',
  summary: 'ProjectAtlas is a secure project knowledge platform.',
  requirements: [
    {
      text: 'Users must authenticate with JWT.',
      sources: [
        {
          number: 1,
          chunk_id: 'chunk-id',
          document_id: 'document-id',
          filename: 'requirements.txt',
          page_number: 1,
          excerpt: 'Users must authenticate with JWT.',
        },
      ],
    },
  ],
  risks: [{ text: 'Token rotation is unclear.', severity: 'MEDIUM', sources: [] }],
  open_questions: [
    { text: 'What is the launch date?', reason: 'No deadline is documented.' },
  ],
  suggested_tasks: [
    {
      title: 'Document token rotation',
      description: 'Define refresh token rotation behavior.',
      priority: 'HIGH',
      reason: 'Authentication details are incomplete.',
      sources: [],
    },
  ],
  provider: 'fake',
  model: 'fake-model',
  requested_by: { id: 'user-id', display_name: 'Dario' },
  created_at: '2026-08-16T12:00:00Z',
}

describe('AnalysisPanel', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'user-id', email: 'dario@example.com', display_name: 'Dario' },
      accessToken: 'access-token',
      isInitializing: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })
    vi.mocked(getLatestAnalysis).mockResolvedValue({ data: { analysis: null } })
  })

  it('runs and displays a structured project analysis', async () => {
    const user = userEvent.setup()
    vi.mocked(runProjectAnalysis).mockResolvedValue({ data: { analysis } })
    render(<AnalysisPanel projectId="project-id" role="OWNER" />)
    await screen.findByText('No analysis available')

    await user.click(screen.getAllByRole('button', { name: 'Analyze project' })[0])

    expect(runProjectAnalysis).toHaveBeenCalledWith('project-id', 'access-token')
    expect(await screen.findByText(analysis.summary)).toBeInTheDocument()
    expect(screen.getAllByText('Users must authenticate with JWT.')).toHaveLength(2)
    expect(screen.getByText('Token rotation is unclear.')).toBeInTheDocument()
    expect(screen.getByText('What is the launch date?')).toBeInTheDocument()
    expect(screen.getByText('Document token rotation')).toBeInTheDocument()
    expect(screen.getByText('requirements.txt · p. 1', { exact: false })).toBeInTheDocument()
  })
})
