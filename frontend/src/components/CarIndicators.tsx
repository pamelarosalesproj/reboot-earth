import { useId, useState } from 'react'
import type { ReactNode } from 'react'
import { fmtDateTime, t } from '../i18n/pt-BR'
import type { CarIndicators as Data, Count, Situacao, SourceState } from '../types'
import IndicatorValue from './IndicatorValue'

const I = t.indicators
const OPEN: Situacao[] = ['embargo_vigente', 'com_fiscalizacao', 'pendente']
const SUPERSEDED: Situacao[] = ['autorizada', 'embargo_levantado', 'suspensa_judicial']

/** Explicación de un término: se abre al pasar el ratón, con el teclado (foco) o tocando (móvil). */
function Help({ term, text }: { term: string; text: string }) {
  const id = useId()
  const [open, setOpen] = useState(false)
  return (
    <span className={`ind-help${open ? ' open' : ''}`}>
      <button
        type="button"
        className="ind-help-btn"
        aria-label={I.helpLabel(term)}
        aria-describedby={id}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        onBlur={() => setOpen(false)}
      >
        ?
      </button>
      <span role="tooltip" id={id} className="ind-help-text">
        {text}
      </span>
    </span>
  )
}

function Row({
  label,
  hint,
  risk,
  help,
  children,
}: {
  label: string
  hint?: string
  risk?: boolean
  help?: { term: string; text: string }
  children: ReactNode
}) {
  return (
    <div className={`ind-row${risk ? ' ind-risk' : ''}`}>
      <span className="ind-label">
        {label}
        {help && <Help term={help.term} text={help.text} />}
        {hint && <span className="ind-hint"> · {hint}</span>}
      </span>
      <span className="ind-val">{children}</span>
    </div>
  )
}

const sumCounts = (d: Data, keys: Situacao[]): Count =>
  keys.reduce((acc, k) => ({ n: acc.n + (d.alerts_by_status[k]?.n ?? 0), ha: acc.ha + (d.alerts_by_status[k]?.ha ?? 0) }), {
    n: 0,
    ha: 0,
  })

export function IndicatorsView({ d }: { d: Data }) {
  const mb: SourceState = d.sources.mapbiomas.status
  const o = d.open
  const c = d.context
  const countFmt = (key: Situacao) => (
    <IndicatorValue status={mb} value={d.alerts_by_status[key]?.n ?? null} format={() => I.count(d.alerts_by_status[key]!)} />
  )
  const superseded = sumCounts(d, SUPERSEDED)
  const deterClasses = Object.entries(c.deter?.by_class ?? {})

  return (
    <div className="indicators">
      {d.stale && <p className="notice">{I.stale}</p>}

      <section className="ind-block">
        <h4>{I.open}</h4>
        {OPEN.map((k) => (
          <Row key={k} label={I.situacao[k]} risk={(d.alerts_by_status[k]?.n ?? 0) > 0}>
            {countFmt(k)}
          </Row>
        ))}
        <Row label={I.post2020} hint={I.post2020Hint} risk={(o.post_2020?.ha ?? 0) > 0}>
          <IndicatorValue status={mb} value={o.post_2020?.n ?? null} format={() => I.count(o.post_2020!)} />
        </Row>
        <Row label={I.legalReserve} risk={(o.legal_reserve_ha ?? 0) > 0}>
          <IndicatorValue status={mb} value={o.legal_reserve_ha} format={I.ha} />
        </Row>
        <Row label={I.app} risk={(o.app_alerts ?? 0) > 0} help={{ term: 'APP', text: I.appHelp }}>
          <IndicatorValue status={mb} value={o.app_alerts} />
        </Row>
        <Row label={I.embargoesActive} risk={(o.embargoes_active ?? 0) > 0}>
          <IndicatorValue status={mb} value={o.embargoes_active} />
        </Row>
        <Row label={I.indigenous} risk={(o.indigenous_land_ha ?? 0) > 0}>
          <IndicatorValue status={mb} value={o.indigenous_land_ha} format={I.ha} />
        </Row>
        <Row label={I.integral} risk={(o.integral_protection_ha ?? 0) > 0}>
          <IndicatorValue status={mb} value={o.integral_protection_ha} format={I.ha} />
        </Row>
      </section>

      <section className="ind-block ind-context">
        <h4>{I.context}</h4>
        <Row label={I.superseded}>
          <IndicatorValue status={mb} value={superseded.n} format={() => I.count(superseded)} />
        </Row>
        <Row label={I.embargoesLifted}>
          <IndicatorValue status={mb} value={c.embargoes_lifted} />
        </Row>
        <Row label={I.sustainable} hint={c.sustainable_use_names.join(', ') || undefined}>
          <IndicatorValue status={mb} value={c.sustainable_use_ha} format={I.ha} />
        </Row>
        <Row label={I.nativeVegetation}>
          <IndicatorValue
            status={d.sources.prodes.status}
            value={c.native_vegetation?.remaining_pct ?? null}
            format={I.pct}
          />
        </Row>
        {d.sources.prodes.status === 'ok' && <p className="ind-note">{I.nativeVegetationNote}</p>}
        <Row label={I.deter}>
          {d.sources.deter.status === 'ok' && deterClasses.length > 0 ? (
            <ul className="ind-list">
              {deterClasses.map(([k, v]) => (
                <li key={k}>
                  {I.deterClass[k] ?? k}: {I.count(v)}
                </li>
              ))}
            </ul>
          ) : (
            <IndicatorValue
              status={d.sources.deter.status}
              value={c.deter ? 0 : null}
              format={() => I.deterNone}
              notApplicableText={I.notApplicableBiome}
            />
          )}
        </Row>
        <Row label={I.hotspots}>
          <IndicatorValue status={d.sources.focos.status} value={c.hotspots_12m?.count ?? null} />
        </Row>
        <Row label={I.forestManagement}>
          <IndicatorValue
            status={d.sources.sinaflor.status}
            value={c.forest_management?.authorizations ?? null}
            format={() => {
              const f = c.forest_management!
              return I.forestManagementValue(f.authorizations, f.active, f.volume_m3)
            }}
          />
        </Row>
        {d.sources.sinaflor.status === 'ok' && (c.forest_management?.authorizations ?? 0) > 0 && (
          <p className="ind-note">{I.forestManagementNote}</p>
        )}
      </section>

      <p className="ind-note">{I.areaNote}</p>
      <p className="muted small">{I.sources(fmtDateTime(d.fetched_at))}</p>
    </div>
  )
}
