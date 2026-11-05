import { t } from '../i18n/pt-BR'
import type { Status } from '../types'

const S = t.status

/** Nivel del CNPJ con texto (no solo color), explicación y aviso provisional (FR-111/112). */
export default function StatusBadge({ status }: { status: Status }) {
  return (
    <div className="status">
      <span className={`status-badge ${status.level}`} aria-label={`${S.title}: ${S.level[status.level]}`}>
        <span className="status-dot" aria-hidden="true" />
        {S.level[status.level]}
      </span>
      {status.reason && <p className="status-reason">{S.reason[status.reason]}</p>}
      <p className="status-explain">{S.explain[status.level]}</p>
      {status.basis === 'provisional' && <p className="status-provisional muted">{S.provisional}</p>}
    </div>
  )
}
