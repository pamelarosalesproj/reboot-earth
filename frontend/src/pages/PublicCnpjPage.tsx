import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, getPublicCnpj } from '../api/client'
import CnpjReportCard from '../components/CnpjReportCard'
import CnpjSearch from '../components/CnpjSearch'
import { t } from '../i18n/pt-BR'
import { normalizeCnpj } from '../lib/cnpj'
import type { PublicCnpjReport } from '../types'
import { useAuth } from '../auth/AuthContext'
import './PublicCnpjPage.css'

const P = t.publicSearch

function SearchIcon() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg>
}

type Result = { key: string } & ({ kind: 'ok'; report: PublicCnpjReport } | { kind: 'error'; message: string })

function errorMessage(e: unknown) {
  if (e instanceof ApiError && e.status === 429) {
    const s = Number((e.body as { retry_after_s?: number } | null)?.retry_after_s ?? 3600)
    return P.rateLimited(Math.max(1, Math.ceil(s / 60)))
  }
  if (e instanceof ApiError && e.status === 422) return P.invalid
  return P.error
}

/** Página "Consultar CNPJ": pública en /consulta y dentro del panel en /painel/consulta. */
export default function PublicCnpjPage({ basePath = '/consulta' }: { basePath?: '/consulta' | '/painel/consulta' }) {
  const { cnpj = '' } = useParams()
  const digits = cnpj ? normalizeCnpj(cnpj) : null
  // El resultado se guarda con su CNPJ: una respuesta atrasada de otro CNPJ nunca se muestra.
  const [result, setResult] = useState<Result | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const { producer } = useAuth()
  const inPanel = basePath === '/painel/consulta'

  useEffect(() => {
    if (!digits) return
    let active = true
    getPublicCnpj(digits)
      .then((report) => { if (active) setResult({ key: digits, kind: 'ok', report }) })
      .catch((e) => { if (active) setResult({ key: digits, kind: 'error', message: errorMessage(e) }) })
    return () => { active = false }
  }, [digits, retryCount])

  const state = !cnpj
    ? null
    : !digits
      ? ({ kind: 'error', message: P.invalid } as const)
      : result?.key === digits
        ? result
        : ({ kind: 'loading' } as const)

  return (
    <div className={`cnpj-screen${inPanel ? ' cnpj-screen-in-panel' : ''}`}>
      {!inPanel && <header className="cnpj-header">
        <Link to="/" className="cnpj-brand" aria-label={t.appName}>
          <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M19 4C9 2 3 7 5 14s14 9 14-10ZM4 21 15 10M9 16v-5m0 5h5" /></svg></span>{t.appName}
        </Link>
        <nav aria-label={P.navigation}>
          <Link to="/" className="cnpj-back">{P.backHome}</Link>
          <Link to={producer ? '/painel' : '/login'} className="cnpj-header-action">{producer ? t.nav.panel : t.nav.login}<span aria-hidden="true">↗</span></Link>
        </nav>
      </header>}
      <main className="cnpj-main">
        <div className="cnpj-heading"><span className="cnpj-eyebrow"><span />{P.eyebrow}</span><h1>{P.title}<em>{P.headlineAccent}</em></h1><p>{P.subtitle}</p></div>
        <div className="cnpj-workspace">
          <section className="cnpj-search-panel" aria-label={P.title}>
            <div className="cnpj-search-note"><SearchIcon /><span>{P.searchNote}</span></div>
            <CnpjSearch key={cnpj} basePath={basePath} initialValue={digits ?? ''} />
            <div className="cnpj-result-area" aria-live="polite" aria-busy={state?.kind === 'loading'}>
              {!state && <div className="cnpj-empty"><span className="cnpj-empty-icon"><SearchIcon /></span><h2>{P.emptyTitle}</h2><p>{P.emptyText}</p></div>}
              {state?.kind === 'loading' && <div className="cnpj-loading" role="status"><span className="cnpj-loader" aria-hidden="true" /><h2>{P.loading}</h2><p>{P.loadingHint}</p></div>}
              {state?.kind === 'error' && <div className="cnpj-error"><div role="alert"><h2>{P.errorTitle}</h2><p>{state.message}</p></div>{digits && <button type="button" onClick={() => { setResult(null); setRetryCount(count => count + 1) }}>{P.retry}</button>}</div>}
              {state?.kind === 'ok' && <CnpjReportCard report={state.report} />}
            </div>
          </section>
          <aside className="cnpj-guide">
            <span className="cnpj-eyebrow">{t.landing.sourceEyebrow}</span><h2>{P.guideTitle}</h2>
            <ol>{P.guideItems.map((item, i) => <li key={item.title}><span>0{i + 1}</span><div><h3>{item.title}</h3><p>{item.text}</p></div></li>)}</ol>
            <details className="cnpj-level-guide"><summary>{P.levelsTitle}</summary><ul>{t.landing.buyerLevels.map(item => <li className={`cnpj-level-guide-${item.level}`} key={item.level}>{`${t.status.level[item.level]}: ${item.text}`}</li>)}</ul><p>{P.provisionalNote}</p></details>
          </aside>
        </div>
        {!inPanel && <footer className="cnpj-footer"><span>{P.producerPrompt}</span><Link to={producer ? '/painel' : '/registro'}>{P.producerLink}<span aria-hidden="true">↗</span></Link></footer>}
      </main>
    </div>
  )
}
