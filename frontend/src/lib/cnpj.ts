import { maskCnpj } from './car'

const W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
const W2 = [6, ...W1]

const dv = (digits: number[], weights: number[]) => {
  const rest = digits.reduce((s, d, i) => s + d * weights[i], 0) % 11
  return rest < 2 ? 0 : 11 - rest
}

/**
 * CNPJ con 14 dígitos, o null si es inválido. Réplica de `normalize_cnpj`
 * (backend/app/validators.py) solo para dar feedback inmediato: el backend siempre revalida.
 */
export function normalizeCnpj(value: string): string | null {
  const raw = (value ?? '').trim()
  if (/[^\d./\-\s]/.test(raw)) return null
  const digits = raw.replace(/\D/g, '')
  if (digits.length !== 14 || new Set(digits).size === 1) return null
  const n = [...digits].map(Number)
  if (dv(n.slice(0, 12), W1) !== n[12] || dv(n.slice(0, 13), W2) !== n[13]) return null
  return digits
}

/** 00.000.000/0000-00 */
export const formatCnpj = (digits: string) => maskCnpj(digits)
