import React, { useState, useEffect } from 'react'

/**
 * Accueil et visite guidée — même machine à états que les démonstrateurs
 * SDE 35 et EPTB Vistre Vistrenque : welcome → 1 → 2 → 3 → done.
 *
 * L'écran de bienvenue porte le test des dix secondes : un reviewer qui ne
 * clique rien doit savoir de quoi il s'agit, sur quel territoire, et ce qu'il
 * y a derrière. Les trois étapes suivantes sont ancrées sur les vrais
 * contrôles de l'interface via data-ob-anchor, et se repositionnent au resize.
 */
export default function Onboarding() {
  const [step, setStep] = useState('welcome')
  const [cardTop2, setCardTop2] = useState(230)
  const [cardTop3, setCardTop3] = useState(430)

  useEffect(() => {
    function computePositions() {
      if (step === 2) {
        const el = document.querySelector('[data-ob-anchor="grille"]')
        if (el) {
          const rect = el.getBoundingClientRect()
          const ideal = Math.round(rect.top + rect.height / 2)
          setCardTop2(Math.max(80, Math.min(ideal, window.innerHeight - 230)))
        }
      }
      if (step === 3) {
        const el = document.querySelector('[data-ob-anchor="export"]')
        if (el) {
          const rect = el.getBoundingClientRect()
          const ideal = Math.round(rect.top + rect.height / 2 - 85)
          setCardTop3(Math.max(80, Math.min(ideal, window.innerHeight - 260)))
        }
      }
    }
    computePositions()
    window.addEventListener('resize', computePositions)
    return () => window.removeEventListener('resize', computePositions)
  }, [step])

  function next() {
    if (step === 'welcome') setStep(1)
    else if (step === 1) setStep(2)
    else if (step === 2) setStep(3)
    else setStep('done')
  }

  if (step === 'done') return null

  return (
    <div className="ob-overlay">

      {/* ── Écran de bienvenue ── */}
      {step === 'welcome' && (
        <div className="ob-welcome-card">
          <div className="ob-glow" />
          <div className="ob-welcome-title">
            Bienvenue sur votre interface de démonstration
          </div>
          <div className="ob-welcome-subtitle">
            Évaluation environnementale stratégique du PCAET · M6C0007TE lot 1 · Carte 42
          </div>
          <div className="ob-welcome-text">
            31 communes, trois thématiques, données ouvertes exclusivement.
            Cette interface reproduit à échelle réduite la chaîne des phases 1 à 3
            du lot&nbsp;1 : état initial cartographié et hiérarchisé, matrice
            d'incidences, indicateur de suivi renseigné.
          </div>
          <button className="ob-start" onClick={next}>Commencer →</button>
        </div>
      )}

      {/* ── Étape 1 : les trois thématiques ── */}
      {step === 1 && (
        <div className="ob-card ob-card--bottom">
          <div className="ob-glow" />
          <div className="ob-body">
            <div className="ob-emoji">🗺</div>
            <div className="ob-title">Trois enjeux, trois cartes</div>
            <div className="ob-text">
              Artificialisation, vagues de chaleur et risques naturels — trois des
              dix thématiques imposées par le cahier des charges, celles que le
              cahier des charges cite nommément pour ce territoire.
            </div>
          </div>
          <button className="ob-ok" onClick={next}>OK, compris →</button>
          <div className="ob-arrow--down">▼</div>
        </div>
      )}

      {/* ── Étape 2 : la grille de hiérarchisation ── */}
      {step === 2 && (
        <div className="ob-card ob-card--left" style={{ top: cardTop2 }}>
          <div className="ob-glow" />
          <div className="ob-arrow--left-ext">◀</div>
          <div className="ob-body">
            <div className="ob-emoji">⚖</div>
            <div className="ob-title">Vérifiez le classement, ne le croyez pas</div>
            <div className="ob-text">
              Les trois critères de hiérarchisation sont notés enjeu par enjeu :
              sensibilité du milieu, niveau de pression, et marge d'action du plan
              climat. La grille est affichée à côté de son résultat.
            </div>
          </div>
          <button className="ob-ok" onClick={next}>OK, compris →</button>
        </div>
      )}

      {/* ── Étape 3 : exports ── */}
      {step === 3 && (
        <div className="ob-card ob-card--left-low" style={{ top: cardTop3 }}>
          <div className="ob-glow" />
          <div className="ob-body">
            <div className="ob-emoji">📥</div>
            <div className="ob-title">Tout est exportable</div>
            <div className="ob-text">
              La matrice d'incidences se télécharge en tableur manipulable avec ses
              règles de notation, les couches en GeoJSON compatible QGIS, et
              l'indicateur avec la chaîne de calcul qui produit sa valeur.
            </div>
          </div>
          <button className="ob-ok" onClick={next}>C'est parti ✓</button>
          <div className="ob-arrow--left-ext-bottom">◀</div>
        </div>
      )}
    </div>
  )
}
