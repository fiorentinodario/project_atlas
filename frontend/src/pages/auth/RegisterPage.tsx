import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowRight } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { ApiClientError } from '../../lib/api'
import { AuthLayout } from './AuthLayout'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    const data = new FormData(event.currentTarget)
    try {
      await register({
        display_name: String(data.get('display_name')),
        email: String(data.get('email')),
        password: String(data.get('password')),
      })
      navigate('/', { replace: true })
    } catch (caughtError) {
      setError(caughtError instanceof ApiClientError ? caughtError.message : 'Unable to create your account. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <p className="text-sm font-semibold text-brand-600">Start building context</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">Create your account</h1>
      <p className="mt-3 text-sm leading-6 text-ink-500">Set up your workspace and bring your first project into focus.</p>
      {error && <div role="alert" className="mt-6 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="mt-0.5 shrink-0" size={17} />{error}</div>}
      <form className="mt-7 space-y-4" onSubmit={handleSubmit}>
        <Input id="display_name" name="display_name" label="Full name" autoComplete="name" placeholder="Dario Fiorentino" minLength={2} maxLength={120} required />
        <Input id="email" name="email" label="Email address" type="email" autoComplete="email" placeholder="you@company.com" required />
        <Input id="password" name="password" label="Password" type="password" autoComplete="new-password" placeholder="At least 12 characters" minLength={12} maxLength={128} required />
        <p className="text-xs leading-5 text-ink-500">Use 12–128 characters with at least one letter and one number.</p>
        <Button type="submit" className="w-full" disabled={isSubmitting}>{isSubmitting ? 'Creating account...' : 'Create account'} {!isSubmitting && <ArrowRight size={17} />}</Button>
      </form>
      <p className="mt-7 text-center text-sm text-ink-500">Already have an account? <Link to="/login" className="font-semibold text-brand-700 hover:underline">Sign in</Link></p>
    </AuthLayout>
  )
}
