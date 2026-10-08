import React, { useEffect, useMemo, useState } from 'react'
import Onboarding from './components/Onboarding.jsx'
import MapView from './components/MapView.jsx'
import { INDICATEURS, LEVIERS, ATTRIBUTS, CRITERES } from './config.js'

// Libellés d'affichage des clés de métadonnées. Les fichiers de données
// gardent des clés machine ; l'habillage se fait ici.
const LIBELLES = {
  producteur: 'Producteur',
  departement: 'Département',
  periodes: 'Périodes',
  projection_de_calcul: 'Projection de calcul',
  perimetre: 'Périmètre',
  unite: 'Unité',
  licence: 'Licence',
  note: 'Note',
  lecture_des_flux: 'Lecture des flux',
  scene: 'Scène',
  date: 'Date',
  couverture_nuageuse_scene_pct: 'Couverture nuageuse de la scène',
  acces: 'Accès',
  indice: 'Indice',
  resolution_de_calcul_m: 'Résolution de calcul',
  seuil_vegetation_faible: 'Seuil de végétation faible',
  classes_de_classification_ecartees: 'Classes de classification écartées',
  pixels_exploitables_pct: 'Pixels exploitables',
  note_vulnerabilite: 'Note sur la vulnérabilité',
  nb_appels: "Nombre d'appels",
  millesimes: 'Millésimes',
  date_de_publication: 'Date de publication',
  date_d_interrogation: "Date d'interrogation",
  reserve_de_lecture: 'Réserve de lecture',
  couche: 'Couche',
  usage: 'Usage',
  requete: 'Requête',
  resultat: 'Résultat',
  communes_par_risque: 'Communes concernées, par risque',
  territoires_a_risque_important_inondation: "Territoires à risque important d'inondation",
}

function valeurLisible(v) {
  if (Array.isArray(v)) {
    return v.map((e) =>
      typeof e === 'object' && e !== null
        ? Object.values(e).join(' — ')
        : String(e)
    ).join(' · ')
  }
  if (typeof v === 'object' && v !== null) {
    return Object.entries(v).map(([k, x]) => `${k} : ${x}`).join(' · ')
  }
  return String(v)
}

const nb = (v, d = 1) =>
  typeof v === 'number' && Number.isFinite(v)
    ? v.toLocaleString('fr-FR', { minimumFractionDigits: d, maximumFractionDigits: d })
    : '—'

// Poids d'un fichier, en kilo-octets, pour l'inventaire du volet « sources ».
const ko = (octets) => `${Math.max(1, Math.round(octets / 1024)).toLocaleString('fr-FR')} Ko`

