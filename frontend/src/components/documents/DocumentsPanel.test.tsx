import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuth } from '../../auth/useAuth'
import { getDocuments, uploadDocument } from '../../documents/api'
import { DocumentsPanel } from './DocumentsPanel'

vi.mock('../../auth/useAuth', () => ({ useAuth: vi.fn() }))
vi.mock('../../documents/api', () => ({
  getDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  searchDocuments: vi.fn(),
}))

describe('DocumentsPanel', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'user-id', email: 'dario@example.com', display_name: 'Dario' },
      accessToken: 'access-token',
      isInitializing: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })
    vi.mocked(getDocuments).mockResolvedValue({ data: { items: [] } })
  })

  it('uploads and displays a ready text document', async () => {
    const user = userEvent.setup()
    const document = {
      id: 'document-id',
      project_id: 'project-id',
      filename: 'requirements.txt',
      mime_type: 'text/plain',
      size_bytes: 12,
      status: 'READY' as const,
      processing_error: null,
      indexed_at: '2026-08-16T12:00:00Z',
      indexing_error: null,
      created_at: '2026-08-16T12:00:00Z',
      updated_at: '2026-08-16T12:00:00Z',
    }
    vi.mocked(uploadDocument).mockResolvedValue({ data: { document } })
    render(<DocumentsPanel projectId="project-id" role="OWNER" />)
    await screen.findByText('No documents yet')

    const file = new File(['requirements'], 'requirements.txt', { type: 'text/plain' })
    await user.upload(screen.getByLabelText('Upload document'), file)

    expect(uploadDocument).toHaveBeenCalledWith('project-id', file, 'access-token')
    expect(await screen.findByText('requirements.txt')).toBeInTheDocument()
    expect(screen.getByText('Ready')).toBeInTheDocument()
  })
})
