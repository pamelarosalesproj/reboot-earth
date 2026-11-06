import BrandMark from '../components/BrandMark'
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import AuditReportModal from '../components/AuditReportModal'
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
  const [reportModalOpen, setReportModalOpen] = useState(false)
  if (!producer) return null

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand"><BrandMark inverse /><span className="elo-brand-name">{t.appName}</span></div>
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
          <NavLink to="/painel/nivel">
            <span aria-hidden>?</span> {t.sidebar.rules}
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

      <AuditReportModal isOpen={reportModalOpen} onClose={() => setReportModalOpen(false)} />
    </div>
  )
}
