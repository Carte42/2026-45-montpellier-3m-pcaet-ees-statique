# Démonstrateur — évaluation environnementale stratégique du PCAET de Montpellier Méditerranée Métropole

Interface de démonstration accompagnant la réponse de **Carte 42** au **lot 1** de la consultation
*« Appui à la révision du Plan Climat Air Énergie Territorial »* — Montpellier Méditerranée Métropole,
marché **M6C0007TE**, affaire interne **2026-45**.

Remise des offres : **mardi 3 novembre 2026, 12:00** sur marchespublics.montpellier3m.fr.

> Ce dépôt contient la chaîne de production et le site du démonstrateur.
> **Aucune pièce d'offre** — mémoire technique, acte d'engagement, décomposition du prix,
> bordereau, pièces administratives — n'y figure et n'y figurera.

> **Les résultats présentés sont une démonstration de méthode, établie à partir de données
> ouvertes exclusivement.** Ils ne constituent pas une évaluation environnementale et n'engagent
> ni Montpellier Méditerranée Métropole ni aucune autre collectivité.

## Ce que le démonstrateur doit prouver

L'évaluation environnementale stratégique du marché n'existe pas au moment de l'offre : elle sera
produite entre 2027 et 2030. Le démonstrateur reproduit donc, **à échelle réduite et sur le
territoire de l'acheteur**, la chaîne des trois premières phases du lot 1, pour que la Métropole
apprécie la qualité attendue sur son propre territoire plutôt que sur un territoire sans rapport
avec le sien.

| Volet | Phase du lot 1 | Contenu |
|---|---|---|
| 1 — Planches d'enjeux | Phase 1, état initial de l'environnement | 3 thématiques sur les 31 communes, avec la grille de hiérarchisation affichée à côté de son résultat |
| 2 — Matrice d'incidences | Phase 2, évaluation des incidences | Orientations du PCAET solidaire 2021-2026 croisées aux enjeux, échelle de notation publiée, export tableur |
| 3 — Fiche d'indicateur | Phase 3, dispositif de suivi | Un indicateur renseigné à l'état initial, avec sa source, son porteur, son pas de temps et sa chaîne de calcul |

Trois thématiques retenues sur les dix que le cahier des charges impose, choisies parce que la
donnée ouverte existe et parce que le cahier des charges les cite nommément pour ce territoire :
**artificialisation et occupation du sol**, **vagues de chaleur et couvert végétal**,
**risques naturels**.

## Périmètre

31 communes, 522 542 habitants, établis depuis `geo.api.gouv.fr/epcis/243400017` — le SIREN de la
Métropole, déduit du SIRET porté à l'article 9.2 du cahier des clauses administratives
particulières. Ces deux valeurs corroborent exactement le cahier des charges.

## Données

Vérification de disponibilité faite le 8 octobre 2026 en interrogeant les services, service par
service : voir **[docs/DONNEES.md](docs/DONNEES.md)**, qui donne les noms de couches exacts, les
tailles de réponse et les réserves.

| Thématique | Source | Accès |
|---|---|---|
| Artificialisation | Occupation du sol à grande échelle, IGN, millésimes 2017-2020 et 2021-2023 | GeoPackage départemental à télécharger — pas de service web vectoriel |
| Couvert végétal | Sentinel-2 niveau 2A, programme Copernicus | Catalogue STAC, sans authentification |
| Risques naturels | Géorisques — inventaire GASPAR, territoires à risque important d'inondation, zonage sismique | API, interrogation par commune |
| Fonds de plan | IGN | Service web `data.geopf.fr/wms-r/wms` |
| Contours communaux | API Découpage administratif, Etalab | API |

## Structure

```
docs/            notes de méthode et vérification des données
pipeline/        chaîne de production — calculs lourds, exécutés hors ligne
public/data/     sorties du pipeline, légères, publiées avec le site
src/             interface React
```

Le calcul se fait hors ligne et le site ne sert que des fichiers précalculés : il charge en moins
d'une seconde et ne dépend d'aucun service applicatif pendant la période d'analyse des offres.

## Développement

```bash
npm install
npm run dev
```

## Hébergement

Déploiement sur **pcaet.carte42.fr**, infrastructure OVH en France, comme l'ensemble des
productions mises en ligne par Carte 42.
