/** Símbolo Elo Rural: elo e folha em uma única forma, adaptado da identidade aprovada. */
export default function BrandMark({ inverse = false }: { inverse?: boolean }) {
  return <img className="elo-brand-mark" src={inverse ? '/elo-rural-symbol-inverse.svg' : '/elo-rural-symbol.svg'} alt="" aria-hidden="true" width="128" height="80" />
}
