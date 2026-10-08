// ── Services web IGN ─────────────────────────────────────────────────────────
export const IGN_WMS_URL = 'https://data.geopf.fr/wms-r/wms'

// Occupation du sol a grande echelle. Verifie le 8 octobre 2026 : les trois
// millesimes renvoient de la donnee au-dessus de Montpellier. Le demonstrateur
// se construit sur les deux premiers, certains ; la diffusion du troisieme sur
// l'Herault etait annoncee pour le quatrieme trimestre 2026 et reste a
// confirmer sur la donnee vectorielle avant d'etre exploitee.
export const OCSGE_M1 = 'OCSGE.COUVERTURE.2017-2020'
export const OCSGE_M2 = 'OCSGE.COUVERTURE.2021-2023'
export const OCSGE_M3 = 'OCSGE.COUVERTURE.2024-2026'   // sous reserve
export const OCSGE_ARTIF_M1 = 'OCSGE.ARTIF.2017-2020'
export const OCSGE_ARTIF_M2 = 'OCSGE.ARTIF.2021-2023'

export const ORTHO = 'ORTHOIMAGERY.ORTHOPHOTOS'
export const OMBRAGE = 'ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW'

// Piege de nommage IGN releve sur le demonstrateur SDE 35, conserve ici :
// ORTHOIMAGERY.ORTHOPHOTOS.ORTHO-EXPRESS.<annee> jusqu'en 2025,
// ORTHOIMAGERY.ORTHOPHOTOS.RVB-EXPRESS.<annee> a partir de 2026.
// ORTHO-EXPRESS.2026 renvoie une erreur.

// ── Cadrage ──────────────────────────────────────────────────────────────────
// Centre et zoom sur les 31 communes de Montpellier Mediterranee Metropole.
export const MAP_CENTER = [43.63, 3.87]
export const MAP_ZOOM = 10

// ── Perimetre ────────────────────────────────────────────────────────────────
// 31 communes, 522 542 habitants, etablis depuis l'API Decoupage administratif
// a partir du SIREN 243400017. Ces deux valeurs corroborent le cahier des
// charges, qui annonce 31 communes et 522 000 habitants en 2023.
export const EPCI_SIREN = '243400017'
export const NB_COMMUNES = 31
export const POPULATION = 522542

// ── Les trois thematiques du volet 1 ─────────────────────────────────────────
export const THEMATIQUES = [
  {
    cle: 'artificialisation',
    libelle: 'Artificialisation et occupation du sol',
    mesure: "Part de surface artificialisee par commune et son evolution entre les millesimes 2017-2020 et 2021-2023",
    source: "Occupation du sol a grande echelle, IGN",
  },
  {
    cle: 'chaleur',
    libelle: 'Vagues de chaleur et couvert vegetal',
    mesure: "Indice de vegetation par commune, calcule sur Sentinel-2",
    source: 'Sentinel-2 niveau 2A, programme Copernicus',
  },
  {
    cle: 'risques',
    libelle: 'Risques naturels',
    mesure: "Inventaire des risques par commune, territoire a risque important d'inondation et zonage sismique",
    source: 'Georisques — inventaire GASPAR',
  },
]
