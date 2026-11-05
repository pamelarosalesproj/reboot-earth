import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ApiError, getPublicCnpj } from '../api/client'
import CnpjReportCard from '../components/CnpjReportCard'
import CnpjSearch from '../components/CnpjSearch'
import { t } from '../i18n/pt-BR'
import { normalizeCnpj } from '../lib/cnpj'
import type { PublicCnpjReport } from '../types'

const P = t.publicSearch

type Result = { key: string } & ({ kind: 'ok'; report: PublicCnpjReport } | { kind: 'error'; message: string })

function errorMessage(e: unknown) {
  if (e instanceof ApiError && e.status === 429) {
    const s = Number((e.body as { retry_after_s?: number } | null)?.retry_after_s ?? 3600)
    return P.rateLimited(Math.max(1, Math.ceil(s / 60)))
  }
  if (e instanceof ApiError && e.status === 422) return P.invalid
  return P.error
}

/** Página "Consultar CNPJ": pública en /consulta y dentro del panel en /painel/consulta. */
export default function PublicCnpjPage({ basePath = '/consulta' }: { basePath?: '/consulta' | '/painel/consulta' }) {
  const { cnpj = '' } = useParams()
  const digits = cnpj ? normalizeCnpj(cnpj) : null
  // El resultado se guarda con su CNPJ: una respuesta atrasada de otro CNPJ nunca se muestra.
  const [result, setResult] = useState<Result | null>(null)

  useEffect(() => {
    if (!digits) return
    getPublicCnpj(digits)
      .then((report) => setResult({ key: digits, kind: 'ok', report }))
      .catch((e) => setResult({ key: digits, kind: 'error', message: errorMessage(e) }))
  }, [digits])

  const state = !cnpj
    ? null
    : !digits
      ? ({ kind: 'error', message: P.invalid } as const)
      : result?.key === digits
        ? result
        : ({ kind: 'loading' } as const)

  return (
    <main className="page public-cnpj">
      <h1>{P.title}</h1>
      <p className="muted">{P.subtitle}</p>
      <CnpjSearch key={cnpj} basePath={basePath} initialValue={digits ?? ''} />

      {state?.kind === 'loading' && <p className="muted">{P.loading}</p>}
      {state?.kind === 'error' && (
        <div className="error-box" role="alert">
          <p>{state.message}</p>
        </div>
      )}
      {state?.kind === 'ok' && <CnpjReportCard report={state.report} />}
    </main>
  )
}
