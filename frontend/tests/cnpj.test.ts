import { describe, expect, it } from 'vitest'
import { formatCnpj, normalizeCnpj } from '../src/lib/cnpj'

describe('normalizeCnpj (réplica de validators.normalize_cnpj)', () => {
  it('acepta con y sin máscara', () => {
    expect(normalizeCnpj('04.654.691/0001-06')).toBe('04654691000106')
    expect(normalizeCnpj('04654691000106')).toBe('04654691000106')
    expect(normalizeCnpj('11.222.333/0001-81')).toBe('11222333000181')
  })
  it('rechaza dígitos verificadores incorrectos', () => {
    expect(normalizeCnpj('11.222.333/0001-00')).toBeNull()
  })
  it('rechaza todos iguales, longitud y letras', () => {
    expect(normalizeCnpj('00000000000000')).toBeNull()
    expect(normalizeCnpj('0465469100010')).toBeNull()
    expect(normalizeCnpj('04654691000106a')).toBeNull()
    expect(normalizeCnpj('')).toBeNull()
  })
  it('formatCnpj', () => {
    expect(formatCnpj('04654691000106')).toBe('04.654.691/0001-06')
  })
})
