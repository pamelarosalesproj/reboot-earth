export const CAR_RE = /^[A-Z]{2}-\d{7}-[0-9A-F]{32}$/
export const normalizeCar = (v: string) => v.trim().toUpperCase()
export const isValidCar = (v: string) => CAR_RE.test(normalizeCar(v))

/** Máscara 00.000.000/0000-00 mientras se escribe. */
export function maskCnpj(v: string) {
  const d = v.replace(/\D/g, '').slice(0, 14)
  return d
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2')
}
