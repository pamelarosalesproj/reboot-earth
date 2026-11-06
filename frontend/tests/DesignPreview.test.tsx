import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import DesignPreview from '../src/preview/DesignPreview'
import { AuthContext, RequireAuth } from '../src/auth/AuthContext'

afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.history.replaceState({}, '', '/') })

it('mostra o painel com dados fictícios sem chamar a API', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  window.history.replaceState({}, '', '/preview/painel')
  render(<DesignPreview />)
  expect((await screen.findAllByText('Silver')).length).toBeGreaterThan(0)
  expect(screen.getAllByRole('note')[0]).toHaveTextContent('dados fictícios')
  expect(screen.getByText('Relatório do CNPJ')).toBeInTheDocument()
  expect(screen.queryByText('DEMO-VERDE-01')).toBeNull()
  expect(fetchMock).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('link', { name: /Meus CARs/ }))
  expect(screen.getByText('Esta prévia mostra o Início do painel')).toBeInTheDocument()
  expect(fetchMock).not.toHaveBeenCalled()
})

it('mantém o painel real protegido quando não há sessão', () => {
  render(
    <AuthContext.Provider value={{ producer: null, loading: false, setProducer: vi.fn(), signOut: vi.fn() }}>
      <MemoryRouter initialEntries={['/painel']}>
        <Routes>
          <Route path="/painel" element={<RequireAuth><h1>Painel protegido</h1></RequireAuth>} />
          <Route path="/login" element={<h1>Login obrigatório</h1>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
  expect(screen.getByRole('heading', { name: 'Login obrigatório' })).toBeInTheDocument()
  expect(screen.queryByText('Painel protegido')).toBeNull()
})

it('filtra e busca os lotes fictícios em /preview/lotes, sem chamadas de rede', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  window.history.replaceState({}, '', '/preview/lotes')
  render(<DesignPreview />)
  expect(await screen.findByText('DEMO-VERDE-01')).toBeInTheDocument()
  expect(screen.getAllByRole('row')).toHaveLength(4)
  fireEvent.click(screen.getByRole('button', { name: 'Risco elevado' }))
  expect(screen.queryByText('DEMO-VERDE-01')).toBeNull()
  expect(screen.getAllByRole('row')).toHaveLength(3)
  fireEvent.change(screen.getByRole('textbox', { name: 'Buscar lotes' }), { target: { value: 'jatoba' } })
  expect(screen.getByText('DEMO-VOL-03')).toBeInTheDocument()
  expect(screen.queryByText('DEMO-GEO-02')).toBeNull()
  fireEvent.change(screen.getByRole('textbox', { name: 'Buscar lotes' }), { target: { value: 'inexistente' } })
  expect(screen.getByText('Nenhum lote encontrado para esta busca.')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Limpar filtros' }))
  expect(screen.getAllByRole('row')).toHaveLength(4)
  expect(fetchMock).not.toHaveBeenCalled()
})
