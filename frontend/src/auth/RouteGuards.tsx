import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './useAuth'

function SessionLoading() {
  return (
    <div className="grid min-h-screen place-items-center bg-canvas" role="status">
      <div className="text-center">
        <span className="mx-auto block size-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
        <p className="mt-3 text-sm font-medium text-ink-500">Restoring your workspace...</p>
      </div>
    </div>
  )
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isInitializing } = useAuth()
  const location = useLocation()

  if (isInitializing) return <SessionLoading />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

export function GuestRoute({ children }: { children: ReactNode }) {
  const { user, isInitializing } = useAuth()

  if (isInitializing) return <SessionLoading />
  if (user) return <Navigate to="/" replace />
  return children
}
