import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { IndicatorsView } from '../src/components/CarIndicators'
import type { CarIndicators as Data } from '../src/types'

const ok = { status: 'ok' as const, fetched_at: '2026-11-06T12:00:00Z', stale: false }

function data(over: Partial<Data> = {}): Data {
  return {
    car_code: 'PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0',
    fetched_at: '2026-11-06T12:00:00Z',
    stale: false,
    sources: { mapbiomas: ok, prodes: ok, deter: { ...ok, status: 'nao_se_aplica' }, focos: ok, sinaflor: { ...ok, status: 'nao_se_aplica' } },
    alerts_by_status: {
      suspensa_judicial: { n: 0, ha: 0 },
      embargo_vigente: { n: 0, ha: 0 },
      autorizada: { n: 0, ha: 0 },
      embargo_levantado: { n: 0, ha: 0 },
      com_fiscalizacao: { n: 0, ha: 0 },
      pendente: { n: 3, ha: 74.46 },
    },
    open: {
      post_2020: { n: 3, ha: 74.46 },
      legal_reserve_ha: 27.07,
      app_alerts: 2,
      embargoes_active: 0,
      indigenous_land_ha: 0,
      integral_protection_ha: 0,
    },
    context: {
      embargoes_lifted: 0,
      sustainable_use_ha: 0,
      sustainable_use_names: [],
      native_vegetation: { remaining_pct: 2.1, deforested_ha: 260.3, by_year: {} },
      deter: null,
      hotspots_12m: { count: 1, by_month: { '2026-10': 1 } },
      forest_management: null,
    },
    alerts: [],
    ...over,
  }
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('IndicatorsView (feature 003)', () => {
  it('riscos abertos: pendente como "Sem autorização registrada" con n.º y ha', () => {
    render(<IndicatorsView d={data()} />)
    expect(screen.getByText('Sem autorização registrada')).toBeInTheDocument()
    expect(screen.getAllByText('3 · 74,5 ha').length).toBe(2) // pendente + pós-2020
    expect(screen.getByText('27,1 ha')).toBeInTheDocument()
  })

  it('0 confirmado se muestra como 0; nunca la palabra "ilegal"', () => {
    const { container } = render(<IndicatorsView d={data()} />)
    expect(container.textContent).not.toMatch(/ilegal/i)
    const embargoRow = screen.getByText('Embargos vigentes').closest('.ind-row')!
    expect(embargoRow).toHaveTextContent('0')
  })

  it('MapBiomas indisponível → "Indisponível", no 0', () => {
    const d = data({
      sources: { ...data().sources, mapbiomas: { status: 'indisponivel', fetched_at: null, stale: false } },
      alerts_by_status: {},
      open: { post_2020: null, legal_reserve_ha: null, app_alerts: null, embargoes_active: null, indigenous_land_ha: null, integral_protection_ha: null },
    })
    render(<IndicatorsView d={d} />)
    const row = screen.getByText('Embargos vigentes').closest('.ind-row')!
    expect(row).toHaveTextContent('Indisponível')
    expect(row).not.toHaveTextContent(/\b0\b/)
  })

  it('DETER fuera de la Amazonía y aviso de vegetación', () => {
    render(<IndicatorsView d={data()} />)
    expect(screen.getByText('Não se aplica a este bioma')).toBeInTheDocument()
    expect(screen.getByText(/não registra regeneração/)).toBeInTheDocument()
    expect(screen.getByText('2,1 %')).toBeInTheDocument()
  })

  it('DETER: CS_GEOMETRICO como padrão de manejo', () => {
    const d = data({
      sources: { ...data().sources, deter: ok },
      context: { ...data().context, deter: { by_class: { CS_GEOMETRICO: { n: 2, ha: 12.3, last: '2025-07-01' } } } },
    })
    render(<IndicatorsView d={d} />)
    expect(screen.getByText('Corte seletivo – padrão de manejo: 2 · 12,3 ha')).toBeInTheDocument()
  })

  it('APP tiene ayuda accesible que explica el término', () => {
    render(<IndicatorsView d={data()} />)
    const btn = screen.getByRole('button', { name: 'O que é APP?' })
    expect(screen.getByRole('tooltip', { hidden: true })).toHaveTextContent(/Área de Preservação Permanente/)
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
    expect(btn.closest('.ind-help')).toHaveClass('open')
  })
})
