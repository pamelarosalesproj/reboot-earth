import { useId, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { t } from '../i18n/pt-BR'
import { maskCnpj } from '../lib/car'
import { normalizeCnpj } from '../lib/cnpj'

const P = t.publicSearch

interface Props {
  basePath?: '/consulta' | '/painel/consulta'
  initialValue?: string
}

/** Valida el CNPJ antes de navegar: si es inválido no se hace ninguna petición (FR-102). */
export default function CnpjSearch({ basePath = '/consulta', initialValue = '' }: Props) {
  const navigate = useNavigate()
  const [value, setValue] = useState(maskCnpj(initialValue))
  const [error, setError] = useState<string | null>(null)
  const id = useId()

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const digits = normalizeCnpj(value)
    if (!digits) {
      setError(P.invalid)
      return
    }
    setError(null)
    navigate(`${basePath}/${digits}`)
  }

  return (
    <form className="cnpj-search" onSubmit={submit} noValidate>
      <label htmlFor={id}>{P.label}</label>
        <div className="cnpj-search-row">
          <input
            id={id}
            inputMode="numeric"
            value={value}
            onChange={(e) => {
              setValue(maskCnpj(e.target.value))
              setError(null)
            }}
            placeholder={P.placeholder}
            aria-invalid={error ? true : undefined}
            aria-describedby={`${id}-hint${error ? ` ${id}-error` : ''}`}
            className={error ? 'invalid' : ''}
          />
          <button type="submit" className="btn btn-primary">
            {P.submit}
          </button>
        </div>
      <span className="field-hint" id={`${id}-hint`}>{P.searchHint}</span>
      {error && (
        <span className="field-error" id={`${id}-error`} role="alert">
          {error}
        </span>
      )}
    </form>
  )
}
