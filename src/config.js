// ── Services web IGN ─────────────────────────────────────────────────────────
export const IGN_WMS_URL = 'https://data.geopf.fr/wms-r/wms'
export const ORTHO = 'ORTHOIMAGERY.ORTHOPHOTOS'

// Gabarit de tuiles de la Géoplateforme. Leaflet substitue {z}/{x}/{y} ;
// la substitution d'emprise {bbox-…} relève d'une autre bibliothèque et
// provoque une erreur ici.
export const IGN_WMTS_URL =
  'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0' +
  '&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM' +
  '&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png'

// Piège de nommage IGN relevé sur le démonstrateur SDE 35, conservé ici :
// ORTHOIMAGERY.ORTHOPHOTOS.ORTHO-EXPRESS.<annee> jusqu'en 2025,
// ORTHOIMAGERY.ORTHOPHOTOS.RVB-EXPRESS.<annee> a partir de 2026.
// ORTHO-EXPRESS.2026 renvoie une erreur.

// ── Cadrage ──────────────────────────────────────────────────────────────────
export const MAP_CENTER = [43.63, 3.87]
export const MAP_ZOOM = 10

// ── Palettes ─────────────────────────────────────────────────────────────────
// Cinq classes, séquentielles, sombre vers clair. Une seule sémiologie par
// indicateur, constante d'une planche à l'autre.
export const PALETTES = {
  ocre: ['#2e2a1f', '#6b5a2e', '#a88a35', '#d8b74a', '#f6cc57'],
  vert: ['#123028', '#1d5a46', '#2a8f6d', '#35b88c', '#45c6a4'],
  bleu: ['#16294d', '#2a4d7a', '#3d74ab', '#5CA6E0', '#bfdaf0'],
}

// ── Les trois enjeux du volet 1 ──────────────────────────────────────────────
// Les notes de hiérarchisation sont le résultat de la grille à trois critères
// exposée au volet 1, appliquée de façon identique aux trois enjeux.
export const INDICATEURS = [
  {
    cle: 'artificialisation',
    court: 'Artificialisation',
    libelle: 'Artificialisation nette 2021-2024',
    champ: 'net_2021-2024_ha',
    unite: 'ha',
    decimales: 1,
    palette: 'ocre',
    lecture:
      "Solde des surfaces artificialisées et désartificialisées sur la période, par commune. Source : couches d'évolution de l'occupation du sol à grande échelle, IGN.",
    notes: { sensibilite: 2, pression: 3, marge: 3 },
  },
  {
    cle: 'chaleur',
    court: 'Vagues de chaleur',
    libelle: 'Vulnérabilité aux vagues de chaleur',
    champ: 'vulnerabilite_chaleur',
    unite: '/ 100',
    decimales: 1,
    palette: 'vert',
    lecture:
      'Croisement du rang de faible végétation et du rang de densité de population. Indice de hiérarchisation entre communes, sans valeur absolue. Source : Sentinel-2, programme Copernicus.',
    notes: { sensibilite: 3, pression: 3, marge: 2 },
  },
  {
    cle: 'risques',
    court: 'Risques naturels',
    libelle: 'Nombre de familles de risques recensées',
    champ: 'nb_risques',
    unite: 'familles',
    decimales: 0,
    palette: 'bleu',
    lecture:
      "Familles de risques recensées par commune, agrégées au niveau parent de la nomenclature. Source : inventaire GASPAR, Géorisques.",
    notes: { sensibilite: 3, pression: 2, marge: 1 },
  },
]

// ── Grille de hiérarchisation ────────────────────────────────────────────────
export const CRITERES = [
  {
    cle: 'sensibilite',
    libelle: 'Sensibilité du milieu',
    mesure: "État du milieu concerné et sa capacité de retour à l'état initial",
  },
  {
    cle: 'pression',
    libelle: 'Niveau de pression',
    mesure: 'Intensité et tendance des pressions mesurées sur le territoire',
  },
  {
    cle: 'marge',
    libelle: "Marge d'action du plan",
    mesure: "Leviers dont la Métropole dispose effectivement sur cette pression",
  },
]

// ── Attributs de la matrice d'incidences ─────────────────────────────────────
export const ATTRIBUTS = [
  { cle: 'sens', libelle: 'Sens', valeurs: 'positif ou négatif' },
  { cle: 'voie', libelle: 'Voie', valeurs: 'direct ou indirect' },
  { cle: 'duree', libelle: 'Durée', valeurs: 'temporaire ou permanent' },
  { cle: 'horizon', libelle: 'Horizon', valeurs: '2030, 2040 ou 2050' },
  { cle: 'intensite', libelle: 'Intensité', valeurs: 'de 1 à 4, échelle publiée' },
]

// ── Leviers de compétence de la Métropole, cités au cahier des charges ──────
export const LEVIERS = [
  'Habitat et logement',
  'Mobilités et transports',
  'Urbanisme et aménagement',
  'Développement économique',
  'Réseaux énergétiques',
  'Ressource en eau et GEMAPI',
  'Gestion des déchets',
  'Preservation des ressources et de l\'espace',
]
