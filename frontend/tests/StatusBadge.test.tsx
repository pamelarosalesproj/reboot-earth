import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import StatusBadge from '../src/components/StatusBadge'
import type { Status, StatusLevel } from '../src/types'

const st = (level: StatusLevel, extra: Partial<Status> = {}): Status => ({
  level,
  reason: null,
  partial: false,
  basis: 'provisional',
  ...extra,
})

afterEach(cleanup)

describe('StatusBadge (FR-111/112)', () => {
  it.each([
    ['gold', 'Gold'],
    ['silver', 'Silver'],
    ['bronze', 'Bronze'],
    ['sem_dados', 'Sem dados'],
  ] as const)('%s muestra su etiqueta en texto', (level, label) => {
    render(<StatusBadge status={st(level)} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('sem_dados muestra el motivo', () => {
    render(<StatusBadge status={st('sem_dados', { reason: 'data_unavailable' })} />)
    expect(screen.getByText('Dados indisponíveis')).toBeInTheDocument()
  })

  it('explica el nivel y avisa que es provisional', () => {
    render(<StatusBadge status={st('bronze')} />)
    expect(screen.getByText('Há embargos registrados.')).toBeInTheDocument()
    expect(screen.getByText(/Indicador preliminar/)).toBeInTheDocument()
  })

  it('sin aviso provisional cuando el nivel viene del score', () => {
    render(<StatusBadge status={st('gold', { basis: 'score' })} />)
    expect(screen.queryByText(/Indicador preliminar/)).toBeNull()
  })
})
