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

  it('agente: aviso "Gerado por IA" no topo, antes do título, e nota de que o nível vem das regras', () => {
    const { container } = render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'agente' }} /></MemoryRouter>)
    const badge = screen.getByText('Gerado por IA')
    const heading = screen.getByRole('heading', { name: 'Relatório do CNPJ' })
    expect(badge.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(container.querySelector('.overview-report')?.firstElementChild).toHaveClass('report-ai-badge')
    expect(screen.getByRole('note')).toHaveTextContent('O nível é calculado por regras fixas, nunca pela IA')
  })

  it('regras: sem o aviso de IA e com a nota de texto automático por regras', () => {
    render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'regras' }} /></MemoryRouter>)
    expect(screen.queryByText('Gerado por IA')).toBeNull()
    expect(screen.getByRole('note')).toHaveTextContent('Gerado automaticamente por regras (sem IA)')
  })

  it('exemplo: sem o aviso de IA', () => {
    render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'exemplo' }} /></MemoryRouter>)
    expect(screen.queryByText('Gerado por IA')).toBeNull()
  })

  it('cabeçalho com nível, sinal EUDR e imóveis por nível do painel; link para entender os níveis', () => {
    const status = { level: 'bronze' as const, reason: null, partial: false, basis: 'regras' as const, eudr_attention: true,
      cars_by_level: { gold: 4, silver: 1, bronze: 2, sem_dados: 0 },
      reasons: [{ code: 'EMBARGO_VIGENTE' as const, severity: 'bronze' as const, cars: 1 }] }
    const { container } = render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'agente' }} status={status} /></MemoryRouter>)
    expect(screen.getByText('Bronze')).toBeInTheDocument()
    expect(container.querySelector('.eudr-tag')).toHaveTextContent('Atenção EUDR')
    expect(screen.getByRole('button', { name: /Atenção EUDR/ })).toBeInTheDocument() // ajuda "?"
    expect(screen.getByText(/2 Bronze · 1 Silver · 4 Gold/)).toBeInTheDocument()
    expect(screen.queryByText('Motivos')).toBeNull() // a lista de motivos saiu: os riscos do relatório explicam
    expect(screen.getByRole('link', { name: /Entenda os níveis/ })).toHaveAttribute('href', '/painel/nivel')
  })

  it('por imóvel: coluna com o nível de cada CAR (regras)', () => {
    const imoveis = [
      { car_code: 'PA-1505031-86B4B9FFE117464385B1E4FCA3975AE8', resumo: '3 embargos vigentes.', nivel: 'bronze' as const },
      { car_code: 'AM-1303304-4B3B1D8060024401A46135766447CBA8', resumo: 'Sem alertas.', nivel: 'gold' as const },
    ]
    render(<MemoryRouter><CnpjReportView report={{ ...base, origem: 'agente', imoveis }} /></MemoryRouter>)
    const rows = screen.getAllByRole('listitem').filter((li) => li.querySelector('.report-car'))
    expect(rows[0]).toHaveTextContent(/PA-1505031.*Bronze.*3 embargos vigentes/)
    expect(rows[1]).toHaveTextContent(/AM-1303304.*Gold.*Sem alertas/)
  })

  it('relatório indisponível: o nível e o link continuam visíveis', () => {
    const status = { level: 'silver' as const, reason: null, partial: false, basis: 'regras' as const }
    render(<MemoryRouter><CnpjReportView report="error" status={status} /></MemoryRouter>)
    expect(screen.getByText('Relatório ainda não disponível.')).toBeInTheDocument()
    expect(screen.getByText('Silver')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Entenda os níveis/ })).toBeInTheDocument()
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
