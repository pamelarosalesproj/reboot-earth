import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, login, register } from '../src/api/client'
import { AuthContext } from '../src/auth/AuthContext'
import { t } from '../src/i18n/pt-BR'
import LoginPage from '../src/pages/LoginPage'
import RegisterPage from '../src/pages/RegisterPage'

vi.mock('../src/api/client', async (importOriginal) => ({
  ...await importOriginal<typeof import('../src/api/client')>(),
  login: vi.fn(),
  register: vi.fn(),
}))

const producer = { email: 'produtor@example.com', cnpj: '04654691000106', cars: [] }
const setProducer = vi.fn()

function renderPage(path: '/login' | '/registro') {
  return render(
    <AuthContext.Provider value={{ producer: null, loading: false, setProducer, signOut: vi.fn() }}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/registro" element={<RegisterPage />} />
          <Route path="/painel" element={<h1>Painel</h1>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

function fillCredentials() {
  fireEvent.change(screen.getByLabelText(/^Email/), { target: { value: producer.email } })
  fireEvent.change(screen.getByLabelText(/^Senha/), { target: { value: 'senha-de-teste' } })
}

beforeEach(() => vi.resetAllMocks())
afterEach(cleanup)

describe('Páginas de acesso do produtor', () => {
  it('mantém o login, a sessão e a navegação para o painel', async () => {
    vi.mocked(login).mockResolvedValue(producer)
    renderPage('/login')
    fillCredentials()
    fireEvent.click(screen.getByRole('button', { name: t.auth.submitLogin }))
    expect(await screen.findByRole('heading', { name: 'Painel' })).toBeInTheDocument()
    expect(login).toHaveBeenCalledWith(producer.email, 'senha-de-teste')
    expect(setProducer).toHaveBeenCalledWith(producer)
  })

  it('mantém os dados enviados no cadastro e o aviso de privacidade', async () => {
    vi.mocked(register).mockResolvedValue(producer)
    renderPage('/registro')
    expect(screen.getByText(t.auth.cnpjPublicNotice)).toBeInTheDocument()
    fillCredentials()
    fireEvent.change(screen.getByLabelText(/^CNPJ/), { target: { value: producer.cnpj } })
    fireEvent.click(screen.getByRole('button', { name: t.auth.submitRegister }))
    expect(await screen.findByRole('heading', { name: 'Painel' })).toBeInTheDocument()
    expect(register).toHaveBeenCalledWith({ email: producer.email, password: 'senha-de-teste', cnpj: '04.654.691/0001-06' })
    expect(setProducer).toHaveBeenCalledWith(producer)
  })

  it('associa o erro retornado pelo servidor ao campo de CNPJ', async () => {
    vi.mocked(register).mockRejectedValue(new ApiError(422, { field: 'cnpj', detail: 'CNPJ inválido' }))
    renderPage('/registro')
    fillCredentials()
    fireEvent.click(screen.getByRole('button', { name: t.auth.submitRegister }))
    const field = screen.getByLabelText(/^CNPJ/)
    await waitFor(() => expect(field).toHaveAttribute('aria-invalid', 'true'))
    expect(field).toHaveAccessibleDescription(expect.stringContaining('CNPJ inválido'))
    expect(setProducer).not.toHaveBeenCalled()
  })

  it('apresenta falhas de login e permite alternar para criar conta', async () => {
    vi.mocked(login).mockRejectedValue(new ApiError(401, { detail: 'Email ou senha incorretos' }))
    renderPage('/login')
    fillCredentials()
    fireEvent.click(screen.getByRole('button', { name: t.auth.submitLogin }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou senha incorretos')
    expect(screen.getByRole('button', { name: t.auth.submitLogin })).toBeEnabled()
    fireEvent.click(screen.getByRole('link', { name: t.auth.registerTitle }))
    expect(screen.getByRole('heading', { name: t.auth.registerTitle })).toBeInTheDocument()
    expect(setProducer).not.toHaveBeenCalled()
  })
})
