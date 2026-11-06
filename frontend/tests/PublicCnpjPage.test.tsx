import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import PublicCnpjPage from '../src/pages/PublicCnpjPage'
import type { PublicCnpjReport } from '../src/types'

const report: PublicCnpjReport = {
  cnpj: '04654691000106',
  cnpj_formatted: '04.654.691/0001-06',
  registered: true,
  status: { level: 'silver', reason: null, partial: false, basis: 'provisional' },
  score: { state: 'em_calculo', value: null, computed_at: null, method_version: null },
  cars_count: 2,
  cars_with_data: 2,
  stale: false,
  data_as_of: '2026-11-05T14:02:11Z',
}

const notRegistered: PublicCnpjReport = {
  ...report,
  cnpj: '11222333000181',
  cnpj_formatted: '11.222.333/0001-81',
  registered: false,
  status: { level: 'sem_dados', reason: 'not_registered', partial: false, basis: 'provisional' },
  score: { state: 'nao_calculavel', value: null, computed_at: null, method_version: null },
  cars_count: 0,
  cars_with_data: 0,
  data_as_of: null,
}

function respond(status: number, body: unknown) {
  return vi.fn(async () => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/consulta" element={<PublicCnpjPage />} />
        <Route path="/consulta/:cnpj" element={<PublicCnpjPage />} />
        <Route path="/painel/consulta" element={<PublicCnpjPage basePath="/painel/consulta" />} />
        <Route path="/painel/consulta/:cnpj" element={<PublicCnpjPage basePath="/painel/consulta" />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => vi.restoreAllMocks())
afterEach(cleanup)

describe('PublicCnpjPage', () => {
  it('CNPJ inválido: muestra error y no llama a fetch', () => {
    const fetchMock = respond(200, report)
    vi.stubGlobal('fetch', fetchMock)
    renderAt('/consulta')
    fireEvent.change(screen.getByLabelText(/CNPJ do produtor/), { target: { value: '11.222.333/0001-00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar' }))
    expect(screen.getByRole('alert')).toHaveTextContent('CNPJ inválido')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('CNPJ válido navega y muestra la ficha sin códigos de CAR', async () => {
    vi.stubGlobal('fetch', respond(200, report))
    const { container } = renderAt('/consulta')
    fireEvent.change(screen.getByLabelText(/CNPJ do produtor/), { target: { value: '04654691000106' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar' }))
    expect(await screen.findByText('Silver')).toBeInTheDocument()
    expect(screen.queryByText(/Score/)).toBeNull() // o score ainda não existe: não se mostra
    expect(screen.getByText('2 propriedades informadas pelo produtor')).toBeInTheDocument()
    expect(container.textContent).not.toMatch(/PE-/)
  })

  it('CNPJ no registrado', async () => {
    vi.stubGlobal('fetch', respond(200, notRegistered))
    renderAt('/consulta/11222333000181')
    expect(await screen.findByText('CNPJ não cadastrado na plataforma')).toBeInTheDocument()
    expect(screen.getByText('Sem dados')).toBeInTheDocument()
    expect(screen.queryByText(/Score/)).toBeNull()
  })

  it('429 muestra el límite en minutos', async () => {
    vi.stubGlobal('fetch', respond(429, { detail: 'Limite', retry_after_s: 600 }))
    renderAt('/consulta/04654691000106')
    expect(await screen.findByRole('alert')).toHaveTextContent('Tente novamente em 10 minutos')
  })

  it('datos parciales', async () => {
    vi.stubGlobal('fetch', respond(200, { ...report, cars_with_data: 1, status: { ...report.status, partial: true } }))
    renderAt('/consulta/04654691000106')
    expect(await screen.findByText('Dados parciais: 1 de 2 propriedades.')).toBeInTheDocument()
  })

  it('permite reintentar el mismo CNPJ después de un fallo de conexión', async () => {
    const fetchMock = vi.fn()
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockResolvedValueOnce(new Response(JSON.stringify(report), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    renderAt('/consulta/04654691000106')
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível consultar agora')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('Silver')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[0][0]).toBe(fetchMock.mock.calls[1][0])
  })

  it('conserva el aviso de datos desactualizados y la fecha de la fuente', async () => {
    vi.stubGlobal('fetch', respond(200, { ...report, stale: true }))
    renderAt('/consulta/04654691000106')
    expect(await screen.findByText(/desatualizado/, { selector: '.stale-tag' })).toBeInTheDocument()
    expect(screen.getByText(/Dados de/)).toBeInTheDocument()
  })

  it('usa el mismo resumen público dentro del panel sin duplicar el encabezado', async () => {
    vi.stubGlobal('fetch', respond(200, report))
    const { container } = renderAt('/painel/consulta/04654691000106')
    expect(await screen.findByText('Silver')).toBeInTheDocument()
    expect(container.querySelector('.cnpj-header')).toBeNull()
    expect(container.querySelector('.cnpj-screen-in-panel')).toBeInTheDocument()
    expect(container.querySelector('.leaflet-container')).toBeNull()
    expect(screen.getByText('2 propriedades informadas pelo produtor')).toBeInTheDocument()
  })
})
