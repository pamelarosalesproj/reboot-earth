import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import StatusBadge from '../src/components/StatusBadge'
import type { Status, StatusLevel } from '../src/types'

const st = (level: StatusLevel, extra: Partial<Status> = {}): Status => ({
  level,
  reason: null,
  partial: false,
  basis: 'regras',
  ...extra,
})

afterEach(cleanup)

describe('StatusBadge (FR-111 / feature 006)', () => {
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

  it('motivos del CAR con números y umbral', () => {
    render(
      <StatusBadge
        scope="car"
        status={st('bronze', {
          reasons: [
            { code: 'EMBARGO_VIGENTE', severity: 'bronze', n: 1 },
            { code: 'RL_APP_POS2020', severity: 'silver', n: 2, ha: 3.5, pct: 0.4 },
          ],
        })}
      />,
    )
    expect(screen.getByText('Embargo vigente: 1 embargo')).toBeInTheDocument()
    expect(
      screen.getByText('Alertas em aberto após 2020 em reserva legal ou APP: 2 alertas · 3,5 ha · 0,4 % do imóvel · abaixo de 1 % do imóvel'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Nível do imóvel: Bronze')).toBeInTheDocument()
    expect(screen.getByText(/regras fixas/)).toBeInTheDocument()
  })

  it('CNPJ: motivos por imóveis, distribución y EUDR', () => {
    render(
      <StatusBadge
        status={st('bronze', {
          reasons: [{ code: 'EMBARGO_VIGENTE', severity: 'bronze', cars: 2 }],
          cars_by_level: { gold: 1, silver: 0, bronze: 2, sem_dados: 0 },
          eudr_attention: true,
        })}
      />,
    )
    expect(screen.getByText('Embargo vigente — em 2 imóveis')).toBeInTheDocument()
    expect(screen.getByText('Imóveis: 2 Bronze · 1 Gold')).toBeInTheDocument()
    expect(screen.getByText('Atenção EUDR')).toBeInTheDocument()
  })

  it('EUDR indeterminado no se muestra; compacto muestra el sello', () => {
    render(<StatusBadge status={st('gold', { eudr_attention: null })} />)
    expect(screen.queryByText('Atenção EUDR')).toBeNull()
    cleanup()
    render(<StatusBadge compact status={st('gold', { eudr_attention: true })} />)
    expect(screen.getByText('Atenção EUDR')).toBeInTheDocument()
  })

  it('enlace "Entenda o nível" solo cuando se pide (panel)', () => {
    render(<StatusBadge status={st('silver')} />)
    expect(screen.queryByRole('link')).toBeNull()
    cleanup()
    render(
      <MemoryRouter>
        <StatusBadge status={st('silver')} learnMore />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: /Entenda o nível/ })).toHaveAttribute('href', '/painel/nivel')
  })

  it('nunca usa "ilegal" ni "crime"', () => {
    const { container } = render(
      <StatusBadge
        status={st('bronze', {
          reasons: (['EMBARGO_VIGENTE', 'TI_UC_INTEGRAL', 'RL_APP_POS2020', 'DETER_GRAVE', 'ALERTA_ABERTA', 'DETER_DEGRADACAO', 'DADOS_PARCIAIS'] as const).map(
            (code) => ({ code, severity: 'silver' as const, n: 1, ha: 1 }),
          ),
        })}
      />,
    )
    expect(container.textContent).not.toMatch(/ilegal|crime/i)
  })
})
