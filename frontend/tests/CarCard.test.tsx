import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { EmbargoesValue } from '../src/components/CarCard'
import { isValidCar, maskCnpj } from '../src/lib/car'
import type { CarSummary } from '../src/types'

const base: CarSummary = {
  car_code: 'PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0',
  state: 'PE',
  area_ha: 264.2,
  car_type: null,
  geometry: null,
  alerts_count: 3,
  embargoes_count: 0,
  embargoes_status: 'ok',
  fetched_at: '2026-11-05T12:00:00Z',
  stale: false,
}

afterEach(cleanup)

describe('EmbargoesValue (FR-011)', () => {
  it('0 confirmado', () => {
    render(<EmbargoesValue s={base} />)
    expect(screen.getByText('0 embargos')).toBeInTheDocument()
  })
  it('no determinable no se muestra como 0', () => {
    render(<EmbargoesValue s={{ ...base, embargoes_count: null, embargoes_status: 'not_determinable' }} />)
    expect(screen.getByText('Não determinável')).toBeInTheDocument()
  })
})

describe('validaciones de formulario', () => {
  it('formato CAR', () => {
    expect(isValidCar('pe-2607505-f2671ddfda3d47cc917eb3e0dfeeb8b0')).toBe(true)
    expect(isValidCar('PE-123')).toBe(false)
  })
  it('máscara CNPJ', () => {
    expect(maskCnpj('04654691000106')).toBe('04.654.691/0001-06')
  })
})
