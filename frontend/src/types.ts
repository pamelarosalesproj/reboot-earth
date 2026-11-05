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

export interface Status {
  level: StatusLevel
  reason: StatusReason | null
  partial: boolean
  basis: 'provisional' | 'score'
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
