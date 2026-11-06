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
const indicators = {
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
  it('muestra situación y nombre del APA', async () => {
    renderPage(true)
    expect(await screen.findByText('ÁREA DE PROTEÇÃO AMBIENTAL ILHA DO BANANAL/CANTÃO')).toBeInTheDocument()
    expect(screen.getByText('Sem autorização registrada')).toBeInTheDocument()
  })

  it('si los indicadores fallan, la tabla de alertas se muestra igual', async () => {
    renderPage(false)
    expect(await screen.findByText('1662462')).toBeInTheDocument()
    expect(screen.queryByText('Situação')).toBeNull()
  })
})
