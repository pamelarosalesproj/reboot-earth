import { t } from '../i18n/pt-BR'
import type { Score } from '../types'

/** Texto del estado del score (FR-108/109). */
export function scoreText(score: Score) {
  if (score.state === 'disponivel' && score.value != null) return t.status.score.disponivel(score.value)
  return score.state === 'nao_calculavel' ? t.status.score.nao_calculavel : t.status.score.em_calculo
}
