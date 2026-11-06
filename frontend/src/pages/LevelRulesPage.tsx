import type { ReactNode } from 'react'
import { t } from '../i18n/pt-BR'
import './LevelRulesPage.css'

const R = t.rules

function Terms({ items }: { items: readonly { term: string; text: string }[] }) {
  return (
    <dl className="rules-terms">
      {items.map((i) => (
        <div key={i.term}>
          <dt>{i.term}</dt>
          <dd>{i.text}</dd>
        </div>
      ))}
    </dl>
  )
}

function LevelColumn({ level, title, children }: { level: 'bronze' | 'silver' | 'gold'; title: string; children: ReactNode }) {
  return (
    <div className={`rules-column rules-column-${level}`}>
      <span className={`status-badge ${level}`}>
        <span className="status-dot" aria-hidden="true" />
        {t.status.level[level]}
      </span>
      <h3>{title}</h3>
      {children}
    </div>
  )
}

/** "Entenda o nível" (feature 006, US4): explica a regra de `services/level_rules.py` no painel. */
export default function LevelRulesPage() {
  return (
    <main className="page rules-page">
      <span className="overview-eyebrow">{R.eyebrow}</span>
      <h1>{R.title}</h1>
      <p className="rules-intro">{R.intro}</p>

      <section className="card" aria-labelledby="rules-levels">
        <h2 id="rules-levels">{R.levelsTitle}</h2>
        <ul className="rules-levels">
          {R.levels.map((l) => (
            <li key={l.level}>
              <span className={`status-badge ${l.level}`}>
                <span className="status-dot" aria-hidden="true" />
                {t.status.level[l.level]}
              </span>
              <span>{l.text}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="rules-car">
        <h2 id="rules-car">{R.carTitle}</h2>
        <p className="muted">{R.carIntro}</p>
        <div className="rules-columns">
          <LevelColumn level="bronze" title={R.bronzeTitle}>
            <Terms items={R.bronze} />
          </LevelColumn>
          <LevelColumn level="silver" title={R.silverTitle}>
            <Terms items={R.silver} />
          </LevelColumn>
          <LevelColumn level="gold" title={R.goldTitle}>
            <p>{R.gold}</p>
          </LevelColumn>
        </div>
      </section>

      <section className="card" aria-labelledby="rules-never">
        <h2 id="rules-never">{R.neverTitle}</h2>
        <p className="muted">{R.neverIntro}</p>
        <ul>
          {R.never.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="rules-cnpj">
        <h2 id="rules-cnpj">{R.cnpjTitle}</h2>
        <ul>
          {R.cnpj.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="rules-eudr">
        <h2 id="rules-eudr">{R.eudrTitle}</h2>
        <p>{R.eudr}</p>
      </section>

      <section className="card" aria-labelledby="rules-improve">
        <h2 id="rules-improve">{R.improveTitle}</h2>
        <ul>
          {R.improve.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </section>

      <section className="card" aria-labelledby="rules-sources">
        <h2 id="rules-sources">{R.sourcesTitle}</h2>
        <Terms items={R.sources} />
      </section>

      <section className="card" aria-labelledby="rules-glossary">
        <h2 id="rules-glossary">{R.glossaryTitle}</h2>
        <Terms items={R.glossary} />
      </section>

      <p className="muted small">{R.disclaimer}</p>
    </main>
  )
}
