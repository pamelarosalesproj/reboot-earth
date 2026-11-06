import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import CarDetailPage from '../src/pages/CarDetailPage'

vi.mock('../src/components/CarMap', () => ({ default: () => <div /> }))

const CODE = 'TO-1712504-72577A629BF64D78A5DBF5F26734167B'
const detail = {
  summary: { car_code: CODE, state: 'TO', area_ha: 6350, car_type: null, geometry: null, alerts_count: 1,
    embargoes_count: 0, embargoes_status: 'ok', fetched_at: '2026-11-06T12:00:00Z', stale: false },
  alerts: [{ alert_code: 1662462, detected_at: '2026-08-28', area_ha: 3.9, area_in_car_ha: 2.36, embargoes_count: 0 }],
  embargoes: [],
}
const ok = { status: 'ok', fetched_at: '2026-11-06T12:00:00Z', stale: false }
const indicators = {
  car_code: CODE,
  fetched_at: '2026-11-06T12:00:00Z',
  stale: false,
  sources: { mapbiomas: ok, prodes: ok, deter: { ...ok, status: 'nao_se_aplica' }, focos: ok, sinaflor: ok },
  alerts_by_status: { pendente: { n: 1, ha: 2.36 } },
  open: { post_2020: { n: 1, ha: 2.36 }, legal_reserve_ha: 0, app_alerts: 0, embargoes_active: 0,
    indigenous_land_ha: 0, integral_protection_ha: 0 },
  context: { embargoes_lifted: 0, sustainable_use_ha: 2.36,
    sustainable_use_names: ['ÁREA DE PROTEÇÃO AMBIENTAL ILHA DO BANANAL/CANTÃO'],
    native_vegetation: { remaining_pct: 64.3, deforested_ha: 2283.7, by_year: {} }, deter: null,
    hotspots_12m: { count: 4, by_month: {} }, forest_management: { authorizations: 0, active: 0, volume_m3: 0, last_issued: null } },
  alerts: [{ alert_code: 1662462, detected_at: '2026-08-28', area_in_car_ha: 2.36, status: 'pendente', post_2020: true,
    authorized_ha: 0, legal_reserve_ha: 0, touches_app: false, indigenous_land_ha: 0, integral_protection_ha: 0,
    sustainable_use_ha: 2.36, conservation_units: ['ÁREA DE PROTEÇÃO AMBIENTAL ILHA DO BANANAL/CANTÃO'] }],
}

function renderPage(indicatorsOk: boolean) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.includes('/indicators')) {
      return indicatorsOk ? new Response(JSON.stringify(indicators)) : new Response('{}', { status: 500 })
    }
    return new Response(JSON.stringify(detail))
  }))
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

describe('Detalle: situación por alerta (US3)', () => {
  it('muestra el bloque de indicadores y la situación por alerta', async () => {
    renderPage(true)
    expect(await screen.findByText('Indicadores socioambientais')).toBeInTheDocument()
    expect(await screen.findByText('Riscos abertos')).toBeInTheDocument()
    expect(screen.getByText('Contexto')).toBeInTheDocument()
    expect(screen.getAllByText('Sem autorização registrada').length).toBe(2) // bloque + columna de la tabla
    expect(screen.getAllByText('ÁREA DE PROTEÇÃO AMBIENTAL ILHA DO BANANAL/CANTÃO').length).toBeGreaterThan(0)
  })

  it('si los indicadores fallan, la tabla de alertas se muestra igual', async () => {
    renderPage(false)
    expect(await screen.findByText('1662462')).toBeInTheDocument()
    expect(screen.queryByText('Situação')).toBeNull()
    expect(await screen.findByText('Indicadores indisponíveis no momento.')).toBeInTheDocument()
  })
})
