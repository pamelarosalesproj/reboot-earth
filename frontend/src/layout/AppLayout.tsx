import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'
import { maskCnpj } from '../lib/car'
import './AppLayout.css'

/** Iniciales a partir del email (el sistema aún no guarda foto de usuario). */
export function initials(email: string) {
  const name = email.split('@')[0]
  const parts = name.split(/[._\-+]+/).filter(Boolean)
  const letters = parts.length >= 2 ? parts[0][0] + parts[1][0] : name.slice(0, 2)
  return letters.toUpperCase()
}

export default function AppLayout() {
  const { producer, signOut } = useAuth()
  const navigate = useNavigate()
  if (!producer) return null

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand"><span className="sidebar-brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M19 4C9 2 3 7 5 14s14 9 14-10ZM4 21 15 10M9 16v-5m0 5h5" /></svg></span>{t.appName}</div>
        <span className="sidebar-section-label">{t.home.workspace}</span>

        <div className="profile">
          <div className="avatar" aria-hidden>
            {initials(producer.email)}
          </div>
          <div className="profile-text">
            <strong title={producer.email}>{producer.email}</strong>
            <span className="muted small">CNPJ {maskCnpj(producer.cnpj)}</span>
          </div>
        </div>

        <nav className="side-nav" aria-label={t.home.navigation}>
          <NavLink to="/painel" end>
            <span aria-hidden>▦</span> {t.sidebar.home}
          </NavLink>
          <NavLink to="/painel/cars">
            <span aria-hidden>⌖</span> {t.sidebar.cars}
          </NavLink>
        </nav>

        <p className="sidebar-note">{t.home.sidebarNote}</p>
        <button
          className="btn btn-ghost sidebar-logout"
          onClick={async () => {
            await signOut()
            navigate('/')
          }}
        >
          {t.nav.logout}
        </button>
      </aside>

      <div className="app-main">
        <Outlet />
      </div>
    </div>
  )
}
