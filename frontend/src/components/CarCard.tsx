import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSummary } from '../api/client'
import { fmtDateTime, t } from '../i18n/pt-BR'
import type { CarSummary, ProducerCar } from '../types'
import CarMap from './CarMap'
import StatusBadge from './StatusBadge'

type State = { kind: 'loading' } | { kind: 'ok'; data: CarSummary } | { kind: 'unavailable' }

interface Props {
  car: ProducerCar
  onRemove: (code: string) => Promise<void>
}

/** FR-011: "0" solo si el dato está confirmado; si no, se dice explícitamente. */
export function EmbargoesValue({ s }: { s: CarSummary }) {
  if (s.embargoes_status === 'ok' && s.embargoes_count != null) return <>{t.panel.embargoes(s.embargoes_count)}</>
  if (s.embargoes_status === 'unavailable') return <>{t.panel.embargoesUnavailable}</>
  return <>{t.panel.embargoesNotDeterminable}</>
}

export default function CarCard({ car, onRemove }: Props) {
  const [state, setState] = useState<State>({ kind: 'loading' })
  const [confirming, setConfirming] = useState(false)
  const [removing, setRemoving] = useState(false)

  // Cada tarjeta carga sus datos por separado: un fallo no afecta a las demás (FR-012).
  const load = useCallback(
    (refresh = false) => {
      setState({ kind: 'loading' })
      getSummary(car.car_code, refresh)
        .then((data) => setState({ kind: 'ok', data }))
        .catch(() => setState({ kind: 'unavailable' }))
    },
    [car.car_code],
  )

  useEffect(() => load(), [load])

  const s = state.kind === 'ok' ? state.data : null

  return (
    <article className="card car-card">
      <header className="car-card-head">
        <h3 className="car-code" title={car.car_code}>
          {car.car_code}
        </h3>
        {s?.status && <StatusBadge status={s.status} compact scope="car" />}
        {s && (
          <span className="muted small">
            {[s.state, s.area_ha != null ? t.panel.area(s.area_ha) : null].filter(Boolean).join(' · ')}
          </span>
        )}
      </header>

      {state.kind === 'loading' && <div className="map-empty">{t.panel.loading}</div>}

      {state.kind === 'unavailable' && (
        <div className="map-empty error-box">
          <p>{t.panel.unavailable}</p>
          <button className="btn btn-primary btn-sm" onClick={() => load(true)}>
            {t.panel.retry}
          </button>
        </div>
      )}

      {s && (
        <>
          {s.stale && <p className="notice">{t.panel.stale}</p>}
          {car.mapbiomas_status === 'not_in_mapbiomas' && !s.geometry && (
            <p className="notice">{t.panel.notInMapBiomas}</p>
          )}
          <CarMap geometry={s.geometry} />
          <div className="stats">
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
          <p className="muted small">{t.panel.updatedAt(fmtDateTime(s.fetched_at))}</p>
        </>
      )}


      <footer className="car-card-actions">
        <Link className="btn btn-primary btn-sm" to={`/painel/cars/${encodeURIComponent(car.car_code)}`}>
          {t.panel.details}
        </Link>
        <button className="btn btn-ghost btn-sm" onClick={() => load(true)} disabled={state.kind === 'loading'}>
          {t.panel.refresh}
        </button>
        {!confirming ? (
          <button className="btn btn-ghost btn-sm" onClick={() => setConfirming(true)}>
            {t.panel.remove}
          </button>
        ) : (
          <span className="confirm">
            {t.panel.confirmRemove}{' '}
            <button
              className="btn btn-danger btn-sm"
              disabled={removing}
              onClick={async () => {
                setRemoving(true)
                try {
                  await onRemove(car.car_code)
                } finally {
                  setRemoving(false)
                  setConfirming(false)
                }
              }}
            >
              {t.panel.yes}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setConfirming(false)}>
              {t.panel.no}
            </button>
          </span>
        )}
      </footer>
    </article>
  )
}
