import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import * as api from '../api/client'
import type { Me } from '../types'

export interface AuthState {
  producer: Me | null
  loading: boolean
  setProducer: (me: Me | null) => void
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthState>({
  producer: null,
  loading: false,
  setProducer: () => {},
  signOut: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [producer, setProducer] = useState<Me | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .me()
      .then(setProducer)
      .catch(() => setProducer(null))
      .finally(() => setLoading(false))
  }, [])

  const signOut = useCallback(async () => {
    await api.logout().catch(() => {})
    setProducer(null)
  }, [])

  return <AuthContext.Provider value={{ producer, loading, setProducer, signOut }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)

/** Rutas protegidas: sin sesión → /login. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { producer, loading } = useAuth()
  if (loading) return <p className="muted center">Carregando…</p>
  if (!producer) return <Navigate to="/login" replace />
  return <>{children}</>
}
