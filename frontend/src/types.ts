// Tipos alineados con specs/001-producer-car-dashboard/contracts/openapi.yaml

export type MapBiomasStatus = 'found' | 'not_in_mapbiomas'

export interface ProducerCar {
  car_code: string
  mapbiomas_status: MapBiomasStatus
  added_at: string
}

export interface Me {
  email: string
  cnpj: string
  cars: ProducerCar[]
}

export type EmbargoesStatus = 'ok' | 'not_determinable' | 'unavailable'

export interface CarSummary {
  car_code: string
  state: string | null
  area_ha: number | null
  car_type: string | null
  geometry: GeoJSON.Geometry | null
  alerts_count: number | null
  embargoes_count: number | null
  embargoes_status: EmbargoesStatus
  fetched_at: string
  stale: boolean
  /** Nível deste CAR (mesma regra do CNPJ, só este imóvel). */
  status?: Status | null
}

export interface Alert {
  alert_code: number
  detected_at: string | null
  area_ha: number | null
  area_in_car_ha: number
  embargoes_count: number | null
}

export interface Embargo {
  source: string | null
  process_code: string | null
  area_ha: number | null
  registered_at: string | null
  expired_at: string | null
  descriptions: string[]
}

export interface CarDetail {
  summary: CarSummary
  alerts: Alert[]
  embargoes: Embargo[]
}

export interface DashboardSummary {
  cars_count: number
  alerts_count: number | null
  embargoes_count: number | null
  cars_with_data: number
  cars_unavailable: number
  cars_embargoes_unknown: number
  stale: boolean
  oldest_fetched_at: string | null
  // Feature 002: a nivel CNPJ, idénticos a la ficha pública
  cnpj_status: Status
  cnpj_score: Score
}

// Feature 002 (contracts/openapi.yaml)
export type StatusLevel = 'gold' | 'silver' | 'bronze' | 'sem_dados'
export type StatusReason = 'not_registered' | 'no_properties' | 'data_unavailable'

export type ReasonCode =
  | 'EMBARGO_VIGENTE'
  | 'TI_UC_INTEGRAL'
  | 'RL_APP_POS2020'
  | 'DETER_GRAVE'
  | 'ALERTA_ABERTA'
  | 'DETER_DEGRADACAO'
  | 'DADOS_PARCIAIS'

export interface Reason {
  code: ReasonCode
  severity: 'bronze' | 'silver'
  n?: number | null
  ha?: number | null
  pct?: number | null
  /** Só no CNPJ: em quantos imóveis. */
  cars?: number | null
}

export interface CarsByLevel {
  gold: number
  silver: number
  bronze: number
  sem_dados: number
}

export interface Status {
  level: StatusLevel
  reason: StatusReason | null
  partial: boolean
  basis: 'provisional' | 'regras' | 'score'
  /** Feature 006: motivos do nível, imóveis por nível (CNPJ) e sinal EUDR (null = indeterminado). */
  reasons?: Reason[]
  cars_by_level?: CarsByLevel | null
  eudr_attention?: boolean | null
  /** Conteos que usou a regra (agregados): explicam o nível com números. */
  alerts_count?: number | null
  embargoes_count?: number | null
}

export interface Score {
  state: 'em_calculo' | 'nao_calculavel' | 'disponivel'
  value: number | null
  computed_at: string | null
  method_version: string | null
}

export interface PublicCnpjReport {
  cnpj: string
  cnpj_formatted: string
  registered: boolean
  status: Status
  score: Score
  cars_count: number
  cars_with_data: number
  stale: boolean
  data_as_of: string | null
}

export interface ApiValidationError {
  detail: string
  field: string | null
  invalid_values: string[]
}

// Feature 003: indicadores del CAR (specs/003-car-indicators/contracts/openapi.yaml)
export type Situacao =
  | 'suspensa_judicial'
  | 'embargo_vigente'
  | 'autorizada'
  | 'embargo_levantado'
  | 'com_fiscalizacao'
  | 'pendente'
export type IndicatorSource = 'mapbiomas' | 'prodes' | 'deter' | 'focos' | 'sinaflor'
export type SourceState = 'ok' | 'indisponivel' | 'nao_se_aplica'

export interface SourceStatus {
  status: SourceState
  fetched_at: string | null
  stale: boolean
}

export interface Count {
  n: number
  ha: number
}

export interface AlertIndicator {
  alert_code: number
  detected_at: string | null
  area_in_car_ha: number
  status: Situacao
  post_2020: boolean
  authorized_ha: number
  legal_reserve_ha: number
  touches_app: boolean
  indigenous_land_ha: number
  integral_protection_ha: number
  sustainable_use_ha: number
  conservation_units: string[]
}

export interface CarIndicators {
  car_code: string
  fetched_at: string
  stale: boolean
  sources: Record<IndicatorSource, SourceStatus>
  alerts_by_status: Partial<Record<Situacao, Count>>
  open: {
    post_2020: Count | null
    legal_reserve_ha: number | null
    app_alerts: number | null
    embargoes_active: number | null
    indigenous_land_ha: number | null
    integral_protection_ha: number | null
  }
  context: {
    embargoes_lifted: number | null
    sustainable_use_ha: number | null
    sustainable_use_names: string[]
    native_vegetation: { remaining_pct: number; deforested_ha: number; by_year: Record<string, number> } | null
    deter: { by_class: Record<string, { n: number; ha: number; last: string | null }> } | null
    hotspots_12m: { count: number; by_month: Record<string, number> } | null
    forest_management: { authorizations: number; active: number; volume_m3: number; last_issued: string | null } | null
  }
  alerts: AlertIndicator[]
}

// Feature 005: Início como resumo do CNPJ (specs/005-dashboard-init/contracts/openapi.yaml)
export interface CnpjOverview {
  cars_count: number
  alerts_total: number | null
  open_alerts: Count | null
  superseded_alerts: Count | null
  embargoes_active: number | null
  cars_without_alert_data: number
  cars_embargoes_unknown: number
  data_as_of: string | null
}

export interface CnpjReport {
  status: 'ok' | 'indisponivel'
  origem?: 'exemplo' | 'agente' | null
  nivel?: StatusLevel | null
  titulo?: string | null
  riscos?: string[]
  contexto?: string[]
  ressalvas?: string[]
  imoveis?: { car_code: string; resumo: string }[]
  data_dos_dados?: string | null
  gerado_em?: string | null
}
