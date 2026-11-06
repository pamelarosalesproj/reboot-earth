import { t } from '../i18n/pt-BR'
import type { Score, Status } from '../types'

/** Texto do score — só quando existe (estado `disponivel`). Enquanto o método não existir, não se mostra nada. */
export function scoreText(score: Score): string | null {
  return score.state === 'disponivel' && score.value != null ? t.status.score.disponivel(score.value) : null
}

/** Motivo do nível com os números que a regra usou (ex.: "Porque há 7 embargos registrados…"). */
export function explain(status: Status): string {
  const S = t.status
  const B = S.because
  if (status.level === 'bronze') {
    return status.embargoes_count ? B.embargoes(status.embargoes_count) : B.embargoesGeneric
  }
  if (status.level === 'silver') {
    if (status.alerts_count) return B.alerts(status.alerts_count) + (status.partial ? ` ${B.partialToo}` : '')
    return status.partial ? B.partial : S.explain.silver
  }
  return S.explain[status.level]
}
