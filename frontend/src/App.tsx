import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import { RequireAuth, useAuth } from './auth/AuthContext'
import { t } from './i18n/pt-BR'
import AppLayout from './layout/AppLayout'
import CarDetailPage from './pages/CarDetailPage'
import CarsPage from './pages/CarsPage'
import HomePage from './pages/HomePage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

/** Cabecera de las páginas públicas (la landing y el panel tienen la suya). */
function Header() {
  const { producer } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  if (pathname === '/' || pathname.startsWith('/painel')) return null

  return (
    <header className="topbar">
      <Link to="/" className="brand">
        {t.appName}
      </Link>
      <nav>
        {producer ? (
          <button className="btn btn-primary" onClick={() => navigate('/painel')}>
            {t.nav.panel}
          </button>
        ) : (
          <>
            <Link to="/login" className="btn btn-ghost">
              {t.nav.login}
            </Link>
            <Link to="/registro" className="btn btn-primary">
              {t.nav.register}
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}

function LegacyCarRedirect() {
  const { code = '' } = useParams()
  return <Navigate to={`/painel/cars/${encodeURIComponent(code)}`} replace />
}

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/registro" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/painel"
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="cars" element={<CarsPage />} />
          <Route path="cars/:code" element={<CarDetailPage />} />
        </Route>
        <Route path="/car/:code" element={<LegacyCarRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}
