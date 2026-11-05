import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, login } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'

export default function LoginPage() {
  const { setProducer } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      setProducer(await login(email, password))
      navigate('/painel')
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? err.message : t.auth.genericError)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <form className="card form" onSubmit={onSubmit}>
        <h1>{t.auth.loginTitle}</h1>
        <label>
          {t.auth.email}
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </label>
        <label>
          {t.auth.password}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {t.auth.submitLogin}
        </button>
        <p className="muted center">
          {t.auth.noAccount} <Link to="/registro">{t.nav.register}</Link>
        </p>
      </form>
    </main>
  )
}
