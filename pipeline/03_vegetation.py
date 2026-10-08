"""03 — Couvert vegetal et exposition aux vagues de chaleur.

Produit `public/data/vegetation.geojson` : par commune, l'indice de vegetation
moyen, la part de surface a vegetation faible, et la densite de population.

Source : Sentinel-2 niveau 2A, programme Copernicus, lu depuis le catalogue
STAC public sans authentification. Les images etant servies en format optimise
pour le web, seule l'emprise du territoire est lue, a la resolution utile.

L'indice retenu est l'indice de vegetation par difference normalisee, calcule
sur les bandes rouge et proche infrarouge. La bande de classification de la
scene sert a ecarter nuages, ombres et eau.

Le cahier des charges cite les vagues de chaleur et les canicules au premier
rang des risques climatiques du territoire. Le couvert vegetal en est le
principal facteur d'atenuation a l'echelle urbaine : une surface peu vegetalisee
et densement peuplee cumule l'exposition et l'enjeu humain.

Usage :
    python 03_vegetation.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import geometry_mask  # noqa: E402
from rasterio.windows import from_bounds  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent
SORTIE = RACINE.parent / "public" / "data"

STAC = "https://earth-search.aws.element84.com/v1/search"
FENETRE = ("2026-06-01T00:00:00Z", "2026-09-15T00:00:00Z")
BBOX = [3.70, 43.50, 4.05, 43.78]

RESOLUTION_M = 20          # resolution de travail, suffisante a l'echelle communale
SEUIL_FAIBLE = 0.20        # en dessous, on considere la vegetation faible

# Classes de la bande de classification Sentinel-2 a ecarter :
# 0 sans donnee, 1 sature, 3 ombre de nuage, 6 eau, 8 nuage probable,
# 9 nuage tres probable, 10 cirrus, 11 neige.
SCL_EXCLUES = {0, 1, 3, 6, 8, 9, 10, 11}


def choisir_scene() -> dict:
    """Retient la scene la moins nuageuse de la fenetre d'ete."""
    corps = {
        "collections": ["sentinel-2-l2a"],
        "bbox": BBOX,
        "datetime": f"{FENETRE[0]}/{FENETRE[1]}",
        "query": {"eo:cloud_cover": {"lt": 10}},
        "limit": 30,
    }
    req = urllib.request.Request(
        STAC,
        data=json.dumps(corps).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Carte42-pipeline/1.0"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        scenes = json.loads(r.read())["features"]
    scenes.sort(key=lambda s: s["properties"].get("eo:cloud_cover", 100))
    print(f"  scenes candidates : {len(scenes)}")
    for s in scenes[:4]:
        print(f"    {s['properties']['datetime'][:10]}  "
              f"{s['properties'].get('eo:cloud_cover', 0):.3f} %  {s['id']}")
    retenue = scenes[0]
    print(f"  scene retenue : {retenue['id']} "
          f"({retenue['properties'].get('eo:cloud_cover', 0):.3f} % de nuages)")
    return retenue


def lire_bande(href: str, bornes: tuple, forme: tuple[int, int]) -> np.ndarray:
    """Lit une bande sur l'emprise donnee, resamplee a la forme demandee."""
    with rasterio.open(href) as src:
        fenetre = from_bounds(*bornes, transform=src.transform)
        return src.read(1, window=fenetre, out_shape=forme, boundless=True, fill_value=0)


def main() -> None:
    print("03 — Couvert vegetal et exposition aux vagues de chaleur")
    print("=" * 70)

    scene = choisir_scene()
    crs_scene = f"EPSG:{scene['properties']['proj:epsg']}" if "proj:epsg" in scene["properties"] else None

    communes = gpd.read_file(SORTIE / "communes_3m.geojson")
    with rasterio.open(scene["assets"]["red"]["href"]) as src:
        crs_scene = src.crs
        transform_src = src.transform
    communes = communes.to_crs(crs_scene)
    print(f"  communes reprojetees en {crs_scene}")

    minx, miny, maxx, maxy = communes.total_bounds
    marge = 500.0
    bornes = (minx - marge, miny - marge, maxx + marge, maxy + marge)
    largeur = int((bornes[2] - bornes[0]) / RESOLUTION_M)
    hauteur = int((bornes[3] - bornes[1]) / RESOLUTION_M)
    print(f"  emprise : {largeur} x {hauteur} pixels a {RESOLUTION_M} m")

    print("  lecture des bandes…")
    rouge = lire_bande(scene["assets"]["red"]["href"], bornes, (hauteur, largeur)).astype("float32")
    proche_ir = lire_bande(scene["assets"]["nir"]["href"], bornes, (hauteur, largeur)).astype("float32")
    classif = lire_bande(scene["assets"]["scl"]["href"], bornes, (hauteur, largeur))
    print(f"    rouge {rouge.shape}, proche infrarouge {proche_ir.shape}, classification {classif.shape}")

    somme = proche_ir + rouge
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(somme > 0, (proche_ir - rouge) / somme, np.nan)

    valide = ~np.isin(classif, list(SCL_EXCLUES))
    ndvi = np.where(valide, ndvi, np.nan)
    part_valide = float(np.isfinite(ndvi).mean() * 100)
    print(f"    pixels exploitables apres masquage : {part_valide:.1f} %")

    transform = rasterio.transform.from_bounds(*bornes, largeur, hauteur)

    moyennes, parts_faibles = [], []
    for geom in communes.geometry:
        masque = geometry_mask(
            [geom], out_shape=(hauteur, largeur), transform=transform, invert=True
        )
        valeurs = ndvi[masque & np.isfinite(ndvi)]
        if valeurs.size == 0:
            moyennes.append(None)
            parts_faibles.append(None)
            continue
        moyennes.append(round(float(valeurs.mean()), 3))
        parts_faibles.append(round(float((valeurs < SEUIL_FAIBLE).mean() * 100), 1))

    communes["ndvi_moyen"] = moyennes
    communes["part_vegetation_faible_pct"] = parts_faibles
    communes["densite_hab_km2"] = (
        communes["population"] / (communes.geometry.area / 1e6)
    ).round(0)

    # Indice de vulnerabilite : croisement du rang de faible vegetation et du
    # rang de densite de population, ramene sur 100. C'est un indicateur de
    # lecture, destine a hierarchiser les communes entre elles.
    rang_veg = communes["part_vegetation_faible_pct"].rank(pct=True)
    rang_dens = communes["densite_hab_km2"].rank(pct=True)
    communes["vulnerabilite_chaleur"] = ((rang_veg + rang_dens) / 2 * 100).round(1)

    sortie = communes.to_crs("EPSG:4326")
    cible = SORTIE / "vegetation.geojson"
    sortie.to_file(cible, driver="GeoJSON")
    print(f"\n  ecrit : {cible.name} ({cible.stat().st_size // 1024} Ko)")

    meta = {
        "produit": "Sentinel-2 niveau 2A, programme Copernicus",
        "producteur": "Agence spatiale europeenne et Commission europeenne",
        "scene": scene["id"],
        "date": scene["properties"]["datetime"][:10],
        "couverture_nuageuse_scene_pct": round(
            float(scene["properties"].get("eo:cloud_cover", 0)), 3
        ),
        "acces": "catalogue STAC public, sans authentification",
        "indice": "Indice de vegetation par difference normalisee, bandes rouge et proche infrarouge",
        "resolution_de_calcul_m": RESOLUTION_M,
        "seuil_vegetation_faible": SEUIL_FAIBLE,
        "classes_de_classification_ecartees": sorted(SCL_EXCLUES),
        "pixels_exploitables_pct": round(part_valide, 1),
        "perimetre": "31 communes de Montpellier Mediterranee Metropole",
        "note_vulnerabilite": (
            "L'indice de vulnerabilite croise le rang de part de vegetation faible et le "
            "rang de densite de population. Il hierarchise les communes entre elles et "
            "n'a pas de valeur absolue. La densite communale est un substitut a la "
            "repartition fine de la population, qui releverait d'un carroyage."
        ),
    }
    (SORTIE / "vegetation_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  ecrit : vegetation_meta.json")

    apercu = communes[
        ["nom", "ndvi_moyen", "part_vegetation_faible_pct", "densite_hab_km2", "vulnerabilite_chaleur"]
    ].sort_values("vulnerabilite_chaleur", ascending=False).head(8)
    print("\nHuit communes au croisement le plus defavorable :")
    print(apercu.to_string(index=False))


if __name__ == "__main__":
    main()
