import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { askProjectAssistant } from '../../assistant/api'
import { useAuth } from '../../auth/useAuth'
import { AssistantPanel } from './AssistantPanel'

vi.mock('../../assistant/api', () => ({ askProjectAssistant: vi.fn() }))
vi.mock('../../auth/useAuth', () => ({ useAuth: vi.fn() }))

describe('AssistantPanel', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'user-id', email: 'dario@example.com', display_name: 'Dario' },
      accessToken: 'access-token',
      isInitializing: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })
  })

  it('sends a project question and renders the grounded response', async () => {
    const user = userEvent.setup()
    vi.mocked(askProjectAssistant).mockResolvedValue({
      data: {
        message: { role: 'assistant', content: 'JWT authentication is required.' },
      },
    })
    render(<AssistantPanel projectId="project-id" />)

    await user.type(screen.getByLabelText('Ask the project assistant'), 'How do users log in?')
    await user.click(screen.getByRole('button', { name: 'Send question' }))

    expect(askProjectAssistant).toHaveBeenCalledWith(
      'project-id',
      'How do users log in?',
      [],
      'access-token',
    )
    expect(await screen.findByText('JWT authentication is required.')).toBeInTheDocument()
  })
})
