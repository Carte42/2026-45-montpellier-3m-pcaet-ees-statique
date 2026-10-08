import React, { useState } from 'react'
import Onboarding from './components/Onboarding.jsx'
import { THEMATIQUES, NB_COMMUNES, POPULATION } from './config.js'

export default function App() {
  const [volet, setVolet] = useState(1)
  const [theme, setTheme] = useState(THEMATIQUES[0].cle)

  return (
    <div className="app">
      <Onboarding />

      <aside className="sidebar">
        <header className="entete">
          <div className="entete-marche">M6C0007TE · Lot 1</div>
          <h1>Évaluation environnementale stratégique du PCAET</h1>
          <div className="entete-territoire">
            Montpellier Méditerranée Métropole · {NB_COMMUNES} communes ·{' '}
            {POPULATION.toLocaleString('fr-FR')} habitants
          </div>
        </header>

        <nav className="volets">
          {[
            { n: 1, titre: 'Planches d\u2019enjeux', phase: 'Phase 1' },
            { n: 2, titre: 'Matrice d\u2019incidences', phase: 'Phase 2' },
            { n: 3, titre: 'Fiche d\u2019indicateur', phase: 'Phase 3' },
          ].map((v) => (
            <button
              key={v.n}
              className={volet === v.n ? 'volet on' : 'volet'}
              onClick={() => setVolet(v.n)}
            >
              <span className="volet-phase">{v.phase}</span>
              <span className="volet-titre">{v.titre}</span>
            </button>
          ))}
        </nav>

        {volet === 1 && (
          <section data-ob-anchor="grille" className="bloc">
            <h2>Hiérarchisation des enjeux</h2>
            <p className="aide">
              Trois critères croisés : sensibilité du milieu, niveau de pression,
              marge d&apos;action du plan climat.
            </p>
            {/* TODO pipeline : grille notée par enjeu, depuis public/data */}
          </section>
        )}

        <section data-ob-anchor="export" className="bloc">
          <h2>Exports</h2>
          <p className="aide">
            Couches en GeoJSON, matrice en tableur, chaîne de calcul de l&apos;indicateur.
          </p>
          {/* TODO pipeline : boutons de telechargement */}
        </section>

        <footer className="mention">
          Démonstration de méthode établie à partir de données ouvertes
          exclusivement. Ne constitue pas une évaluation environnementale et
          n&apos;engage pas Montpellier Méditerranée Métropole.
        </footer>
      </aside>

      <main className="carte">
        <div className="selecteur-themes">
          {THEMATIQUES.map((t) => (
            <button
              key={t.cle}
              className={theme === t.cle ? 'theme on' : 'theme'}
              onClick={() => setTheme(t.cle)}
            >
              {t.libelle}
            </button>
          ))}
        </div>
        {/* TODO : MapView Leaflet, fond IGN, choropleth par commune */}
        <div className="carte-attente">Carte — à brancher sur le pipeline</div>
      </main>
    </div>
  )
}
