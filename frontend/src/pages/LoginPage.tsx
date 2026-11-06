import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, login } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'
import AuthLayout, { AuthArrow } from '../layout/AuthLayout'

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
    <AuthLayout mode="login">
      <form className="producer-auth-form" onSubmit={onSubmit} aria-busy={busy}>
        <h1>{t.auth.loginTitle}</h1>
        <p className="producer-auth-intro">{t.auth.loginIntro}</p>
        <label className="producer-auth-field">
          {t.auth.email}
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" placeholder={t.auth.emailPlaceholder} />
        </label>
        <label className="producer-auth-field">
          {t.auth.password}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            placeholder={t.auth.passwordPlaceholder}
          />
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="producer-auth-submit" type="submit" disabled={busy}>
          {busy ? t.auth.signingIn : t.auth.submitLogin}<span><AuthArrow /></span>
        </button>
        <p className="producer-auth-switch">
          {t.auth.noAccount} <Link to="/registro">{t.nav.register}</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
