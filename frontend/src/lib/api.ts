export type User = { id: number; name: string; email: string; role: 'student' | 'trainer' }

const KEY = 'ctwin_user'
// Leave this empty in local development to use Vite's proxy. Set it to the
// backend origin when the frontend and API are served from different hosts.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export function apiUrl(path: string) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(KEY)
  return raw ? (JSON.parse(raw) as User) : null
}

export function storeUser(u: User | null) {
  if (!u) localStorage.removeItem(KEY)
  else localStorage.setItem(KEY, JSON.stringify(u))
}

export class ApiError extends Error {
  code: string
  status: number
  constructor(code: string, message: string, status: number) {
    super(message)
    this.code = code
    this.status = status
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const user = getStoredUser()
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (user) headers.set('X-User-Id', String(user.id))
  const res = await fetch(apiUrl(path), { ...init, headers })
  const text = await res.text()
  let data: unknown = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      throw new ApiError('INVALID_RESPONSE', 'The server returned an invalid response.', res.status)
    }
  }
  if (!res.ok) {
    const err = (data as { error?: { code?: string; message?: string } } | null)?.error
    throw new ApiError(err?.code || 'ERROR', err?.message || res.statusText, res.status)
  }
  return data as T
}
