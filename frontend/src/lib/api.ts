const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:5000/api/v1'

type ErrorPayload = {
  error?: {
    code?: string
    message?: string
  }
}

export class ApiClientError extends Error {
  code: string
  status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'ApiClientError'
    this.code = code
    this.status = status
  }
}

function cookieValue(name: string): string | undefined {
  return document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith(`${name}=`))
    ?.split('=')
    .slice(1)
    .join('=')
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  accessToken?: string,
): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body) headers.set('Content-Type', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (path === '/auth/refresh' || path === '/auth/logout') {
    const csrfToken = cookieValue('csrf_refresh_token')
    if (csrfToken) headers.set('X-CSRF-TOKEN', csrfToken)
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers,
  })
  const payload = (await response.json().catch(() => ({}))) as T & ErrorPayload

  if (!response.ok) {
    throw new ApiClientError(
      payload.error?.message ?? 'The request could not be completed.',
      payload.error?.code ?? 'REQUEST_FAILED',
      response.status,
    )
  }
  return payload
}
