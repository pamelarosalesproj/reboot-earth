import { Link } from 'react-router-dom'
import { fmtDate, t } from '../i18n/pt-BR'
import type { CnpjReport } from '../types'
import StatusBadge from './StatusBadge'

const R = t.home.report

/** Botão visual: a exportação ainda não existe (aria-disabled + aviso "Em breve"). */
function ExportButton() {
  return (
    <button type="button" className="report-export" aria-disabled="true" title={R.exportSoon} aria-describedby="report-export-soon">
      <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
        <path d="M14 3v5h5" />
        <path d="M9 15h6M12 12v6" />
      </svg>
      {R.exportPdf}
      <span id="report-export-soon" className="overview-sr-only">{R.exportSoon}</span>
    </button>
  )
}

function List({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null
  return (
    <div className="report-list">
      <h3>{title}</h3>
      <ul>
        {items.map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
    </div>
  )
}

/** "Relatório do CNPJ" (FR-505/507). O nível vem do backend (regras), nunca do texto. */
export default function CnpjReportView({ report }: { report: CnpjReport | 'loading' | 'error' }) {
  if (report === 'loading') {
    return (
      <section className="overview-report">
        <h2>{R.title}</h2>
        <p className="muted small">{R.loading}</p>
      </section>
    )
  }
  if (report === 'error' || report.status !== 'ok') {
    return (
      <section className="overview-report">
        <h2>{R.title}</h2>
        <p className="report-unavailable">{R.unavailable}</p>
      </section>
    )
  }
  return (
    <section className="overview-report" aria-labelledby="report-title">
      <div className="report-heading">
        <h2 id="report-title">{R.title}</h2>
        {report.nivel && (
          <StatusBadge status={{ level: report.nivel, reason: null, partial: false, basis: 'regras' }} compact />
        )}
        <ExportButton />
      </div>
      <p className="report-origin" role="note">
        {report.origem === 'agente' ? R.originAgent : R.originExample}
        {report.data_dos_dados && <> · {R.dataAsOf(fmtDate(report.data_dos_dados))}</>}
      </p>
      {report.titulo && <p className="report-headline">{report.titulo}</p>}
      <div className="report-columns">
        <List title={R.risks} items={report.riscos} />
        <List title={R.context} items={report.contexto} />
      </div>
      {!!report.imoveis?.length && (
        <div className="report-properties">
          <h3>{R.properties}</h3>
          <ul>
            {report.imoveis.map((p) => (
              <li key={p.car_code}>
                <span className="report-car">{p.car_code}</span>
                <span className="report-car-text">{p.resumo}</span>
                <Link to={`/painel/cars/${encodeURIComponent(p.car_code)}`}>{R.seeCar} →</Link>
              </li>
            ))}
          </ul>
        </div>
      )}
      <List title={R.caveats} items={report.ressalvas} />
    </section>
  )
}
