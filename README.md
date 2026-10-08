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
| 1 — Planches d'enjeux | Phase 1, état initial de l'environnement | 3 enjeux sur les 31 communes, grille de hiérarchisation à trois critères affichée à côté de son résultat, classement communal |
| 2 — Matrice d'incidences | Phase 2, évaluation des incidences | Échelle des cinq attributs publiée avant tout résultat, matrice appliquée aux leviers de compétence de la Métropole — 14 croisements renseignés sur 24 —, et flux de couverture du sol mesurés |
| 3 — Fiche d'indicateur | Phase 3, dispositif de suivi | Un indicateur renseigné à l'état initial, avec sa source, son porteur, son pas de temps, son seuil d'alerte et sa chaîne de calcul |

Trois enjeux retenus sur les dix que le cahier des charges impose a minima, choisis parce que la
donnée ouverte existe et parce que le cahier des charges cite nommément les aléas correspondants
pour ce territoire : **artificialisation et occupation du sol**, **climat sous l'angle de
l'adaptation aux vagues de chaleur et du couvert végétal**, **risques naturels**.

## Exports

Couche communale en GeoJSON et en Shapefile, indicateurs communaux, matrice d'incidences et flux
de couverture en tableur, chiffres de synthèse en JSON. Les cinq sources employées sont
documentées dans le volet « sources et méthode » de l'interface : producteur, millésime, licence,
résolution de calcul et réserves de lecture.

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
| Artificialisation | Occupation du sol à grande échelle — couches d'artificialisation 2.0, IGN, différences 2018-2021 et 2021-2024 | GeoPackage départemental à télécharger — pas de service web vectoriel |
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

## Publication

**https://pcaet.carte42.fr** — publication automatique à chaque poussée sur `main`.

Le fichier `public/CNAME` porte le domaine personnalisé : Vite le recopie dans `dist/` à chaque
construction. Sans lui, chaque déploiement écraserait le domaine et la page retomberait sur
l'adresse `github.io`.
