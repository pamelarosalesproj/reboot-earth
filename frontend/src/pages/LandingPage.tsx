import { Link } from 'react-router-dom'
import heroImg from '../assets/hero.jpg'
import { useAuth } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'
import './LandingPage.css'

function BuyerCta() {
  return (
    <Link to="/consulta" className="btn btn-light btn-lg buyer-cta">
      {t.landing.buyerCta} →
    </Link>
  )
}

function Cta() {
  const { producer } = useAuth()
  if (producer) {
    return (
      <div className="cta">
        <Link to="/painel" className="btn btn-primary btn-lg">
          {t.nav.panel}
        </Link>
      </div>
    )
  }
  return (
    <div className="cta">
      <Link to="/registro" className="btn btn-primary btn-lg">
        {t.nav.register}
      </Link>
      <Link to="/login" className="btn btn-light btn-lg">
        {t.nav.login}
      </Link>
    </div>
  )
}

const ICONS = ['🗺️', '🌳', '⚖️']

export default function LandingPage() {
  const L = t.landing
  return (
    <div className="landing">
      <section className="hero" style={{ backgroundImage: `url(${heroImg})` }}>
        <div className="hero-overlay" />
        <div className="hero-content">
          <span className="hero-brand">{t.appName}</span>
          <h1>{L.title}</h1>
          <p>{L.subtitle}</p>
          <Cta />
          <div className="cta">
            <BuyerCta />
          </div>
        </div>
      </section>

      <section className="section">
        <h2>{L.whatTitle}</h2>
        <div className="grid-3">
          {L.what.map((w, i) => (
            <div className="feature" key={w.title}>
              <span className="feature-icon" aria-hidden>
                {ICONS[i]}
              </span>
              <h3>{w.title}</h3>
              <p>{w.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section section-alt">
        <h2>{L.howTitle}</h2>
        <ol className="grid-3 steps">
          {L.how.map((s, i) => (
            <li className="step" key={s.title}>
              <span className="step-num">{i + 1}</span>
              <h3>{s.title}</h3>
              <p>{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="section buyers">
        <h2>{L.buyerTitle}</h2>
        <p>{L.buyerText}</p>
        <ul className="buyer-levels">
          {L.buyerLevels.map((b) => (
            <li key={b.level}>
              <span className={`status-badge ${b.level}`}>
                <span className="status-dot" aria-hidden="true" />
                {t.status.level[b.level]}
              </span>
              <span>{b.text}</span>
            </li>
          ))}
        </ul>
        <p className="muted">{L.buyerPrivacy}</p>
        <div className="cta">
          <BuyerCta />
        </div>
      </section>

      <section className="section source">
        <h2>{L.sourceTitle}</h2>
        <p>{L.sourceText}</p>
        <a href="https://alerta.mapbiomas.org" target="_blank" rel="noreferrer">
          {L.sourceLink} →
        </a>
      </section>

      <section className="section final-cta">
        <h2>{L.ctaTitle}</h2>
        <p>{L.ctaText}</p>
        <Cta />
      </section>

      <footer className="landing-footer">
        <span>{t.appName}</span>
        <span className="muted">Dados: MapBiomas Alerta · Mapas: © OpenStreetMap</span>
      </footer>
    </div>
  )
}
