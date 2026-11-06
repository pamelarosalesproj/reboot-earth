import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import CarCard from '../src/components/CarCard'

vi.mock('../src/components/CarMap', () => ({ default: () => <div /> }))

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Tarjeta del CAR compacta', () => {
  it('no carga ni muestra indicadores; enlaza al detalle', async () => {
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ car_code: 'PE-1', state: 'PE', area_ha: 10, car_type: null, geometry: null,
        alerts_count: 3, embargoes_count: 0, embargoes_status: 'ok', fetched_at: '2026-11-06T12:00:00Z', stale: false })),
    )
    vi.stubGlobal('fetch', fetchMock)
    render(
      <MemoryRouter>
        <CarCard car={{ car_code: 'PE-1', mapbiomas_status: 'found', added_at: '2026-11-05T00:00:00Z' }} onRemove={async () => {}} />
      </MemoryRouter>,
    )
    expect(await screen.findByText('3 alertas')).toBeInTheDocument()
    expect(screen.queryByText('Riscos abertos')).toBeNull()
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/indicators'))).toBe(false)
    expect(screen.getByRole('link', { name: 'Ver detalhes' })).toHaveAttribute('href', '/painel/cars/PE-1')
  })
})
