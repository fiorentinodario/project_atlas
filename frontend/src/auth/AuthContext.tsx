import { useEffect, useRef, useState, type ReactNode } from 'react'
import { apiRequest } from '../lib/api'
import type { AuthResponse, User } from './types'
import { AuthContext } from './useAuth'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isInitializing, setInitializing] = useState(true)
  const hasInitialized = useRef(false)

  useEffect(() => {
    if (hasInitialized.current) return
    hasInitialized.current = true

    async function restoreSession() {
      try {
        const refreshed = await apiRequest<{ data: { access_token: string } }>('/auth/refresh', {
          method: 'POST',
        })
        const profile = await apiRequest<{ data: { user: User } }>(
          '/auth/me',
          {},
          refreshed.data.access_token,
        )
        setAccessToken(refreshed.data.access_token)
        setUser(profile.data.user)
      } catch {
        setAccessToken(null)
        setUser(null)
      } finally {
        setInitializing(false)
      }
    }

    void restoreSession()
  }, [])

  async function authenticate(path: '/auth/login' | '/auth/register', body: object) {
    const response = await apiRequest<AuthResponse>(path, {
      method: 'POST',
      body: JSON.stringify(body),
    })
    setAccessToken(response.data.access_token)
    setUser(response.data.user)
  }

  async function logout() {
    try {
      await apiRequest('/auth/logout', { method: 'POST' })
    } finally {
      setAccessToken(null)
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isInitializing,
        login: (credentials) => authenticate('/auth/login', credentials),
        register: (registration) => authenticate('/auth/register', registration),
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
