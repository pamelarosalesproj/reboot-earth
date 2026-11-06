import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { scoreText } from '../lib/status'
import StatusBadge from '../components/StatusBadge'
import { fmtDateTime, t } from '../i18n/pt-BR'
import type { DashboardSummary } from '../types'
import LotOverview from '../components/LotOverview'
import type { LotOverviewData } from '../components/LotOverview'
import './HomePage.css'

function BigNumber({ label, value, hint, tone }: { label: string; value: number | null; hint?: string; tone?: string }) {
  return (
    <Link to="/painel/cars" className={`overview-environment-stat ${tone ?? ''}`}>
      <span className="big-number-label">{label}</span>
      <strong className="big-number-value">{value == null ? '—' : value.toLocaleString('pt-BR')}</strong>
      {hint && <span className="big-number-hint">{hint}</span>}
    </Link>
  )
}

export default function HomePage({ previewData, previewLots }: { previewData?: DashboardSummary; previewLots?: LotOverviewData } = {}) {
  const { producer } = useAuth()
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState(false)

  const load = useCallback(() => {
    setError(false)
    if (previewData) {
      setData(previewData)
      return
    }
    getDashboard()
      .then(setData)
      .catch(() => setError(true))
  }, [previewData])

  useEffect(load, [load])

  const H = t.home
  const name = producer?.email.split('@')[0]

  return (
    <main className="producer-overview">
      <header className="overview-header"><div><span className="overview-eyebrow">{H.eyebrow}</span><p className="overview-greeting">{H.greeting(name ?? '')}</p><h1>{H.title}</h1><p className="overview-intro">{H.intro}</p></div><Link to="/painel/cars" className="overview-primary-action">{H.manage}<span aria-hidden="true">↗</span></Link></header>

      {error && (
        <div className="card error-box">
          <p>{t.panel.unavailable}</p>
          <button className="btn btn-primary btn-sm" onClick={load}>
            {t.panel.retry}
          </button>
        </div>
      )}

      {!data && !error && <p className="muted">{t.panel.loading}</p>}

      {data && <LotOverview preview={previewLots} territorialAlerts={data.alerts_count} />}

      {data && producer && (
        <section className="overview-buyer-view">
          <div className="overview-buyer-heading">
          <h2>{H.buyerViewTitle}</h2>
          <Link to={`/consulta/${producer.cnpj}`} className="overview-public-link">{H.buyerViewLink}</Link>
          </div>
          <StatusBadge status={data.cnpj_status} />
          <p className="cnpj-report-score">{scoreText(data.cnpj_score)}</p>
        </section>
      )}

      {data && data.cars_count === 0 && (
        <section className="card empty-state">
          <h2>{t.panel.emptyTitle}</h2>
          <p className="muted">{t.panel.emptyText}</p>
          <Link to="/painel/cars" className="btn btn-primary">
            {H.addFirst}
          </Link>
        </section>
      )}

      {data && data.cars_count > 0 && (
        <>
          <section className="overview-environment" aria-label={H.environmentalTitle}>
          <div className="overview-environment-heading"><h2>{H.environmentalTitle}</h2><p>{H.environmentalSource}</p></div>
          <div className="overview-environment-numbers">
            <BigNumber label={H.cars} value={data.cars_count} />
            <BigNumber
              label={H.alerts}
              value={data.alerts_count}
              tone={data.alerts_count ? 'tone-warn' : ''}
              hint={data.cars_unavailable ? H.partial(data.cars_unavailable) : H.alertsHint}
            />
            <BigNumber
              label={H.embargoes}
              value={data.embargoes_count}
              tone={data.embargoes_count ? 'tone-danger' : ''}
              hint={data.cars_embargoes_unknown ? H.embargoesUnknown(data.cars_embargoes_unknown) : H.embargoesHint}
            />
          </div>
          </section>
          {data.stale && <p className="notice">{t.panel.stale}</p>}
          {data.oldest_fetched_at && (
            <p className="muted small">{t.panel.updatedAt(fmtDateTime(data.oldest_fetched_at))}</p>
          )}
          <Link to="/painel/cars" className="btn btn-ghost">
            {H.seeCars}
          </Link>
        </>
      )}
    </main>
  )
}
