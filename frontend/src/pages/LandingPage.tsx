import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import landscape from '../assets/landing-landscape.jpg'
import { useAuth } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'
import './LandingPage.css'

type IconName = 'leaf' | 'arrow' | 'map' | 'tree' | 'shield' | 'check'
function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  const paths: Record<IconName, ReactNode> = {
    leaf: <><path d="M19 4C9 2 3 7 5 14s14 9 14-10Z" /><path d="M4 21 15 10M9 16v-5m0 5h5" /></>,
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    map: <path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15" />,
    tree: <path d="m12 3-6 7h3l-5 6h6v5h4v-5h6l-5-6h3l-6-7Z" />,
    shield: <><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z" /><path d="m8 12 3 3 5-6" /></>,
    check: <path d="m5 12 4 4L19 6" />,
  }
  return <svg className={`re-icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}
function Brand() {
  return <Link to="/" className="re-brand" aria-label={t.appName}><span className="re-brand-mark"><Icon name="leaf" /></span><span>Reboot<span className="re-brand-light">Earth</span></span></Link>
}
function ProducerCta({ label }: { label?: string }) {
  const { producer } = useAuth()
  return <Link to={producer ? '/painel' : '/registro'} className="re-button re-button-primary">{producer ? t.nav.panel : label ?? t.nav.register}<span className="re-button-arrow"><Icon name="arrow" /></span></Link>
}
const L = t.landing
const featureIcons: IconName[] = ['map', 'tree', 'shield']

export default function LandingPage() {
  const { producer } = useAuth()
  return (
    <div className="re-landing">
      <a className="re-skip" href="#conteudo">{L.skip}</a>
      <header className="re-header">
        <Brand />
        <nav className="re-desktop-nav" aria-label={L.menu}>
          <a href="#plataforma">{L.platform}</a><a href="#como-funciona">{L.howTitle}</a><a href="#compradores">{L.forBuyers}</a>
        </nav>
        <div className="re-header-actions">{!producer && <Link className="re-login" to="/login">{t.nav.login}</Link>}<ProducerCta /></div>
        <details className="re-mobile-menu">
          <summary aria-label={L.menu}><span /><span /><span /></summary>
          <nav aria-label={L.menu}>
            <a href="#plataforma">{L.platform}</a><a href="#como-funciona">{L.howTitle}</a><a href="#compradores">{L.forBuyers}</a>
            <Link to="/consulta">{t.nav.search}</Link>{!producer && <Link to="/login">{t.nav.login}</Link>}
          </nav>
        </details>
      </header>
      <main id="conteudo">
        <section className="re-hero" aria-labelledby="re-hero-title">
          <div className="re-hero-copy">
            <span className="re-eyebrow"><span className="re-dot" />{L.eyebrow}</span>
            <h1 id="re-hero-title">{L.headline}<br /><em>{L.headlineAccent}</em></h1>
            <p>{L.description}</p>
            <div className="re-actions"><ProducerCta label={L.producerCta} /><Link to="/consulta" className="re-button re-button-outline">{t.nav.search}<Icon name="arrow" /></Link></div>
            <a href="#plataforma" className="re-explore">{L.explore}<span aria-hidden="true">↓</span></a>
          </div>
          <figure className="re-landscape">
            <img src={landscape} alt={L.imageAlt} fetchPriority="high" width="1536" height="1024" />
            <div className="re-landscape-message"><Icon name="leaf" /><span>{L.imageNote}<small>{L.imageNoteSub}</small></span></div>
            <figcaption>{L.imageCaption}</figcaption>
          </figure>
          <ul className="re-trust-strip">{L.trust.map(item => <li key={item}><Icon name="check" />{item}</li>)}</ul>
        </section>
        <section className="re-section" id="plataforma" aria-labelledby="re-features-title">
          <div className="re-section-heading"><span className="re-eyebrow">{L.featuresEyebrow}</span><h2 id="re-features-title">{L.featuresTitle}</h2><p>{L.featuresIntro}</p></div>
          <div className="re-feature-grid">{L.what.map((feature, i) => <article className={`re-feature re-feature-${i}`} key={feature.title}>
            <div className="re-feature-top"><span className="re-icon-tile"><Icon name={featureIcons[i]} /></span><span className="re-feature-index">0{i + 1}</span></div>
            <span className="re-eyebrow">{L.featureLabels[i]}</span><h3>{feature.title}</h3><p>{feature.text}</p>
            <div className={`re-feature-art re-feature-art-${i}`} aria-hidden="true">{i === 0 ? <><span /><span /><span /></> : i === 1 ? <><i /><i /><i /><i /><i /><i /><i /></> : <Icon name="shield" />}</div>
          </article>)}</div>
        </section>
        <section className="re-workflow" id="como-funciona" aria-labelledby="re-steps-title"><div className="re-section re-workflow-inner">
          <div className="re-workflow-heading"><span className="re-eyebrow">{L.producerEyebrow}</span><h2 id="re-steps-title">{L.howTitle}</h2><p>{L.stepsIntro}</p><ProducerCta /></div>
          <ol className="re-steps">{L.how.map((step, i) => <li key={step.title}><span className="re-step-number">0{i + 1}</span><div><h3>{step.title}</h3><p>{step.text}</p></div></li>)}</ol>
        </div></section>
        <section className="re-section re-buyers" id="compradores" aria-labelledby="re-buyers-title">
          <div className="re-buyer-copy"><span className="re-eyebrow">{L.buyerEyebrow}</span><h2 id="re-buyers-title">{L.buyerHeadline}</h2><h3>{L.buyerTitle}</h3><p>{L.buyerText}</p><Link to="/consulta" className="re-text-link">{L.buyerCta}<Icon name="arrow" /></Link><div className="re-privacy"><Icon name="shield" /><p>{L.buyerPrivacy}</p></div></div>
          <div className="re-level-panel"><div className="re-level-panel-head"><span>{t.status.title}</span><span className="re-eyebrow">{t.appName}</span></div><ul>{L.buyerLevels.map(item => <li key={item.level}><span className={`re-level re-level-${item.level}`}><span />{t.status.level[item.level]}</span><p>{item.text}</p></li>)}</ul><p className="re-level-note">{L.buyerNote}</p></div>
        </section>
        <section className="re-source" aria-labelledby="re-source-title"><div className="re-section">
          <div className="re-section-heading"><span className="re-eyebrow">{L.sourceEyebrow}</span><h2 id="re-source-title">{L.sourceHeadline}</h2><p>{L.sourceText}</p></div>
          <div className="re-principles">{L.sourcePrinciples.map((item, i) => <article key={item.title}><span className="re-principle-number">0{i + 1}</span><h3>{item.title}</h3><p>{item.text}</p></article>)}</div>
          <a className="re-text-link" href="https://alerta.mapbiomas.org" target="_blank" rel="noreferrer">{L.sourceLink}<Icon name="arrow" /></a>
        </div></section>
        <section className="re-section re-final" aria-labelledby="re-final-title"><span className="re-eyebrow">{L.finalEyebrow}</span><h2 id="re-final-title">{L.finalHeadline}</h2><p>{L.finalDescription}</p><div className="re-actions"><ProducerCta /><Link to="/consulta" className="re-button re-button-outline">{t.nav.search}<Icon name="arrow" /></Link></div><Icon name="leaf" className="re-final-leaf" /></section>
      </main>
      <footer className="re-footer"><div className="re-footer-top"><div><Brand /><p>{L.footerDescription}</p></div><nav aria-label={L.menu}><a href="#plataforma">{L.platform}</a><a href="#como-funciona">{L.howTitle}</a><Link to="/consulta">{t.nav.search}</Link></nav></div><div className="re-footer-bottom"><span>{L.footerNote}</span><span>{L.footerSources}</span></div></footer>
    </div>
  )
}
