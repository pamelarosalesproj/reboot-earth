import { useId, useState } from 'react'
import { t } from '../i18n/pt-BR'

export interface LotPreview {
  code: string
  species: string
  scientificName: string
  origin: string
  car: string
  location: string
  volume: number
  authorizedVolume: number
  status: 'compliant' | 'blocked'
  risk: number
  riskBand: 'low' | 'moderate' | 'high'
  reason: string
}

// Modelo de presentación; la clasificación y los indicadores no se calculan aquí.
export interface LotOverviewData {
  trackedLots: number
  approvedVolume: number
  eudrPercent: number
  territorialAlerts: number
  riskCounts: { low: number; moderate: number; high: number }
  lots: LotPreview[]
}

type IconName = 'lots' | 'volume' | 'shield' | 'alert' | 'search'
export function DashboardIcon({ name }: { name: IconName }) {
  const paths = {
    lots: <><path d="m12 3 8 4-8 4-8-4 8-4Zm-8 9 8 4 8-4M4 17l8 4 8-4" /></>,
    volume: <><path d="M12 3v17M6 21h12M4 7h16M6 7l-4 8h8L6 7Zm12 0-4 8h8l-4-8Z" /></>,
    shield: <><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z" /><path d="m8 12 3 3 5-6" /></>,
    alert: <><path d="m9 3-7 7v4l7 7h6l7-7v-4l-7-7H9Z" /><path d="M12 8v5m0 3h.01" /></>,
    search: <><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></>,
  }
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

const H = t.home
const number = (value: number) => value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const normalize = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()

export default function LotOverview({ preview, territorialAlerts }: { preview?: LotOverviewData; territorialAlerts: number | null }) {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<keyof typeof H.filters>('all')
  const searchId = useId()
  const rows = preview?.lots.filter(lot => {
    const matches = normalize([lot.code, lot.species, lot.scientificName, lot.origin, lot.car, lot.location].join(' ')).includes(normalize(query.trim()))
    return matches && (filter === 'all' || (filter === 'high' ? lot.riskBand === 'high' : lot.status === filter))
  }) ?? []
  const metrics: { label: string; value: string; unit?: string; hint: string; icon: IconName; tone?: string }[] = [
    { label: H.lots, value: preview ? String(preview.trackedLots) : '—', hint: preview ? H.lotsHint : H.integrationPending, icon: 'lots' },
    { label: H.volume, value: preview ? number(preview.approvedVolume) : '—', unit: preview ? 'm³' : undefined, hint: preview ? H.volumeHint : H.unavailable, icon: 'volume' },
    { label: H.eudr, value: preview ? number(preview.eudrPercent) : '—', unit: preview ? '%' : undefined, hint: preview ? H.eudrHint : H.unavailable, icon: 'shield', tone: 'positive' },
    { label: H.territorial, value: (preview?.territorialAlerts ?? territorialAlerts)?.toLocaleString('pt-BR') ?? '—', hint: H.territorialHint, icon: 'alert', tone: 'warning' },
  ]
  const bands = ['low', 'moderate', 'high'] as const
  const total = preview ? bands.reduce((sum, band) => sum + preview.riskCounts[band], 0) : 0

  return <>
    {preview && <p className="overview-demo"><span />{H.designData}</p>}
    <section className="overview-metrics" aria-label={H.environmentalTitle}>
      {metrics.map(metric => <article className={`overview-metric ${metric.tone ?? ''}`} key={metric.label}>
        <div className="overview-metric-heading"><h2>{metric.label}</h2><span><DashboardIcon name={metric.icon} /></span></div>
        <div className="overview-metric-value"><strong>{metric.value}</strong>{metric.unit && <span>{metric.unit}</span>}</div>
        <p>{metric.hint}</p>
      </article>)}
    </section>

    <section className="overview-matrix" aria-labelledby="risk-matrix-title">
      <div className="overview-matrix-top"><div><span className="overview-eyebrow">{H.lotsTitle}</span><h2 id="risk-matrix-title">{H.matrixTitle}</h2><p>{H.matrixIntro}</p></div>
        {preview && <ul className="overview-legend">{bands.map(band => <li key={band}><span className={`risk-dot risk-${band}`} />{H[band]}<strong>{preview.riskCounts[band]}</strong></li>)}</ul>}
      </div>
      {preview && total > 0 ? <div className="overview-risk-bar" role="img" aria-label={bands.map(band => `${H[band]}: ${preview.riskCounts[band]}`).join(', ')}>{bands.map(band => preview.riskCounts[band] > 0 && <span key={band} className={`risk-${band}`} style={{ width: `${preview.riskCounts[band] / total * 100}%` }} />)}</div> : <p className="overview-pending">{H.matrixPending}</p>}
      {preview && <p className="overview-matrix-note">{H.matrixDemo}</p>}
    </section>

    <section className="overview-lots" aria-labelledby="overview-lots-title">
      <div className="overview-table-heading"><div><h2 id="overview-lots-title">{H.lotsTitle}</h2><p>{H.lotsSubtitle}</p></div><span className="overview-count">{preview ? preview.trackedLots : '—'}</span></div>
      <div className="overview-toolbar">
        <div className="overview-search"><DashboardIcon name="search" /><label className="overview-sr-only" htmlFor={searchId}>{H.searchLabel}</label><input id={searchId} value={query} onChange={e => setQuery(e.target.value)} placeholder={H.searchPlaceholder} disabled={!preview} /></div>
        <div className="overview-filters" role="group" aria-label={H.filtersLabel}>{(Object.keys(H.filters) as (keyof typeof H.filters)[]).map(key => <button key={key} type="button" aria-pressed={filter === key} onClick={() => setFilter(key)} disabled={!preview}>{H.filters[key]}</button>)}</div>
      </div>
      <div className="overview-table-scroll" role="region" aria-label={H.lotsTitle} tabIndex={0}><table className="overview-table"><thead><tr>{Object.values(H.columns).map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>
        {rows.map(lot => <tr key={lot.code}>
          <td><strong className="overview-lot-code">{lot.code}</strong><span>{lot.species}</span><i>{lot.scientificName}</i></td>
          <td><strong>{lot.origin}</strong><span className="overview-car-code">{lot.car}</span><small>{lot.location}</small></td>
          <td className="overview-volume"><strong>{number(lot.volume)} <small>m³</small></strong><span>{H.authorized(number(lot.authorizedVolume))}</span></td>
          <td><span className={`overview-lot-status lot-${lot.status}`}><DashboardIcon name={lot.status === 'compliant' ? 'shield' : 'alert'} />{H[lot.status]}</span><small className={`overview-risk-value risk-text-${lot.riskBand}`}>{H.risk(lot.risk)}</small></td>
          <td><p className={lot.status === 'blocked' ? 'overview-reason-alert' : ''}>{lot.reason}</p></td>
        </tr>)}
        {rows.length === 0 && <tr><td colSpan={5} className="overview-table-empty"><DashboardIcon name="lots" /><h3>{preview ? H.noMatches : H.emptyLots}</h3>{preview ? <button onClick={() => { setQuery(''); setFilter('all') }} type="button">{H.resetFilters}</button> : <p>{H.emptyLotsHint}</p>}</td></tr>}
      </tbody></table></div>
    </section>
  </>
}
