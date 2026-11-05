import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, register } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'
import { maskCnpj } from '../lib/car'
import type { ApiValidationError } from '../types'

export default function RegisterPage() {
  const { setProducer } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [cnpj, setCnpj] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<ReactNode>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    setBusy(true)
    try {
      setProducer(await register({ email, password, cnpj }))
      navigate('/painel') // los CARs se añaden en el panel
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError(
          <>
            {t.auth.emailTaken} <Link to="/login">{t.nav.login}</Link>
          </>,
        )
      } else if (err instanceof ApiError && err.status === 422) {
        const body = err.body as ApiValidationError
        if (body.field) setFieldErrors({ [body.field]: body.detail })
        else setError(body.detail)
      } else {
        setError(t.auth.genericError)
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <form className="card form" onSubmit={onSubmit} noValidate>
        <h1>{t.auth.registerTitle}</h1>
        <p className="muted form-intro">{t.auth.registerIntro}</p>

        <label>
          {t.auth.email}
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className={fieldErrors.email ? 'invalid' : ''}
          />
          {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
        </label>

        <label>
          {t.auth.cnpj}
          <input
            inputMode="numeric"
            value={cnpj}
            onChange={(e) => setCnpj(maskCnpj(e.target.value))}
            placeholder="00.000.000/0000-00"
            required
            className={fieldErrors.cnpj ? 'invalid' : ''}
          />
          {fieldErrors.cnpj && <span className="field-error">{fieldErrors.cnpj}</span>}
          <span className="field-hint">{t.auth.cnpjPublicNotice}</span>
        </label>

        <label>
          {t.auth.password}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
            autoComplete="new-password"
            className={fieldErrors.password ? 'invalid' : ''}
          />
          <small className="muted">{t.auth.passwordHint}</small>
          {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
        </label>

        {error && <p className="form-error">{error}</p>}

        <button className="btn btn-primary" type="submit" disabled={busy}>
          {t.auth.submitRegister}
        </button>
        <p className="muted center">
          {t.auth.hasAccount} <Link to="/login">{t.nav.login}</Link>
        </p>
      </form>
    </main>
  )
}
