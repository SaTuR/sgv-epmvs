const API_URL = import.meta.env.VITE_API_URL || '/api'

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('sgv_token')
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'Error de comunicación con el servidor')
  }
  return response.json()
}
