import { Link } from 'react-router-dom'
import { t } from '../i18n/pt-BR'
import { explain, reasonText } from '../lib/status'
import type { Status } from '../types'
import { Help } from './CarIndicators'

const S = t.status

function EudrTag({ withHelp }: { withHelp: boolean }) {
  return (
    <span className="eudr-tag" title={S.eudrHelp}>
      {S.eudr}
      {withHelp && <Help term={S.eudr} text={S.eudrHelp} />}
    </span>
  )
}

/**
 * Nível (CAR ou CNPJ) com texto, não só cor (FR-111). Na versão completa: frase geral, motivos com
 * números (feature 006), imóveis por nível, sinal EUDR e, no painel, o link "Entenda o nível".
 */
export default function StatusBadge({
  status,
  compact = false,
  scope = 'cnpj',
  learnMore = false,
  eudrHelp = false,
}: {
  status: Status
  compact?: boolean
  scope?: 'cnpj' | 'car'
  learnMore?: boolean
  /** Na versão compacta, mostra a ajuda "?" do sinal EUDR (cabeçalho do relatório do CNPJ). */
  eudrHelp?: boolean
}) {
  const badge = (
    <span className={`status-badge ${status.level}`} aria-label={`${scope === 'car' ? S.carTitle : S.title}: ${S.level[status.level]}`}>
      <span className="status-dot" aria-hidden="true" />
      {S.level[status.level]}
    </span>
  )
  const eudr = status.eudr_attention === true
  if (compact) {
    return (
      <span className="status-compact">
        {badge}
        {eudr && <EudrTag withHelp={eudrHelp} />}
      </span>
    )
  }
  const reasons = status.reasons ?? []
  const by = status.cars_by_level
  return (
    <div className="status">
      <div className="status-line">
        {badge}
        {eudr && <EudrTag withHelp />}
      </div>
      {status.reason && <p className="status-reason">{S.reason[status.reason]}</p>}
      <p className="status-explain">{explain(status)}</p>
      {reasons.length > 0 && (
        <div className="status-reasons">
          <span className="status-reasons-title">{S.reasonsTitle}</span>
          <ul>
            {reasons.map((r) => (
              <li key={r.code} className={`reason-${r.severity}`}>
                {reasonText(r)}
              </li>
            ))}
          </ul>
        </div>
      )}
      {by && by.gold + by.silver + by.bronze + by.sem_dados > 0 && <p className="status-cars muted">{S.carsByLevel(by)}</p>}
      {status.basis === 'regras' && <p className="status-provisional muted">{S.basisNote}</p>}
      {learnMore && (
        <Link className="status-learn-more" to="/painel/nivel">
          {S.learnMore} →
        </Link>
      )}
    </div>
  )
}
