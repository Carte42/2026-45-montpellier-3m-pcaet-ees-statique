# Chaîne de production

Les calculs lourds s'exécutent ici, hors ligne. Le site ne sert que les sorties
légères déposées dans `public/data/`.

## 01 — Périmètre

Déjà produit : `public/data/communes_3m.geojson`, 31 communes avec leurs
contours, population et surface, depuis l'API Découpage administratif.

```bash
curl -s "https://geo.api.gouv.fr/epcis/243400017/communes?fields=nom,code,population,surface&format=geojson&geometry=contour" \
  -o ../public/data/communes_3m.geojson
```

## 02 — Artificialisation par commune

L'occupation du sol à grande échelle n'est pas servie en service web vectoriel :
vérification faite le 8 octobre 2026, le catalogue du service web de l'IGN
n'expose aucun type d'objet national pour ce produit. Le vectoriel se télécharge
donc par département, au format GeoPackage, depuis `geoservices.ign.fr/ocsge`.

Étapes :

1. télécharger les deux millésimes de l'Hérault, 2017-2020 et 2021-2023, dans
   `pipeline/sources/` — non versionné ;
2. découper sur les 31 communes ;
3. agréger la surface artificialisée par commune et par millésime, selon la
   nomenclature couverture et usage du produit ;
4. écrire `public/data/artificialisation.geojson` : par commune, surface totale,
   surface artificialisée aux deux millésimes, écart absolu et part.

La sortie attendue pèse quelques dizaines de kilo-octets pour 31 entités.

## 03 — Couvert végétal

Catalogue STAC `earth-search.aws.element84.com/v1`, collection `sentinel-2-l2a`,
sans authentification. Vérification du 8 octobre 2026 : 13 scènes à moins de 10 %
de nuages entre le 1ᵉʳ juin et le 15 septembre 2026, dont une à 0 % le
13 septembre 2026. Bandes rouge et proche infrarouge pour l'indice de végétation,
bande de classification pour masquer nuages et ombres.

Les images étant servies en format optimisé pour le web, seule l'emprise utile
est lue : pas de téléchargement de scène entière.

## 04 — Risques naturels

API Géorisques, un appel par commune, soit 31 appels :

- `gaspar/risques?code_insee=` — inventaire des risques ;
- `gaspar/tri?code_insee=` — territoire à risque important d'inondation ;
- `zonage_sismique?code_insee=` — zone de sismicité.

Le point d'entrée `rga` relatif au retrait-gonflement des argiles attend d'autres
paramètres que le code commune : à reprendre.

Sortie : `public/data/risques.json`, un objet par commune.