export default function App() {
  const [territoire, setTerritoire] = useState(null)
  const [synthese, setSynthese] = useState(null)
  const [flux, setFlux] = useState([])
  const [matrice, setMatrice] = useState(null)
  const [metas, setMetas] = useState({})
  const [volet, setVolet] = useState(1)
  const [cleIndic, setCleIndic] = useState(INDICATEURS[0].cle)
  const [survol, setSurvol] = useState(null)
  const [sourcesOuvertes, setSourcesOuvertes] = useState(false)
  const [inventaire, setInventaire] = useState(null)

  useEffect(() => {
    const b = import.meta.env.BASE_URL
    Promise.all([
      fetch(`${b}data/territoire.geojson`).then((r) => r.json()),
      fetch(`${b}data/synthese.json`).then((r) => r.json()),
      fetch(`${b}data/artificialisation_flux.json`).then((r) => r.json()),
      fetch(`${b}data/artificialisation_meta.json`).then((r) => r.json()),
      fetch(`${b}data/vegetation_meta.json`).then((r) => r.json()),
      fetch(`${b}data/risques_meta.json`).then((r) => r.json()),
      fetch(`${b}data/matrice.json`).then((r) => r.json()),
      fetch(`${b}data/perimetre_meta.json`).then((r) => r.json()),
      fetch(`${b}data/fonddeplan_meta.json`).then((r) => r.json()),
    ])
      .then(([t, s, f, ma, mv, mr, mx, mp, mf]) => {
        setTerritoire(t)
        setSynthese(s)
        setFlux(f)
        setMatrice(mx)
        setMetas({ perimetre: mp, artificialisation: ma, vegetation: mv, risques: mr, fonddeplan: mf })
      })
      .catch((e) => console.error('Chargement des données', e))

    // L'inventaire des fichiers servis est produit par 10_publier_traitements.py
    // en parcourant le dossier publié : il ne peut annoncer que ce qui existe.
    fetch(`${b}data/fichiers.json`)
      .then((r) => r.json())
      .then(setInventaire)
      .catch((e) => console.error('Chargement de l’inventaire', e))
  }, [])

  const indic = useMemo(
    () => INDICATEURS.find((i) => i.cle === cleIndic) ?? INDICATEURS[0],
    [cleIndic]
  )
  const formate = useMemo(
    () => (v) => (typeof v === 'number' ? `${nb(v, indic.decimales)} ${indic.unite}` : '—'),
    [indic]
  )

  const classement = useMemo(() => {
    if (!territoire) return []
    return [...territoire.features]
      .filter((f) => typeof f.properties[indic.champ] === 'number')
      .sort((a, b) => b.properties[indic.champ] - a.properties[indic.champ])
  }, [territoire, indic])

  const art = synthese?.artificialisation
  const fluxPeriode = flux.filter((f) => f.periode === '2021-2024').slice(0, 5)

  return (
    <div className="app">
      <Onboarding />

      <aside className="sidebar">
        <header className="entete">
          <div className="entete-marche">M6C0007TE · Lot 1 · Carte 42</div>
          <h1>Évaluation environnementale stratégique du PCAET</h1>
          <div className="entete-territoire">
            {synthese
              ? `${synthese.territoire.nom} · ${synthese.territoire.communes} communes · ${synthese.territoire.population.toLocaleString('fr-FR')} habitants`
              : 'Chargement…'}
          </div>
        </header>

        <nav className="volets">
          {[
            { n: 1, romain: 'I', phase: 'Phase 1', titre: 'Planches d’enjeux' },
            { n: 2, romain: 'II', phase: 'Phase 2', titre: 'Matrice d’incidences' },
            { n: 3, romain: 'III', phase: 'Phase 3', titre: 'Fiche d’indicateur' },
          ].map((v) => (
            <button
              key={v.n}
              className={volet === v.n ? 'volet on' : 'volet'}
              onClick={() => setVolet(v.n)}
            >
              <span className="volet-num" aria-hidden="true">{v.romain}</span>
              <span className="volet-texte">
                <span className="volet-phase">{v.phase}</span>
                <span className="volet-titre">{v.titre}</span>
              </span>
            </button>
          ))}
        </nav>

        {/* ── Volet 1 ─────────────────────────────────────────────────────── */}
        {volet === 1 && (
          <>
            <section className="bloc">
              <h2>{indic.libelle}</h2>
              <p className="aide">{indic.lecture}</p>
              {survol && (
                <div className="survol-fiche">
                  <strong>{survol.nom}</strong>
                  <span>{formate(survol[indic.champ])}</span>
                </div>
              )}
            </section>

            <section className="bloc" data-ob-anchor="grille">
              <h2>Hiérarchisation des enjeux</h2>
              <p className="aide">
                Trois critères croisés, notés de 1 à 3. La note figure à côté de
                son résultat pour que le classement soit vérifiable.
              </p>
              <table className="grille">
                <thead>
                  <tr>
                    <th>Critère</th>
                    <th>Ce qu&apos;il mesure</th>
                    <th>Note</th>
                  </tr>
                </thead>
                <tbody>
                  {CRITERES.map((c) => (
                    <tr key={c.cle}>
                      <td>{c.libelle}</td>
                      <td className="petit">{c.mesure}</td>
                      <td className="note">{indic.notes[c.cle]}</td>
                    </tr>
                  ))}
                  <tr className="total">
                    <td colSpan={2}>Niveau d&apos;enjeu retenu</td>
                    <td className="note">
                      {CRITERES.reduce((s, c) => s + indic.notes[c.cle], 0)} / 9
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section className="bloc">
              <h2>Classement des communes</h2>
              <ol className="classement">
                {classement.slice(0, 8).map((f) => (
                  <li key={f.properties.code}>
                    <span>{f.properties.nom}</span>
                    <b>{formate(f.properties[indic.champ])}</b>
                  </li>
                ))}
              </ol>
            </section>
          </>
        )}

        {/* ── Volet 2 ─────────────────────────────────────────────────────── */}
        {volet === 2 && (
          <>
            <section className="bloc">
              <h2>Instrument d&apos;évaluation</h2>
              <p className="aide">
                Chaque croisement est qualifié selon cinq attributs. L&apos;échelle
                d&apos;intensité est publiée avec la matrice.
              </p>
              <ul className="attributs">
                {ATTRIBUTS.map((a) => (
                  <li key={a.cle}>
                    <b>{a.libelle}</b>
                    <span>{a.valeurs}</span>
                  </li>
                ))}
              </ul>
            </section>

            {matrice && (
              <section className="bloc">
                <h2>Matrice appliquée — {matrice.cellules.length} croisements</h2>
                <p className="aide">
                  Les trois enjeux croisés avec huit des leviers de compétence
                  de la Métropole. Chaque croisement porteur d&apos;une incidence
                  notable est qualifié selon les cinq attributs et porte sa
                  justification.
                </p>
                <table className="matrice">
                  <thead>
                    <tr><th>Levier</th><th>Enjeu</th><th>Sens</th><th>Int.</th></tr>
                  </thead>
                  <tbody>
                    {matrice.cellules.map((c, i) => (
                      <tr key={i} title={c.justification}>
                        <td>{c.levier}</td>
                        <td className="petit">{c.enjeu.split(' —')[0].split(' et ')[0]}</td>
                        <td className={c.sens === 'positif' ? 'pos' : 'neg'}>
                          {c.sens === 'positif' ? '+' : '−'}
                        </td>
                        <td className="note">{c.intensite}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="aide">
                  Survolez une ligne pour lire la justification. Les cinq attributs
                  complets et les justifications figurent dans l&apos;export tableur.
                </p>
              </section>
            )}

            <section className="bloc">
              <h2>Flux de couverture mesurés — 2021-2024</h2>
              <p className="aide">
                Surfaces consommées par l&apos;artificialisation, par classe de
                couverture du sol, sur les {synthese?.territoire.communes ?? 31}
                communes.
              </p>
              <ul className="flux">
                {fluxPeriode.map((f, i) => (
                  <li key={i}>
                    <span>
                      {f.depuis} <em>→</em> {f.vers}
                    </span>
                    <b>{nb(f.surface_ha)} ha</b>
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}

        {/* ── Volet 3 ─────────────────────────────────────────────────────── */}
        {volet === 3 && art && (
          <section className="bloc">
            <h2>Artificialisation nette annuelle</h2>
            <table className="fiche">
              <tbody>
                <tr><th>Définition</th><td>Solde des surfaces artificialisées et désartificialisées, rapporté à l&apos;année</td></tr>
                <tr><th>Unité</th><td>hectare par an</td></tr>
                <tr><th>Valeur 2018-2021</th><td><b>{nb(art.periodes[0].solde_ha / 3)} ha/an</b></td></tr>
                <tr><th>Valeur 2021-2024</th><td><b>{nb(art.periodes[1].solde_ha / 3)} ha/an</b></td></tr>
                <tr><th>Tendance</th><td className="baisse">{nb(art.evolution_du_rythme_pct)} %</td></tr>
                <tr><th>Source</th><td>OCS GE Artificialisation 2.0, IGN</td></tr>
                <tr><th>Porteur pressenti</th><td>Direction de l&apos;urbanisme et de l&apos;aménagement</td></tr>
                <tr><th>Pas de temps</th><td>triennal, au rythme des millésimes</td></tr>
                <tr><th>Seuil d&apos;alerte</th><td>retour au rythme de la période précédente</td></tr>
                <tr><th>Reproductible</th><td>oui — <code>pipeline/02_artificialisation.py</code></td></tr>
              </tbody>
            </table>
            <p className="aide">
              La valeur initiale est établie, et la chaîne de traitement qui la
              produit est livrée avec elle.
            </p>
          </section>
        )}

        <section className="bloc" data-ob-anchor="export">
          <h2>Exports</h2>
          <div className="exports">
            <a href={`${import.meta.env.BASE_URL}data/territoire.geojson`} download>
              Couche communale — GeoJSON
            </a>
            <a href={`${import.meta.env.BASE_URL}data/territoire_shp.zip`} download>
              Couche communale — Shapefile
            </a>
            <a href={`${import.meta.env.BASE_URL}data/territoire.csv`} download>
              Indicateurs communaux — tableur
            </a>
            <a href={`${import.meta.env.BASE_URL}data/matrice.csv`} download>
              Matrice d&apos;incidences — tableur
            </a>
            <a href={`${import.meta.env.BASE_URL}data/flux.csv`} download>
              Flux de couverture — tableur
            </a>
            <a href={`${import.meta.env.BASE_URL}data/synthese.json`} download>
              Chiffres de synthèse — JSON
            </a>
            <a
              href={`${import.meta.env.BASE_URL}planches/planches_demonstrateur.pdf`}
              download
            >
              Planches imprimables — PDF
            </a>
            <a
              href={`${import.meta.env.BASE_URL}planches/B2_jeux_de_donnees.pdf`}
              download
            >
              Dictionnaire des données et métadonnées — PDF
            </a>
            <button className="lien" onClick={() => setSourcesOuvertes(true)}>
              Sources et méthode
            </button>
          </div>
        </section>

        <footer className="mention">
          Démonstration de méthode établie à partir de données ouvertes
          exclusivement. Ne constitue pas une évaluation environnementale et
          n&apos;engage pas Montpellier Méditerranée Métropole.
        </footer>
      </aside>

      <main className="carte">
        <div className="selecteur-themes">
          {INDICATEURS.map((i) => (
            <button
              key={i.cle}
              className={cleIndic === i.cle ? 'theme on' : 'theme'}
              onClick={() => setCleIndic(i.cle)}
            >
              {i.court}
            </button>
          ))}
        </div>

        {territoire ? (
          <MapView
            territoire={territoire}
            champ={indic.champ}
            palette={indic.palette}
            format={formate}
            onSurvol={setSurvol}
          />
        ) : (
          <div className="carte-attente">Chargement du territoire…</div>
        )}

        {synthese && (
          <div className="bandeau-chiffres">
            <div>
              <b>{nb(synthese.artificialisation.periodes[1].solde_ha)} ha</b>
              <span>artificialisation nette 2021-2024</span>
            </div>
            <div>
              <b>{nb(synthese.artificialisation.evolution_du_rythme_pct)} %</b>
              <span>par rapport à 2018-2021</span>
            </div>
            <div>
              <b>{nb(synthese.vegetation.ndvi_moyen_territoire, 3)}</b>
              <span>indice de végétation moyen</span>
            </div>
            <div>
              <b>{synthese.risques.tri ? Object.values(synthese.risques.tri)[0] : '—'}</b>
              <span>communes en territoire à risque d&apos;inondation</span>
            </div>
          </div>
        )}
      </main>

      {sourcesOuvertes && (
        <div className="voile" onClick={() => setSourcesOuvertes(false)}>
          <div className="panneau-sources" onClick={(e) => e.stopPropagation()}>
            <div className="panneau-tete">
              <h2>Sources et méthode</h2>
              <button className="fermer" onClick={() => setSourcesOuvertes(false)}>×</button>
            </div>
            <div className="panneau-corps">
              {Object.entries(metas).map(([cle, m]) => (
                <section key={cle}>
                  <h3>{m.produit}</h3>
                  <dl>
                    {Object.entries(m)
                      .filter(([k]) => k !== 'produit')
                      .map(([k, v]) => (
                        <React.Fragment key={k}>
                          <dt>{LIBELLES[k] ?? k.replace(/_/g, ' ')}</dt>
                          <dd>{valeurLisible(v)}</dd>
                        </React.Fragment>
                      ))}
                  </dl>
                </section>
              ))}
              {inventaire && (
                <section>
                  <h3>Fichiers publiés</h3>
                  <p className="mention">
                    Chacun est téléchargeable directement. L&apos;archive des
                    traitements contient les scripts qui produisent tout le reste.
                  </p>
                  {Object.entries(inventaire.familles).map(([cle, titre]) => {
                    const lot = inventaire.fichiers.filter((f) => f.famille === cle)
                    if (!lot.length) return null
                    return (
                      <div key={cle} className="inventaire">
                        <h4>{titre}</h4>
                        <ul>
                          {lot.map((f) => (
                            <li key={f.chemin}>
                              <a href={`${import.meta.env.BASE_URL}${f.chemin}`} download>
                                {f.nom}
                              </a>
                              <span> — {f.legende}</span>
                              <span className="poids"> {ko(f.octets)}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )
                  })}
                </section>
              )}
              <p className="mention">
                Toutes les données employées sont ouvertes et accessibles sans
                authentification. Aucune donnée fournie par Montpellier
                Méditerranée Métropole n&apos;a été utilisée.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
