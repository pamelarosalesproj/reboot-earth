import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { AuthContext } from '../src/auth/AuthContext'
import type { AuthState } from '../src/auth/AuthContext'
import AppLayout, { initials } from '../src/layout/AppLayout'

afterEach(cleanup)

describe('initials', () => {
  it('usa las dos primeras partes del nombre del email', () => {
    expect(initials('maria.silva@fazenda.com')).toBe('MS')
    expect(initials('produtor@test.com')).toBe('PR')
    expect(initials('a@b.com')).toBe('A')
  })
})

describe('barra lateral', () => {
  it('no incluye Consultar CNPJ ni Gerar Relatório ESG (quitados del menú del productor)', () => {
    const value: AuthState = {
      producer: { email: 'a@b.com', cnpj: '04654691000106', cars: [] },
      loading: false,
      setProducer: () => {},
      signOut: async () => {},
    }
    render(
      <AuthContext.Provider value={value}>
        <MemoryRouter>
          <AppLayout />
        </MemoryRouter>
      </AuthContext.Provider>,
    )
    expect(screen.queryByRole('link', { name: /Consultar CNPJ/ })).toBeNull()
    expect(screen.queryByRole('link', { name: /Relatório ESG/i })).toBeNull()
  })
})
