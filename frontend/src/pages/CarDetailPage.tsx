import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, getDetail, getIndicators } from '../api/client'
import { EmbargoesValue } from '../components/CarCard'
import { Help, IndicatorsView } from '../components/CarIndicators'
import CarMap from '../components/CarMap'
import StatusBadge from '../components/StatusBadge'
import { fmtDate, fmtDateTime, fmtNum, t } from '../i18n/pt-BR'
import type { AlertIndicator, CarDetail, CarIndicators } from '../types'

const OPEN = new Set(['embargo_vigente', 'com_fiscalizacao', 'pendente'])

export default function CarDetailPage() {
  const { code = '' } = useParams()
  const [detail, setDetail] = useState<CarDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  // Indicadores por alerta (feature 003): si fallan, la tabla se muestra igual.
  const [indicators, setIndicators] = useState<CarIndicators | null>(null)
  const [indicatorsError, setIndicatorsError] = useState(false)
  const byAlert: Map<number, AlertIndicator> | null = indicators
    ? new Map(indicators.alerts.map((a) => [a.alert_code, a]))
    : null

  const load = useCallback(
    (refresh = false) => {
      setLoading(true)
      setError(null)
      getDetail(code, refresh)
        .then(setDetail)
        .catch((err) => setError(err instanceof ApiError && err.status === 404 ? err.message : t.panel.unavailable))
        .finally(() => setLoading(false))
      getIndicators(code, refresh)
        .then((d) => {
          setIndicators(d)
          setIndicatorsError(false)
        })
        .catch(() => {
          setIndicators(null)
          setIndicatorsError(true)
        })
    },
    [code],
  )

  useEffect(() => load(), [load])

  const s = detail?.summary
  const D = t.detail
  const I = t.indicators
  // Colunas do IBAMA (feature 007) só quando algum embargo as tem.
  const hasTerm = !!detail?.embargoes.some((e) => e.term)
  const hasOverlap = !!detail?.embargoes.some((e) => e.overlap_ha != null)

  return (
    <main className="page">
      <Link to="/painel/cars" className="btn btn-ghost btn-sm">
        {D.back}
      </Link>
      <h1 className="car-code">{code}</h1>

      {loading && !detail && <p className="muted">{t.panel.loading}</p>}
      {error && (
        <div className="error-box card">
          <p>{error}</p>
          <button className="btn btn-primary btn-sm" onClick={() => load(true)}>
            {t.panel.retry}
          </button>
        </div>
      )}

      {detail && s && (
        <>
          {s.stale && <p className="notice">{t.panel.stale}</p>}
          {s.status && (
            <section className="card car-status" aria-labelledby="car-status-title">
              <h2 id="car-status-title">{t.status.carTitle}</h2>
              <StatusBadge status={s.status} scope="car" learnMore />
            </section>
          )}
          <div className="detail-head card">
            <CarMap geometry={s.geometry} height={340} />
            <div className="stats">
              <div className="stat">
                <span className="stat-label">UF · Área</span>
                <strong>
                  {s.state ?? '—'} · {s.area_ha != null ? t.panel.area(s.area_ha) : '—'}
                </strong>
              </div>
              <div className={`stat ${s.alerts_count ? 'stat-warn' : ''}`}>
                <span className="stat-label">{t.panel.alertsLabel}</span>
                <strong>{s.alerts_count != null ? t.panel.alerts(s.alerts_count) : '—'}</strong>
              </div>
              <div className={`stat ${s.embargoes_count ? 'stat-danger' : ''}`}>
                <span className="stat-label">{t.panel.embargoesLabel}</span>
                <strong>
                  <EmbargoesValue s={s} />
                </strong>
              </div>
            </div>
            <p className="muted small">
              {t.panel.updatedAt(fmtDateTime(s.fetched_at))}{' '}
              <button className="btn btn-link btn-sm" onClick={() => load(true)} disabled={loading}>
                {t.panel.refresh}
              </button>
            </p>
          </div>

          <section className="card detail-indicators">
            <h2>{I.title}</h2>
            {indicators ? (
              <IndicatorsView d={indicators} />
            ) : (
              <p className="muted small">{indicatorsError ? I.error : I.loading}</p>
            )}
          </section>

          <section className="card">
            <h2>{D.alertsTitle}</h2>
            {detail.alerts.length === 0 ? (
              <p className="muted">{D.noAlerts}</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>{D.cols.code}</th>
                      <th>{D.cols.detected}</th>
                      <th className="num">{D.cols.area}</th>
                      <th className="num">{D.cols.areaInCar}</th>
                      <th className="num">{D.cols.embargoes}</th>
                      {byAlert && (
                        <>
                          <th>{I.cols.status}</th>
                          <th>{I.cols.post2020}</th>
                          <th className="num">{I.cols.legalReserve}</th>
                          <th>{I.cols.app}</th>
                          <th>{I.cols.uc}</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {detail.alerts.map((a) => (
                      <tr key={a.alert_code}>
                        <td>{a.alert_code}</td>
                        <td>{fmtDate(a.detected_at)}</td>
                        <td className="num">{fmtNum(a.area_ha)}</td>
                        <td className="num">{fmtNum(a.area_in_car_ha)}</td>
                        <td className="num">{a.embargoes_count ?? '—'}</td>
                        {byAlert &&
                          (() => {
                            const x = byAlert.get(a.alert_code)
                            if (!x) return <td colSpan={5}>—</td>
                            return (
                              <>
                                <td className={OPEN.has(x.status) ? 'ind-status-open' : ''}>
                                  {I.situacaoShort[x.status]}
                                </td>
                                <td>{x.post_2020 ? I.yes : I.no}</td>
                                <td className="num">{fmtNum(x.legal_reserve_ha)}</td>
                                <td>{x.touches_app ? I.yes : I.no}</td>
                                <td>{x.conservation_units.join(', ') || '—'}</td>
                              </>
                            )
                          })()}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="card">
            <h2>{D.embargoesTitle}</h2>
            {s.embargoes_status === 'ok' && s.embargoes_source && (
              <p className="muted">
                {D.embargoesSource(
                  D.embargoesSourceNames[s.embargoes_source],
                  fmtDateTime(s.embargoes_checked_at ?? s.fetched_at),
                )}
                {s.embargoes_source === 'ibama' && <Help term={D.ibamaHelpTerm} text={D.ibamaHelp} />}
                {s.embargoes_stale && <> · {D.embargoesStale}</>}
              </p>
            )}
            {s.embargoes_status !== 'ok' ? (
              <p className="muted">
                <EmbargoesValue s={s} />
              </p>
            ) : detail.embargoes.length === 0 ? (
              <p className="muted">{D.noEmbargoes}</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>{D.cols.source}</th>
                      {hasTerm && <th>{D.cols.term}</th>}
                      <th>{D.cols.process}</th>
                      <th className="num">{D.cols.area}</th>
                      {hasOverlap && <th className="num">{D.cols.overlap}</th>}
                      <th>{D.cols.registered}</th>
                      <th>{D.cols.descriptions}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.embargoes.map((e, i) => (
                      <tr key={`${e.source}-${e.process_code}-${i}`}>
                        <td>{e.source ?? '—'}</td>
                        {hasTerm && <td>{e.term ?? '—'}</td>}
                        <td>{e.process_code ?? '—'}</td>
                        <td className="num">{fmtNum(e.area_ha)}</td>
                        {hasOverlap && <td className="num">{fmtNum(e.overlap_ha ?? null)}</td>}
                        <td>{fmtDate(e.registered_at)}</td>
                        <td>{e.descriptions.join(' · ') || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )
}
