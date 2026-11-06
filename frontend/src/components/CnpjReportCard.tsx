import { fmtDateTime, t } from '../i18n/pt-BR'
import { scoreText } from '../lib/status'
import type { PublicCnpjReport } from '../types'
import StatusBadge from './StatusBadge'

const P = t.publicSearch

/** Ficha agregada de un CNPJ. Sin mapa, códigos de CAR ni datos de la cuenta (FR-105). */
export default function CnpjReportCard({ report }: { report: PublicCnpjReport }) {
  const { status } = report
  return (
    <article className={`card cnpj-report cnpj-report-${status.level}`} aria-label={P.resultLabel}>
      <header className="cnpj-report-head">
        <span className="cnpj-result-eyebrow">{P.resultLabel}</span>
        <h2>{report.cnpj_formatted}</h2>
      </header>

      <StatusBadge status={status} />

      {scoreText(report.score) && <p className="cnpj-report-score">{scoreText(report.score)}</p>}

      {status.reason === 'not_registered' ? (
        <p className="muted">{P.notRegisteredNote}</p>
      ) : (
        <ul className="cnpj-report-facts">
          <li>{P.properties(report.cars_count)}</li>
          {status.partial && <li>{P.partial(report.cars_with_data, report.cars_count)}</li>}
          {report.data_as_of ? (
            <li>
              {P.dataAsOf(fmtDateTime(report.data_as_of))}
              {report.stale && <strong className="stale-tag"> · {P.stale}</strong>}
            </li>
          ) : <li>{P.noDate}</li>}
        </ul>
      )}
      <p className="cnpj-result-source">{P.resultSource}</p>
    </article>
  )
}
