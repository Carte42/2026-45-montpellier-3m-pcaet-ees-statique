# Disponibilité des données ouvertes — vérifiée le 8 octobre 2026

Vérification faite en interrogeant directement les services, pas d'après de la documentation. Chaque ligne a été testée sur le territoire de Montpellier Méditerranée Métropole.

## Périmètre

| Élément | Source | Résultat |
|---|---|---|
| Liste et contours des communes | `geo.api.gouv.fr/epcis/243400017/communes` | **31 communes**, contours GeoJSON, 240 Ko |
| Population | même source | **522 542 habitants** |

Le numéro 243400017 est le SIREN de la Métropole, déduit du SIRET 24340001700022 porté à l'article 9.2 du cahier des clauses administratives particulières.

**Ces deux valeurs corroborent exactement le cahier des charges**, qui annonce « 31 communes et 522 000 habitants en 2023 ». C'est un point à utiliser : le périmètre du démonstrateur est celui de la Métropole, établi depuis une source officielle et vérifiable, pas une approximation.

## Thématique 1 — Artificialisation et occupation du sol

Service testé : `https://data.geopf.fr/wms-r/wms`, requêtes GetMap sur une emprise de 6 km centrée sur Montpellier.

| Couche | Réponse | Verdict |
|---|---|---|
| `OCSGE.COUVERTURE.2017-2020` | 190 816 o | donnée présente |
| `OCSGE.COUVERTURE.2021-2023` | 190 634 o | donnée présente |
| `OCSGE.COUVERTURE.2024-2026` | 190 392 o | donnée présente |
| `OCSGE.ARTIF.2017-2020` | 141 305 o | donnée présente |
| `OCSGE.ARTIF.2021-2023` | 140 730 o | donnée présente |
| `OCSGE.ARTIF.2024-2026` | 140 356 o | donnée présente |
| `ORTHOIMAGERY.ORTHOPHOTOS` | 167 942 o | donnée présente |
| `ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW` | 16 511 o | donnée présente |

**C'est le résultat le plus favorable de la vérification.** L'occupation du sol à grande échelle existe en **trois millésimes** sur ce territoire, et l'Institut national de l'information géographique et forestière publie en plus des couches d'artificialisation dédiées. Le démonstrateur peut donc présenter une **évolution mesurée entre deux dates officielles**, et non un état figé — ce qui est exactement l'argument d'analyse multi-temporelle du mémoire.

**Réserve à lever avant de s'appuyer sur le millésime 2024-2026.** La documentation de l'Institut annonçait une diffusion du troisième bloc pour l'Hérault au quatrième trimestre 2026, période dans laquelle nous entrons. Le service renvoie bien de la donnée, mais cela ne garantit pas que le département soit couvert plutôt que servi par une couche nationale partiellement renseignée. **Le démonstrateur se construit donc sur les deux millésimes certains**, et n'ajoute le troisième que si le contrôle sur la donnée vectorielle le confirme.

> **Levé le 8 octobre 2026.** Le contrôle sur la donnée vectorielle a été conduit : les couches de différence du produit Artificialisation 2.0 couvrent l'Hérault pour **2018-2021** (publiée le 16 septembre 2025) et **2021-2024** (publiée le 27 août 2026). Ce sont ces deux périodes que le démonstrateur mesure, et non les millésimes de couverture repérés ci-dessus au service de tuiles vectorielles. Le troisième bloc n'a pas été retenu.

Pour le calcul, la donnée vectorielle se télécharge par département au format GeoPackage depuis `geoservices.ign.fr/ocsge`. Le service web sert à l'affichage, le fichier vectoriel au calcul.

## Thématique 2 — Vagues de chaleur et couvert végétal

Service testé : catalogue STAC `earth-search.aws.element84.com/v1`, collection `sentinel-2-l2a`, sans authentification.

Emprise 3,70-4,05 E / 43,50-43,72 N, du 1ᵉʳ juin au 15 septembre 2026, couverture nuageuse inférieure à 10 % : **13 scènes disponibles**, dont une à 0 % de nuages le 13 septembre 2026.

> **Scène finalement retenue :** `S2A_31TEJ_20260806_1_L2A`, du **6 août 2026**, à 0,003 % de couverture nuageuse. Elle a été préférée à celle du 13 septembre parce qu'une prise de vue d'août rend compte de l'état du couvert végétal au cœur de la saison sèche, période sur laquelle porte l'enjeu d'exposition aux vagues de chaleur.

Bandes présentes sur chaque scène : `red`, `green`, `blue`, `nir`, `nir08`, `swir16`, `scl`, `visual`. Les bandes rouge et proche infrarouge permettent le calcul de l'indice de végétation ; la bande `scl` fournit le masque de classification pour écarter nuages et ombres.

L'accès est libre et les images sont servies en format optimisé pour le web, ce qui permet de ne lire que l'emprise utile sans télécharger la scène entière.

## Thématique 3 — Risques naturels

Service testé : `https://www.georisques.gouv.fr/api/v1`.

| Point d'entrée | Résultat sur Montpellier (34172) |
|---|---|
| `gaspar/risques?code_insee=` | inventaire renseigné : inondation, crue torrentielle ou à montée rapide, mouvement de terrain, affaissements et effondrements, éboulement ou chutes de blocs, glissement de terrain, tassements différentiels, séisme |
| `gaspar/tri?code_insee=` | territoire à risque important d'inondation **34DDTM20120167 — Montpellier-Lunel-Mauguio** |
| `zonage_sismique?code_insee=` | zone **2 — faible** |

Le point d'entrée `rga` relatif au retrait-gonflement des argiles exige d'autres paramètres que le code commune ; à reprendre lors de la construction.

L'interrogation se fait commune par commune, soit 31 appels, ce qui permet de constituer un inventaire par commune comparable à l'échelle de la Métropole.

## Ce qui n'est pas disponible par cette voie

Les périmètres Natura 2000 ne figurent pas au service web de l'Institut national de l'information géographique et forestière interrogé ici : seule la couche `PROTECTEDAREAS.PRSF` y est exposée. Ils sont publiés par l'Inventaire national du patrimoine naturel, qui dispose de ses propres services. Sans incidence sur le démonstrateur, la biodiversité n'étant pas retenue parmi les trois thématiques.

## Conclusion

Les trois thématiques retenues sont réalisables sur données ouvertes, et aucune ne dépend d'une donnée fournie par la Métropole. Le verrou que je redoutais — l'absence de couverture de l'occupation du sol à grande échelle sur l'Hérault — est levé, et avec une marge : deux périodes d'évolution certaines et un troisième bloc, non retenu.
