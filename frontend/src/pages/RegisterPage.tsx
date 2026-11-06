import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, register } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'
import { maskCnpj } from '../lib/car'
import type { ApiValidationError } from '../types'
import AuthLayout, { AuthArrow } from '../layout/AuthLayout'

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
    <AuthLayout mode="register">
      <form className="producer-auth-form" onSubmit={onSubmit} noValidate aria-busy={busy}>
        <h1>{t.auth.registerTitle}</h1>
        <p className="producer-auth-intro">{t.auth.registerIntro}</p>

        <label className="producer-auth-field" htmlFor="register-email">
          {t.auth.email}
          <input
            type="email"
            id="register-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder={t.auth.emailPlaceholder}
            aria-invalid={fieldErrors.email ? true : undefined}
            aria-describedby={fieldErrors.email ? 'register-email-error' : undefined}
            className={fieldErrors.email ? 'invalid' : ''}
          />
          {fieldErrors.email && <span className="field-error" id="register-email-error">{fieldErrors.email}</span>}
        </label>

        <label className="producer-auth-field" htmlFor="register-cnpj">
          {t.auth.cnpj}
          <input
            inputMode="numeric"
            id="register-cnpj"
            value={cnpj}
            onChange={(e) => setCnpj(maskCnpj(e.target.value))}
            placeholder={t.auth.cnpjPlaceholder}
            aria-invalid={fieldErrors.cnpj ? true : undefined}
            aria-describedby={`register-cnpj-hint${fieldErrors.cnpj ? ' register-cnpj-error' : ''}`}
            required
            className={fieldErrors.cnpj ? 'invalid' : ''}
          />
          {fieldErrors.cnpj && <span className="field-error" id="register-cnpj-error">{fieldErrors.cnpj}</span>}
          <span className="field-hint" id="register-cnpj-hint">{t.auth.cnpjPublicNotice}</span>
        </label>

        <label className="producer-auth-field" htmlFor="register-password">
          {t.auth.password}
          <input
            type="password"
            id="register-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
            autoComplete="new-password"
            placeholder={t.auth.newPasswordPlaceholder}
            aria-invalid={fieldErrors.password ? true : undefined}
            aria-describedby={`register-password-hint${fieldErrors.password ? ' register-password-error' : ''}`}
            className={fieldErrors.password ? 'invalid' : ''}
          />
          <small className="field-hint" id="register-password-hint">{t.auth.passwordHint}</small>
          {fieldErrors.password && <span className="field-error" id="register-password-error">{fieldErrors.password}</span>}
        </label>

        {error && <p className="form-error" role="alert">{error}</p>}

        <button className="producer-auth-submit" type="submit" disabled={busy}>
          {busy ? t.auth.creatingAccount : t.auth.submitRegister}<span><AuthArrow /></span>
        </button>
        <p className="producer-auth-switch">
          {t.auth.hasAccount} <Link to="/login">{t.nav.login}</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
