import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { AuthContext } from '../src/auth/AuthContext'
import type { AuthState } from '../src/auth/AuthContext'
import LandingPage from '../src/pages/LandingPage'

function renderWith(producer: AuthState['producer']) {
  const value: AuthState = { producer, loading: false, setProducer: () => {}, signOut: async () => {} }
  return render(
    <AuthContext.Provider value={value}>
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

afterEach(cleanup)

describe('LandingPage', () => {
  it('sin sesión muestra Cadastrar-se y Entrar', () => {
    renderWith(null)
    const register = screen.getAllByRole('link', { name: 'Cadastrar-se' })
    const login = screen.getAllByRole('link', { name: 'Entrar' })
    expect(register[0]).toHaveAttribute('href', '/registro')
    expect(login[0]).toHaveAttribute('href', '/login')
    expect(screen.queryByRole('link', { name: 'Ir para o painel' })).toBeNull()
  })

  it('con sesión muestra solo Ir para o painel', () => {
    renderWith({ email: 'a@b.com', cnpj: '04654691000106', cars: [] })
    expect(screen.getAllByRole('link', { name: 'Ir para o painel' })[0]).toHaveAttribute('href', '/painel')
    expect(screen.queryByRole('link', { name: 'Cadastrar-se' })).toBeNull()
  })

  it('explica la fuente de datos', () => {
    renderWith(null)
    expect(screen.getAllByText(/MapBiomas Alerta/).length).toBeGreaterThan(0)
    expect(screen.getByText('Como funciona')).toBeInTheDocument()
  })
})
