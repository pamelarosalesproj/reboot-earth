import type { CarDetail, CarSummary, DashboardSummary, Me, ProducerCar, PublicCnpjReport } from '../types'

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
    const detail = (body as { detail?: unknown } | null)?.detail
    super(typeof detail === 'string' ? detail : `HTTP ${status}`)
    this.status = status
    this.body = body
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, {
      credentials: 'include',
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
    })
  } catch {
    throw new ApiError(0, { detail: 'Sem conexão com o servidor' })
  }
  if (res.status === 204) return undefined as T
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, body)
  return body as T
}

const json = (data: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(data) })
const q = (refresh?: boolean) => (refresh ? '?refresh=true' : '')
const enc = encodeURIComponent

export const register = (data: { email: string; password: string; cnpj: string }) =>
  apiFetch<Me>('/api/auth/register', json(data))
export const login = (email: string, password: string) => apiFetch<Me>('/api/auth/login', json({ email, password }))
export const logout = () => apiFetch<void>('/api/auth/logout', { method: 'POST' })
export const me = () => apiFetch<Me>('/api/auth/me')

export const getDashboard = () => apiFetch<DashboardSummary>('/api/dashboard')
export const listCars = () => apiFetch<ProducerCar[]>('/api/cars')
export const addCar = (car_code: string) => apiFetch<ProducerCar>('/api/cars', json({ car_code }))
export const removeCar = (code: string) => apiFetch<void>(`/api/cars/${enc(code)}`, { method: 'DELETE' })
export const getSummary = (code: string, refresh?: boolean) =>
  apiFetch<CarSummary>(`/api/cars/${enc(code)}/summary${q(refresh)}`)
export const getDetail = (code: string, refresh?: boolean) =>
  apiFetch<CarDetail>(`/api/cars/${enc(code)}/detail${q(refresh)}`)

/** Ficha pública de un CNPJ (sin sesión). 429 → ApiError con body.retry_after_s. */
export const getPublicCnpj = (cnpj: string) => apiFetch<PublicCnpjReport>(`/api/public/cnpj/${enc(cnpj)}`)
