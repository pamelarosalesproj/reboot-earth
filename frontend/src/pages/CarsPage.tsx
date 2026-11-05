import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, addCar, listCars, removeCar } from '../api/client'
import CarCard from '../components/CarCard'
import { t } from '../i18n/pt-BR'
import { isValidCar, normalizeCar } from '../lib/car'
import type { ProducerCar } from '../types'

function AddCarForm({ onAdded, large = false }: { onAdded: () => void; large?: boolean }) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!isValidCar(value)) {
      setError(t.auth.invalidCar)
      return
    }
    setBusy(true)
    try {
      await addCar(normalizeCar(value))
      setValue('')
      onAdded()
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 503 ? t.auth.tryLater : err instanceof Error ? err.message : t.auth.genericError,
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className={`add-car ${large ? 'add-car-lg' : ''}`} onSubmit={onSubmit} noValidate>
      <div className="add-car-row">
        <input
          aria-label={t.panel.addTitle}
          placeholder="PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          spellCheck={false}
          autoCapitalize="characters"
          className={error ? 'invalid' : ''}
        />
        <button className="btn btn-primary" disabled={busy}>
          {busy ? t.panel.adding : t.panel.add}
        </button>
      </div>
      {error && <span className="field-error">{error}</span>}
    </form>
  )
}

export default function CarsPage() {
  const [cars, setCars] = useState<ProducerCar[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(() => {
    listCars()
      .then(setCars)
      .catch(() => setError(t.auth.genericError))
  }, [])

  useEffect(reload, [reload])

  async function onRemove(code: string) {
    try {
      await removeCar(code)
      reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : t.auth.genericError)
    }
  }

  if (error) return <main className="page"><p className="form-error">{error}</p></main>
  if (!cars) return <main className="page"><p className="muted">{t.panel.loading}</p></main>

  if (cars.length === 0) {
    return (
      <main className="page">
        <section className="card empty-state">
          <h1>{t.panel.emptyTitle}</h1>
          <p className="muted">{t.panel.emptyText}</p>
          <AddCarForm onAdded={reload} large />
          <small className="muted">{t.auth.carsHint}</small>
        </section>
      </main>
    )
  }

  return (
    <main className="page">
      <div className="page-head">
        <h1>{t.sidebar.cars}</h1>
        <AddCarForm onAdded={reload} />
      </div>
      <div className="cards">
        {cars.map((car) => (
          <CarCard key={car.car_code} car={car} onRemove={onRemove} />
        ))}
      </div>
    </main>
  )
}
