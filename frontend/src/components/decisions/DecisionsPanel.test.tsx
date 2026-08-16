import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuth } from '../../auth/useAuth'
import { detectDecisions, getDecisions, reviewDecision } from '../../decisions/api'
import type { ProjectDecision } from '../../decisions/types'
import { DecisionsPanel } from './DecisionsPanel'

vi.mock('../../auth/useAuth', () => ({ useAuth: vi.fn() }))
vi.mock('../../decisions/api', () => ({
  getDecisions: vi.fn(),
  createDecision: vi.fn(),
  updateDecision: vi.fn(),
  deleteDecision: vi.fn(),
  detectDecisions: vi.fn(),
  reviewDecision: vi.fn(),
}))

const pendingDecision: ProjectDecision = {
  id: 'decision-id',
  project_id: 'project-id',
  title: 'PostgreSQL selected',
  description: 'The team selected PostgreSQL as the primary database.',
  decision_date: '2026-08-16T12:00:00Z',
  origin: 'AI_DETECTED',
  status: 'PENDING',
  source: {
    document_id: 'document-id',
    filename: 'meeting-notes.txt',
    chunk_id: 'chunk-id',
    page_number: 1,
  },
  created_by: { id: 'user-id', display_name: 'Dario' },
  confirmed_by: null,
  confirmed_at: null,
  created_at: '2026-08-16T12:00:00Z',
  updated_at: '2026-08-16T12:00:00Z',
}

describe('DecisionsPanel', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'user-id', email: 'dario@example.com', display_name: 'Dario' },
      accessToken: 'access-token',
      isInitializing: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })
    vi.mocked(getDecisions).mockResolvedValue({ data: { items: [] } })
  })

  it('detects an AI decision and requires explicit confirmation', async () => {
    const user = userEvent.setup()
    vi.mocked(detectDecisions).mockResolvedValue({ data: { items: [pendingDecision] } })
    vi.mocked(reviewDecision).mockResolvedValue({
      data: {
        decision: {
          ...pendingDecision,
          status: 'CONFIRMED',
          confirmed_by: { id: 'user-id', display_name: 'Dario' },
        },
      },
    })
    render(<DecisionsPanel projectId="project-id" role="OWNER" />)
    await screen.findByText('No project decisions yet')

    await user.click(screen.getByRole('button', { name: /Detect with AI/i }))

    expect(await screen.findByText('PostgreSQL selected')).toBeInTheDocument()
    expect(screen.getByText(/confirmation is required/i)).toBeInTheDocument()
    expect(screen.getByText('meeting-notes.txt · Page 1')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Confirm PostgreSQL selected' }))

    expect(reviewDecision).toHaveBeenCalledWith('decision-id', 'confirm', 'access-token')
    expect(await screen.findByText('CONFIRMED')).toBeInTheDocument()
  })
})
