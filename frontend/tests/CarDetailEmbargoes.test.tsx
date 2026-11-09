import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import CarDetailPage from '../src/pages/CarDetailPage'

vi.mock('../src/components/CarMap', () => ({ default: () => <div /> }))

const CODE = 'AM-1303304-4B3B1D8060024401A46135766447CBA8'
const summary = {
  car_code: CODE, state: 'AM', area_ha: 2968.4, car_type: null, geometry: null, alerts_count: 0,
  embargoes_count: 1, embargoes_status: 'ok', embargoes_source: 'ibama',
  embargoes_checked_at: '2026-11-08T23:24:47Z', embargoes_stale: false,
  fetched_at: '2026-11-08T23:24:47Z', stale: false,
}
const ibamaEmbargo = {
  source: 'IBAMA', process_code: '02048000439201263', area_ha: 240.17, registered_at: '2012-07-11',
  expired_at: null, descriptions: ['Fica embargada a área.'], term: '625137/C', overlap_ha: 12.5,
}

function renderPage(detail: object) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) =>
    url.includes('/indicators') ? new Response('{}', { status: 500 }) : new Response(JSON.stringify(detail))))
  render(
    <MemoryRouter initialEntries={[`/painel/cars/${CODE}`]}>
      <Routes>
        <Route path="/painel/cars/:code" element={<CarDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Detalhe: embargos do IBAMA (feature 007)', () => {
  it('mostra a fonte IBAMA, a ajuda e as colunas de termo e área no CAR', async () => {
    renderPage({ summary, alerts: [], embargoes: [ibamaEmbargo] })
    expect(await screen.findByText(/Fonte: IBAMA – áreas embargadas · consultado em/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Embargos do IBAMA/ })).toBeInTheDocument()
    expect(screen.getByText('Termo')).toBeInTheDocument()
    expect(screen.getByText('Área no CAR (ha)')).toBeInTheDocument()
    expect(screen.getByText('625137/C')).toBeInTheDocument()
  })

  it('sem embargos do IBAMA mostra "Nenhum embargo" com a fonte', async () => {
    renderPage({ summary: { ...summary, embargoes_count: 0 }, alerts: [], embargoes: [] })
    expect(await screen.findByText('Nenhum embargo.')).toBeInTheDocument()
    expect(screen.getByText(/Fonte: IBAMA – áreas embargadas/)).toBeInTheDocument()
  })

  it('com embargos do MapBiomas não mostra a ajuda nem as colunas do IBAMA', async () => {
    const mb = { ...ibamaEmbargo, term: null, overlap_ha: null }
    renderPage({ summary: { ...summary, embargoes_source: 'mapbiomas' }, alerts: [], embargoes: [mb] })
    expect(await screen.findByText(/Fonte: MapBiomas Alerta/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Embargos do IBAMA/ })).toBeNull()
    expect(screen.queryByText('Termo')).toBeNull()
  })

  it('avisa quando os embargos vêm de uma consulta anterior', async () => {
    renderPage({ summary: { ...summary, embargoes_stale: true }, alerts: [], embargoes: [ibamaEmbargo] })
    expect(await screen.findByText(/Nenhuma fonte respondeu agora/)).toBeInTheDocument()
  })
})
