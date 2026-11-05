import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, getDetail } from '../api/client'
import { EmbargoesValue } from '../components/CarCard'
import CarMap from '../components/CarMap'
import { fmtDate, fmtDateTime, fmtNum, t } from '../i18n/pt-BR'
import type { CarDetail } from '../types'

export default function CarDetailPage() {
  const { code = '' } = useParams()
  const [detail, setDetail] = useState<CarDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(
    (refresh = false) => {
      setLoading(true)
      setError(null)
      getDetail(code, refresh)
        .then(setDetail)
        .catch((err) => setError(err instanceof ApiError && err.status === 404 ? err.message : t.panel.unavailable))
        .finally(() => setLoading(false))
    },
    [code],
  )

  useEffect(() => load(), [load])

  const s = detail?.summary
  const D = t.detail

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
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="card">
            <h2>{D.embargoesTitle}</h2>
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
                      <th>{D.cols.process}</th>
                      <th className="num">{D.cols.area}</th>
                      <th>{D.cols.registered}</th>
                      <th>{D.cols.descriptions}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.embargoes.map((e, i) => (
                      <tr key={`${e.source}-${e.process_code}-${i}`}>
                        <td>{e.source ?? '—'}</td>
                        <td>{e.process_code ?? '—'}</td>
                        <td className="num">{fmtNum(e.area_ha)}</td>
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
