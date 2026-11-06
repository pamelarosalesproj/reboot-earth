import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../src/auth/AuthContext'
import type { AuthState } from '../src/auth/AuthContext'
import HomePage from '../src/pages/HomePage'
import type { DashboardSummary } from '../src/types'

const dashboard: DashboardSummary = {
  cars_count: 1,
  alerts_count: 0,
  embargoes_count: 1,
  cars_with_data: 1,
  cars_unavailable: 0,
  cars_embargoes_unknown: 0,
  stale: false,
  oldest_fetched_at: '2026-11-05T14:00:00Z',
  cnpj_status: { level: 'bronze', reason: null, partial: false, basis: 'provisional' },
  cnpj_score: { state: 'em_calculo', value: null, computed_at: null, method_version: null },
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

it('não inventa volumes, conformidade ou riscos quando a API não os fornece', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  render(<MemoryRouter><HomePage previewData={{ ...dashboard, alerts_count: null }} /></MemoryRouter>)
  expect(await screen.findByText('Os dados de lotes ainda não estão disponíveis.')).toBeInTheDocument()
  for (const name of ['Volume homologado', 'Conformidade EUDR', 'Alertas territoriais']) {
    const card = screen.getByRole('heading', { name }).closest('article')
    expect(card).toHaveTextContent('—')
    expect(card).not.toHaveTextContent('0%')
  }
  expect(screen.queryByText('DEMO-VERDE-01')).toBeNull()
  expect(screen.getByText('A distribuição será exibida quando a classificação de risco estiver disponível.')).toBeInTheDocument()
  expect(fetchMock).not.toHaveBeenCalled()
})

describe('HomePage — cómo ven los compradores mi CNPJ (FR-114)', () => {
  it('muestra el nivel del CNPJ y enlaza a la ficha pública', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(dashboard), { status: 200 })))
    const value: AuthState = {
      producer: { email: 'prod@test.com', cnpj: '04654691000106', cars: [] },
      loading: false,
      setProducer: () => {},
      signOut: async () => {},
    }
    render(
      <AuthContext.Provider value={value}>
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      </AuthContext.Provider>,
    )
    expect(await screen.findByText('Como compradores veem seu CNPJ')).toBeInTheDocument()
    expect(screen.getByText('Bronze')).toBeInTheDocument()
    expect(screen.getByText('Score em cálculo')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Ver ficha pública/ })).toHaveAttribute('href', '/consulta/04654691000106')
  })
})
