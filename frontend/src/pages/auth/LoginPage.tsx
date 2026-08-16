import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, AlertCircle } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'
import { ApiClientError } from '../../lib/api'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { AuthLayout } from './AuthLayout'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    const data = new FormData(event.currentTarget)
    try {
      await login({ email: String(data.get('email')), password: String(data.get('password')) })
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/'
      navigate(destination, { replace: true })
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to sign in. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <p className="text-sm font-semibold text-brand-600">Welcome back</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">Sign in to your workspace</h1>
      <p className="mt-3 text-sm leading-6 text-ink-500">Continue managing your projects and knowledge base.</p>
      {error && <div role="alert" className="mt-6 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="mt-0.5 shrink-0" size={17} />{error}</div>}
      <form className="mt-7 space-y-5" onSubmit={handleSubmit}>
        <Input id="email" name="email" label="Email address" type="email" autoComplete="email" placeholder="you@company.com" required />
        <Input id="password" name="password" label="Password" type="password" autoComplete="current-password" placeholder="Enter your password" required />
        <Button type="submit" className="w-full" disabled={isSubmitting}>{isSubmitting ? 'Signing in...' : 'Sign in'} {!isSubmitting && <ArrowRight size={17} />}</Button>
      </form>
      <p className="mt-7 text-center text-sm text-ink-500">New to ProjectAtlas? <Link to="/register" className="font-semibold text-brand-700 hover:underline">Create an account</Link></p>
    </AuthLayout>
  )
}
