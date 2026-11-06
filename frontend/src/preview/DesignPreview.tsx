import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import { AuthContext } from '../auth/AuthContext'
import { t } from '../i18n/pt-BR'
import AppLayout from '../layout/AppLayout'
import HomePage from '../pages/HomePage'
import type { AuthState } from '../auth/AuthContext'
import type { CnpjOverview, CnpjReport, DashboardSummary } from '../types'
import LotOverview from '../components/LotOverview'
import type { LotOverviewData } from '../components/LotOverview'
import './DesignPreview.css'

// Este módulo se importa solo en desarrollo. No crea una sesión ni consulta el API.
const summary: DashboardSummary = {
  cars_count: 3,
  alerts_count: 1,
  embargoes_count: 0,
  cars_with_data: 3,
  cars_unavailable: 0,
  cars_embargoes_unknown: 0,
  stale: false,
  oldest_fetched_at: '2026-11-06T12:00:00Z',
  cnpj_status: {
    level: 'silver',
    reason: null,
    partial: false,
    basis: 'regras',
    reasons: [{ code: 'ALERTA_ABERTA', severity: 'silver', cars: 2 }],
    cars_by_level: { gold: 1, silver: 2, bronze: 0, sem_dados: 0 },
    eudr_attention: true,
  },
  cnpj_score: { state: 'em_calculo', value: null, computed_at: null, method_version: null },
}

const auth: AuthState = {
  producer: { email: 'produtor@exemplo.invalid', cnpj: '00000000000000', cars: [] },
  loading: false,
  setProducer: () => {},
  signOut: async () => { window.location.assign('/') },
}

const lots: LotOverviewData = {
  trackedLots: 3,
  approvedVolume: 255,
  eudrPercent: 33.3,
  territorialAlerts: 1,
  riskCounts: { low: 1, moderate: 0, high: 2 },
  lots: [
    { code: 'DEMO-VERDE-01', species: 'Ipê-amarelo', scientificName: 'Handroanthus heptaphyllus', origin: 'Fazenda Horizonte', car: 'CAR demonstrativo · MT-01', location: 'Mato Grosso · exemplo', volume: 50, authorizedVolume: 50, status: 'compliant', risk: 0, riskBand: 'low', reason: 'Cenário sem alertas territoriais ou divergências de volume.' },
    { code: 'DEMO-GEO-02', species: 'Maçaranduba', scientificName: 'Manilkara huberi', origin: 'Fazenda Boa Terra', car: 'CAR demonstrativo · PA-02', location: 'Pará · exemplo', volume: 80, authorizedVolume: 80, status: 'blocked', risk: 75, riskBand: 'high', reason: 'Alerta territorial simulado em área de origem do lote.' },
    { code: 'DEMO-VOL-03', species: 'Jatobá', scientificName: 'Hymenaea courbaril', origin: 'Manejo Vale do Sol', car: 'CAR demonstrativo · RO-03', location: 'Rondônia · exemplo', volume: 125, authorizedVolume: 100, status: 'blocked', risk: 65, riskBand: 'high', reason: 'Divergência simulada: volume excede o autorizado em 25 m³.' },
  ],
}

const overview: CnpjOverview = {
  cars_count: 3,
  alerts_total: 4,
  open_alerts: { n: 3, ha: 41.2 },
  superseded_alerts: { n: 1, ha: 6.5 },
  embargoes_active: 0,
  cars_without_alert_data: 0,
  cars_embargoes_unknown: 0,
  data_as_of: '2026-11-06T12:00:00Z',
}

const report: CnpjReport = {
  status: 'ok',
  origem: 'exemplo',
  nivel: 'silver',
  titulo: 'Alertas recentes sem autorização registrada em 2 dos 3 imóveis (cenário fictício)',
  riscos: ['3 alertas abertas somam 41,2 ha, todas posteriores a 31/12/2020.'],
  contexto: ['1 alerta autorizada (6,5 ha) não conta como risco aberto.'],
  ressalvas: ['Dados fictícios da prévia de design.'],
  imoveis: [
    { car_code: 'MT-0000000-DEMO01', resumo: '2 alertas de 2025 sem autorização registrada (30,0 ha).' },
    { car_code: 'PA-0000000-DEMO02', resumo: '1 alerta de 2026 sem autorização registrada (11,2 ha).' },
    { car_code: 'RO-0000000-DEMO03', resumo: 'Sem alertas abertas; 1 alerta autorizada.' },
  ],
  data_dos_dados: '2026-11-06',
}

function LotsPreview() {
  return (
    <main className="producer-overview">
      <h1>{t.preview.lotsTitle}</h1>
      <LotOverview preview={lots} territorialAlerts={lots.territorialAlerts} />
    </main>
  )
}

function PreviewOnly() {
  return <main className="page"><section className="card"><h1>{t.preview.limitedTitle}</h1><p>{t.preview.limitedText}</p><Link to="/painel" className="btn btn-primary">{t.preview.back}</Link></section></main>
}

export default function DesignPreview() {
  return (
    <div className="design-preview">
      <div className="design-preview-banner" role="note"><strong>{t.preview.notice}</strong><a href="/">{t.preview.exit} ↗</a></div>
      <AuthContext.Provider value={auth}>
        <BrowserRouter basename="/preview">
          <Routes>
            <Route element={<AppLayout />}>
              <Route
                path="/painel"
                element={<HomePage previewData={summary} previewOverview={overview} previewReport={report} />}
              />
              <Route path="/lotes" element={<LotsPreview />} />
              <Route path="*" element={<PreviewOnly />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthContext.Provider>
    </div>
  )
}
