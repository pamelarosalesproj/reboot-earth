import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'
import loginLandscape from '../assets/auth-login-crops.jpg'
import registerSoil from '../assets/auth-register-soil.jpg'
import { t } from '../i18n/pt-BR'
import './AuthLayout.css'

export function AuthArrow() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6" /></svg>
}

export default function AuthLayout({ mode, children }: { mode: 'login' | 'register'; children: ReactNode }) {
  const A = t.auth
  return (
    <div className={`producer-auth producer-auth-${mode}`}>
      <header className="producer-auth-header">
        <Link to="/" className="producer-auth-brand" aria-label={t.appName}>
          <span className="producer-auth-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M19 4C9 2 3 7 5 14s14 9 14-10ZM4 21 15 10M9 16v-5m0 5h5" /></svg>
          </span>
          {t.appName}
        </Link>
        <Link to="/" className="producer-auth-back"><AuthArrow />{A.backHome}</Link>
      </header>

      <main className="producer-auth-main">
        <aside className="producer-auth-story">
          <img src={mode === 'login' ? loginLandscape : registerSoil} alt="" width="1024" height="1536" />
          <div className="producer-auth-story-content">
            <span className="producer-auth-eyebrow">{t.landing.eyebrow}</span>
            <h2>{A.landscapeTitle}<br /><em>{A.landscapeAccent}</em></h2>
            <p>{mode === 'login' ? A.landscapeLogin : A.landscapeDescription}</p>
            <div className="producer-auth-source">
              <span className="producer-auth-eyebrow">{A.sourceLabel}</span>
              <p>{A.sourceDescription}</p>
            </div>
          </div>
          <p className="producer-auth-caption">{t.landing.imageCaption}</p>
        </aside>

        <div className="producer-auth-panel">
          <div className="producer-auth-form-wrap">
            <nav className="producer-auth-tabs" aria-label={A.navigation}>
              <NavLink to="/registro">{A.registerTitle}</NavLink>
              <NavLink to="/login">{A.loginTitle}</NavLink>
            </nav>
            <span className="producer-auth-eyebrow producer-auth-kicker"><span />{A.eyebrow}</span>
            {children}
            <div className="producer-auth-buyer">
              <span>{A.buyerPrompt}</span>
              <Link to="/consulta">{A.buyerLink}<AuthArrow /></Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
