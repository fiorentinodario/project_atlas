import { createContext, useContext } from 'react'
import type { Credentials, Registration, User } from './types'

export type AuthContextValue = {
  user: User | null
  accessToken: string | null
  isInitializing: boolean
  login: (credentials: Credentials) => Promise<void>
  register: (registration: Registration) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
