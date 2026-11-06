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
    expect(screen.getByText('Porque há embargos registrados nos imóveis do CNPJ.')).toBeInTheDocument()
    expect(screen.getByText(/Nível provisório/)).toBeInTheDocument()
  })

  it('sin aviso provisional cuando el nivel viene del score', () => {
    render(<StatusBadge status={st('gold', { basis: 'score' })} />)
    expect(screen.queryByText(/Nível provisório/)).toBeNull()
  })

  it.each([
    [{ level: 'bronze', embargoes_count: 7 }, 'Porque há 7 embargos registrados nos imóveis do CNPJ.'],
    [{ level: 'bronze', embargoes_count: 1 }, 'Porque há 1 embargo registrado nos imóveis do CNPJ.'],
    [{ level: 'silver', alerts_count: 3 }, 'Porque há 3 alertas de desmatamento nos imóveis do CNPJ.'],
    [{ level: 'silver', alerts_count: 3, partial: true }, 'Porque há 3 alertas de desmatamento nos imóveis do CNPJ. Parte dos dados não pôde ser verificada.'],
    [{ level: 'silver', alerts_count: 0, partial: true }, 'Porque parte dos dados não pôde ser verificada.'],
  ] as const)('explica o nível com os números da regra: %o', (extra, text) => {
    render(<StatusBadge status={st(extra.level, extra)} />)
    expect(screen.getByText(text)).toBeInTheDocument()
  })
})

describe('StatusBadge do CAR', () => {
  it('explica o nível falando do imóvel, não do CNPJ', () => {
    render(
      <StatusBadge
        scope="car"
        status={{ level: 'bronze', reason: null, partial: false, basis: 'provisional', alerts_count: 2, embargoes_count: 1 }}
      />,
    )
    expect(screen.getByText('Porque há 1 embargo registrado neste imóvel.')).toBeInTheDocument()
    expect(screen.getByLabelText('Nível do imóvel: Bronze')).toBeInTheDocument()
  })
})
