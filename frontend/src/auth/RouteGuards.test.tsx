import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ProtectedRoute } from './RouteGuards'
import { useAuth, type AuthContextValue } from './useAuth'

vi.mock('./useAuth', () => ({ useAuth: vi.fn() }))

const baseAuth: AuthContextValue = {
  user: null,
  accessToken: null,
  isInitializing: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

function renderProtectedRoute() {
  render(
    <MemoryRouter initialEntries={['/private']}>
      <Routes>
        <Route path="/login" element={<p>Sign in page</p>} />
        <Route
          path="/private"
          element={
            <ProtectedRoute>
              <p>Private workspace</p>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue(baseAuth)
  })

  it('redirects an anonymous visitor to sign in', () => {
    renderProtectedRoute()

    expect(screen.getByText('Sign in page')).toBeInTheDocument()
  })

  it('renders private content for an authenticated user', () => {
    vi.mocked(useAuth).mockReturnValue({
      ...baseAuth,
      accessToken: 'access-token',
      user: { id: 'user-id', email: 'user@example.com', display_name: 'Dario' },
    })

    renderProtectedRoute()

    expect(screen.getByText('Private workspace')).toBeInTheDocument()
  })

  it('shows a loading state while restoring the session', () => {
    vi.mocked(useAuth).mockReturnValue({ ...baseAuth, isInitializing: true })

    renderProtectedRoute()

    expect(screen.getByRole('status')).toHaveTextContent('Restoring your workspace')
  })
})
