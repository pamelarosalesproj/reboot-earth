import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import LevelRulesPage from '../src/pages/LevelRulesPage'

afterEach(cleanup)

describe('Entenda o nível (feature 006, US4)', () => {
  it('explica criterios, CNPJ, EUDR, fuentes y glosario con los mismos umbrales de la regla', () => {
    const { container } = render(<LevelRulesPage />)
    for (const h of ['Os níveis', 'Nível de cada imóvel', 'O que nunca rebaixa o nível', 'Nível do CNPJ', 'Sinal "Atenção EUDR"', 'Fontes', 'Glossário']) {
      expect(screen.getByRole('heading', { name: h })).toBeInTheDocument()
    }
    const text = container.textContent ?? ''
    expect(text).toMatch(/1\s% ou mais da área do imóvel/) // RL_APP_THRESHOLD_PCT
    expect(text).toMatch(/últimos 24 meses/) // DETER_WINDOW_DAYS
    expect(text).toMatch(/imóvel em pior situação/)
    expect(text).not.toMatch(/ilegal|crime/i)
  })

  it('enlaza las fuentes y el reglamento EUDR, abriendo en una pestaña nueva', () => {
    render(<LevelRulesPage />)
    const eurlex = screen.getAllByRole('link', { name: /Regulamento \(UE\) 2023\/1115/ })
    expect(eurlex.length).toBe(2) // seção EUDR + glossário
    expect(eurlex[0]).toHaveAttribute('href', 'https://eur-lex.europa.eu/eli/reg/2023/1115/oj')
    for (const name of [/Plataforma MapBiomas Alerta/, /TerraBrasilis – DETER/, /Pamgia/, /SINAFLOR/]) {
      const link = screen.getByRole('link', { name })
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noreferrer')
    }
  })
})
