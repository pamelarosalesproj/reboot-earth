import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, getOverview, getReport } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import CnpjReportView from '../components/CnpjReportView'
import StatusBadge from '../components/StatusBadge'
import { fmtDateTime, t } from '../i18n/pt-BR'
import { maskCnpj } from '../lib/car'
import { scoreText } from '../lib/status'
import type { CnpjOverview, CnpjReport, DashboardSummary } from '../types'
import './HomePage.css'

const H = t.home

function BigNumber({ label, value, hint, tone }: { label: string; value: string | null; hint?: string; tone?: string }) {
  return (
    <Link to="/painel/cars" className={`overview-environment-stat ${tone ?? ''}`}>
      <span className="big-number-label">{label}</span>
      <strong className={`big-number-value${value == null ? ' big-number-unavailable' : ''}`}>{value ?? H.unavailable}</strong>
      {hint && <span className="big-number-hint">{hint}</span>}
    </Link>
  )
}

function Numbers({ o }: { o: CnpjOverview | 'loading' | 'error' }) {
  if (o === 'loading') return <p className="muted small">{t.panel.loading}</p>
  if (o === 'error') return <p className="muted small">{H.numbersError}</p>
  const open = o.open_alerts
  const missingAlerts = o.cars_without_alert_data ? H.partial(o.cars_without_alert_data) : undefined
  return (
    <>
      <div className="overview-environment-numbers">
        <BigNumber label={H.cars} value={o.cars_count.toLocaleString('pt-BR')} hint={H.carsHint} />
        <BigNumber
          label={H.openAlerts}
          value={open ? H.openAlertsValue(open.n, open.ha) : null}
          tone={open?.n ? 'tone-warn' : ''}
          hint={missingAlerts ?? (o.alerts_total != null ? H.openAlertsHint(o.alerts_total, o.superseded_alerts?.n ?? 0) : undefined)}
        />
        <BigNumber
          label={H.activeEmbargoes}
          value={o.embargoes_active != null ? o.embargoes_active.toLocaleString('pt-BR') : null}
          tone={o.embargoes_active ? 'tone-danger' : ''}
          hint={o.cars_embargoes_unknown ? H.embargoesUnknown(o.cars_embargoes_unknown) : H.activeEmbargoesHint}
        />
      </div>
      {o.data_as_of && <p className="muted small overview-data-date">{H.dataAsOf(fmtDateTime(o.data_as_of))}</p>}
    </>
  )
}

interface Preview {
  previewData?: DashboardSummary
  previewOverview?: CnpjOverview
  previewReport?: CnpjReport
}

/** Início = resumo do CNPJ (feature 005): status, 3 números e relatório. Sem módulos sem fonte de dados. */
export default function HomePage({ previewData, previewOverview, previewReport }: Preview = {}) {
  const { producer } = useAuth()
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState(false)
  const [overview, setOverview] = useState<CnpjOverview | 'loading' | 'error'>('loading')
  const [report, setReport] = useState<CnpjReport | 'loading' | 'error'>('loading')

  const load = useCallback(() => {
    if (previewData) {
      setData(previewData)
      setOverview(previewOverview ?? 'error')
      setReport(previewReport ?? 'error')
      return
    }
    setError(false)
    getDashboard()
      .then(setData)
      .catch(() => setError(true))
    // Números e relatório carregam à parte: se falharem, o status continua visível (SC-504).
    getOverview()
      .then(setOverview)
      .catch(() => setOverview('error'))
    getReport()
      .then(setReport)
      .catch(() => setReport('error'))
  }, [previewData, previewOverview, previewReport])

  useEffect(load, [load])

  const name = producer?.email.split('@')[0]

  return (
    <main className="producer-overview">
      <header className="overview-header">
        <div>
          <span className="overview-eyebrow">{H.eyebrow}</span>
          <p className="overview-greeting">
            {H.greeting(name ?? '')}
            {producer && <> · CNPJ {maskCnpj(producer.cnpj)}</>}
          </p>
          <h1>{H.summaryTitle}</h1>
          <p className="overview-intro">{H.summaryIntro}</p>
        </div>
        <Link to="/painel/cars" className="overview-primary-action">
          {H.manage}
          <span aria-hidden="true">↗</span>
        </Link>
      </header>

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
        <section className="overview-buyer-view overview-status" aria-labelledby="status-title">
          <div className="overview-buyer-heading">
            <h2 id="status-title">{H.statusTitle}</h2>
          </div>
          <StatusBadge status={data.cnpj_status} learnMore />
          {scoreText(data.cnpj_score) && <p className="cnpj-report-score">{scoreText(data.cnpj_score)}</p>}
          {data.stale && <p className="notice">{t.panel.stale}</p>}
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
          <section className="overview-environment" aria-labelledby="numbers-title">
            <div className="overview-environment-heading">
              <h2 id="numbers-title">{H.numbersTitle}</h2>
              <p>{H.numbersSource}</p>
            </div>
            <Numbers o={overview} />
          </section>
          <CnpjReportView report={report} />
        </>
      )}
    </main>
  )
}
