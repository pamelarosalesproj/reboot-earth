import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { scoreText } from '../lib/status'
import StatusBadge from '../components/StatusBadge'
import { fmtDateTime, t } from '../i18n/pt-BR'
import type { DashboardSummary } from '../types'

function BigNumber({ label, value, hint, tone }: { label: string; value: number | null; hint?: string; tone?: string }) {
  return (
    <Link to="/painel/cars" className={`big-number ${tone ?? ''}`}>
      <span className="big-number-label">{label}</span>
      <strong className="big-number-value">{value == null ? '—' : value.toLocaleString('pt-BR')}</strong>
      {hint && <span className="big-number-hint">{hint}</span>}
    </Link>
  )
}

export default function HomePage() {
  const { producer } = useAuth()
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState(false)

  const load = useCallback(() => {
    setError(false)
    getDashboard()
      .then(setData)
      .catch(() => setError(true))
  }, [])

  useEffect(load, [load])

  const H = t.home
  const name = producer?.email.split('@')[0]

  return (
    <main className="page">
      <h1>{H.greeting(name ?? '')}</h1>
      <p className="muted home-sub">{H.subtitle}</p>

      {error && (
        <div className="card error-box">
          <p>{t.panel.unavailable}</p>
          <button className="btn btn-primary btn-sm" onClick={load}>
            {t.panel.retry}
          </button>
        </div>
      )}

      {!data && !error && <p className="muted">{t.panel.loading}</p>}

      {data && producer && (
        <section className="card buyer-view">
          <h2>{H.buyerViewTitle}</h2>
          <StatusBadge status={data.cnpj_status} />
          <p className="cnpj-report-score">{scoreText(data.cnpj_score)}</p>
          <Link to={`/consulta/${producer.cnpj}`} className="btn btn-ghost btn-sm">
            {H.buyerViewLink}
          </Link>
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
          <div className="big-numbers">
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
