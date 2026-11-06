import { t } from '../i18n/pt-BR'
import { explain } from '../lib/status'
import type { Status } from '../types'

const S = t.status

/** Nivel del CNPJ con texto (no solo color), explicación y aviso provisional (FR-111/112). */
export default function StatusBadge({
  status,
  compact = false,
  scope = 'cnpj',
}: {
  status: Status
  compact?: boolean
  scope?: 'cnpj' | 'car'
}) {
  const badge = (
    <span className={`status-badge ${status.level}`} aria-label={`${scope === 'car' ? S.carTitle : S.title}: ${S.level[status.level]}`}>
      <span className="status-dot" aria-hidden="true" />
      {S.level[status.level]}
    </span>
  )
  if (compact) return badge
  return (
    <div className="status">
      {badge}
      {status.reason && <p className="status-reason">{S.reason[status.reason]}</p>}
      <p className="status-explain">{explain(status, scope)}</p>
      {status.basis === 'provisional' && <p className="status-provisional muted">{S.provisional}</p>}
    </div>
  )
}
