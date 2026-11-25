import axios from 'axios'

export type AppSession = {
  access: string
  refresh: string
  must_change_password?: boolean
  user: {
    id: number
    name: string
    email: string
    role: 'HOD' | 'TEACHER' | 'STUDENT'
    department?: { id: number; code: string; name: string } | null
  }
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api',
})

api.interceptors.request.use((config) => {
  const session = getSession()
  if (session?.access) {
    config.headers.Authorization = `Bearer ${session.access}`
  }
  return config
})

export function getSession(): AppSession | null {
  try {
    return JSON.parse(localStorage.getItem('aiems_session') || 'null') as AppSession | null
  } catch {
    return null
  }
}

export function saveSession(session: AppSession) {
  localStorage.setItem('aiems_session', JSON.stringify(session))
  api.defaults.headers.common.Authorization = `Bearer ${session.access}`
}

export function clearSession() {
  localStorage.removeItem('aiems_session')
  delete api.defaults.headers.common.Authorization
}
