import { fmtNum, t } from '../i18n/pt-BR'
import type { Reason, Score, Status } from '../types'

/** Texto do score — só quando existe (estado `disponivel`). Enquanto o método não existir, não se mostra nada. */
export function scoreText(score: Score): string | null {
  return score.state === 'disponivel' && score.value != null ? t.status.score.disponivel(score.value) : null
}

/** Frase geral do nível (os motivos detalhados vêm em `reasonText`). */
export function explain(status: Status): string {
  return t.status.explain[status.level]
}

const ha = (v: number) => `${fmtNum(v)} ha`

/**
 * Um motivo em texto. No CAR traz os números (ex.: "Alertas em aberto após 2020 em reserva legal ou APP:
 * 3 alertas · 74,5 ha · 28,2 % do imóvel"); no CNPJ, em quantos imóveis.
 */
export function reasonText(r: Reason): string {
  const S = t.status
  const label = S.reasonLabel[r.code]
  if (r.cars != null) return `${label} — ${S.inCars(r.cars)}`
  const parts: string[] = []
  if (r.n != null) {
    if (r.code === 'EMBARGO_VIGENTE') parts.push(S.count.EMBARGO_VIGENTE(r.n))
    else if (r.code.startsWith('DETER')) parts.push(S.count.detections(r.n))
    else parts.push(S.count.alerts(r.n))
  }
  if (r.ha != null) parts.push(ha(r.ha))
  if (r.pct != null) parts.push(`${fmtNum(r.pct)} % ${S.ofCar}`)
  if (r.code === 'RL_APP_POS2020' && r.severity === 'silver') parts.push(S.belowThreshold)
  return parts.length ? `${label}: ${parts.join(' · ')}` : label
}
