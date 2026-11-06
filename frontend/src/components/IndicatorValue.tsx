import type { ReactNode } from 'react'
import { t } from '../i18n/pt-BR'
import type { SourceState } from '../types'

const I = t.indicators

interface Props {
  status: SourceState
  /** null con status ok = la fuente respondió pero el dato no es determinable. */
  value: number | null | undefined
  format?: (v: number) => ReactNode
  notApplicableText?: string
}

/** FR-313: valor (incluido 0) / "Indisponível" / "Não se aplica" — nunca un 0 falso. */
export default function IndicatorValue({ status, value, format = (v) => v.toLocaleString('pt-BR'), notApplicableText }: Props) {
  if (status === 'nao_se_aplica') return <span className="ind-na">{notApplicableText ?? I.notApplicable}</span>
  if (status === 'indisponivel') return <span className="ind-unavailable">{I.unavailable}</span>
  if (value == null) return <span className="ind-unavailable">{I.notDeterminable}</span>
  return <span className="ind-value">{format(value)}</span>
}
