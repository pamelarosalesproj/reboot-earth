import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../src/auth/AuthContext'
import type { AuthState } from '../src/auth/AuthContext'
import HomePage from '../src/pages/HomePage'
import type { CnpjOverview, CnpjReport, DashboardSummary } from '../src/types'

const dashboard: DashboardSummary = {
  cars_count: 7,
  alerts_count: 38,
  embargoes_count: 7,
  cars_with_data: 7,
  cars_unavailable: 0,
  cars_embargoes_unknown: 1,
  stale: false,
  oldest_fetched_at: '2026-11-06T13:42:26Z',
  cnpj_status: { level: 'bronze', reason: null, partial: true, basis: 'provisional' },
  cnpj_score: { state: 'em_calculo', value: null, computed_at: null, method_version: null },
}
const overview: CnpjOverview = {
  cars_count: 7,
  alerts_total: 38,
  open_alerts: { n: 36, ha: 376.06 },
  superseded_alerts: { n: 2, ha: 48.54 },
  embargoes_active: 7,
  cars_without_alert_data: 0,
  cars_embargoes_unknown: 1,
  data_as_of: '2026-11-06T13:42:26Z',
}
const report: CnpjReport = {
  status: 'ok',
  origem: 'exemplo',
  nivel: 'bronze',
  titulo: 'Embargos vigentes e desmatamento recente sem autorização registrada',
  riscos: ['7 embargos vigentes em 2 imóveis.'],
  contexto: ['9 focos de calor nos últimos 12 meses.'],
  ressalvas: ['O PRODES não registra regeneração.'],
  imoveis: [{ car_code: 'MT-5102504-FB5206A8AF224FDC8B7E1D19FCF26A8E', resumo: '5 embargos vigentes.' }],
  data_dos_dados: '2026-11-06',
}

function serve(routes: Record<string, { status?: number; body: unknown }>) {
  return vi.fn(async (url: string) => {
    const r = Object.entries(routes).find(([k]) => url.endsWith(k))?.[1]
    return new Response(JSON.stringify(r?.body ?? {}), { status: r?.status ?? (r ? 200 : 404) })
  })
}

function renderHome() {
  const value: AuthState = {
    producer: { email: 'cp.rosaless@gmail.com', cnpj: '88419439000102', cars: [] },
    loading: false,
    setProducer: () => {},
    signOut: async () => {},
  }
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Início como resumo do CNPJ (feature 005)', () => {
  it('status, 3 números e relatório; sem módulos de lotes', async () => {
    vi.stubGlobal('fetch', serve({
      '/api/dashboard': { body: dashboard },
      '/api/dashboard/overview': { body: overview },
      '/api/dashboard/report': { body: report },
    }))
    const { container } = renderHome()
    expect(await screen.findByRole('heading', { name: 'Relatório do CNPJ' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Status do CNPJ' })).toBeNull() // o nível foi para o relatório
    expect(screen.getByText('Bronze')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Entenda os níveis Gold, Silver e Bronze/ })).toHaveAttribute('href', '/painel/nivel')
    expect(screen.queryByRole('link', { name: /comprador vê/ })).toBeNull()
    expect(await screen.findByText('36 · 376,1 ha')).toBeInTheDocument()
    expect(screen.getByText('de 38 · 2 superadas')).toBeInTheDocument()
    expect(screen.getByText('1 CAR com embargos não determináveis')).toBeInTheDocument()
    expect(await screen.findByText(report.titulo!)).toBeInTheDocument()
    expect(screen.getByRole('note')).toHaveTextContent('Exemplo escrito manualmente')
    for (const gone of ['Lotes rastreados', 'Volume homologado', 'Conformidade EUDR', 'Rastreabilidade dos lotes']) {
      expect(container.textContent).not.toContain(gone)
    }
  })

  it('sem relatório nem números: o status continua visível e nada aparece como 0', async () => {
    vi.stubGlobal('fetch', serve({
      '/api/dashboard': { body: dashboard },
      '/api/dashboard/overview': { body: { ...overview, alerts_total: null, open_alerts: null, superseded_alerts: null, embargoes_active: null, cars_without_alert_data: 7, cars_embargoes_unknown: 7 } },
      '/api/dashboard/report': { body: { status: 'indisponivel' } },
    }))
    renderHome()
    expect(await screen.findByText('Relatório ainda não disponível.')).toBeInTheDocument()
    expect(screen.getAllByText('Indisponível').length).toBe(2)
    expect(screen.getByText('7 CARs sem dados no momento')).toBeInTheDocument()
    expect(screen.getByText('Bronze')).toBeInTheDocument()
  })

  it('erro nos endpoints novos não derruba o Início', async () => {
    vi.stubGlobal('fetch', serve({
      '/api/dashboard': { body: dashboard },
      '/api/dashboard/overview': { status: 500, body: {} },
      '/api/dashboard/report': { status: 500, body: {} },
    }))
    renderHome()
    expect(await screen.findByText('Não foi possível carregar os números agora.')).toBeInTheDocument()
    expect(screen.getByText('Relatório ainda não disponível.')).toBeInTheDocument()
    expect(screen.getByText('Bronze')).toBeInTheDocument()
  })
})
