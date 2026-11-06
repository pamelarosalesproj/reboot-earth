import '@testing-library/jest-dom/vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import CnpjReportView from '../src/components/CnpjReportView'

afterEach(cleanup)

const base = {
  status: 'ok' as const,
  nivel: 'silver' as const,
  titulo: 'Título',
  riscos: ['Risco 1'],
  contexto: ['Contexto 1'],
  ressalvas: ['Ressalva 1'],
  imoveis: [{ car_code: 'PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0', resumo: 'Resumo do imóvel' }],
  data_dos_dados: '2026-11-06',
}

describe('CnpjReportView', () => {
  it('exemplo: aviso de origem, seções e link de cada imóvel', () => {
    const { container } = render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'exemplo' }} /></MemoryRouter>)
    expect(screen.getByRole('note')).toHaveTextContent('Exemplo escrito manualmente')
    expect(screen.getByRole('note')).toHaveTextContent('Dados de 06/11/2026')
    for (const s of ['Riscos', 'Contexto', 'Ressalvas', 'Por imóvel', 'Silver']) expect(screen.getByText(s)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ver detalhes →' })).toHaveAttribute(
      'href',
      '/painel/cars/PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0',
    )
    expect(container.textContent).not.toMatch(/ilegal|crime/i)
  })

  it('agente: aviso de IA e de que o nível é calculado por regras', () => {
    render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'agente' }} /></MemoryRouter>)
    expect(screen.getByRole('note')).toHaveTextContent('Gerado por IA')
    expect(screen.getByRole('note')).toHaveTextContent('o nível é calculado por regras')
  })

  it('indisponível', () => {
    render(<MemoryRouter><CnpjReportView report={{ status: 'indisponivel' }} /></MemoryRouter>)
    expect(screen.getByText('Relatório ainda não disponível.')).toBeInTheDocument()
  })

  it('botão Exportar PDF visível mas ainda sem função (aria-disabled)', () => {
    render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'exemplo' }} /></MemoryRouter>)
    const btn = screen.getByRole('button', { name: /Exportar PDF/ })
    expect(btn).toHaveAttribute('aria-disabled', 'true')
    expect(btn).toHaveAccessibleDescription('Em breve: exportação do relatório em PDF')
  })
})
