"""05 — Consolidation.

Fusionne les sorties des trois volets en un fichier unique
`public/data/territoire.geojson` : une seule geometrie par commune, portant
l'ensemble des indicateurs. Evite de charger trois fois les memes contours.

Simplifie legerement les contours : le demonstrateur s'affiche a l'echelle de
la Metropole, une tolerance de 10 m est invisible a l'ecran et divise le poids
du fichier.

Produit aussi `public/data/synthese.json`, les chiffres de tete utilises par
l'interface, pour qu'aucune valeur ne soit ecrite en dur dans le code.

Usage :
    python 05_consolidation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent
DATA = RACINE.parent / "public" / "data"

TOLERANCE_M = 10.0
LAMBERT93 = "EPSG:2154"


def main() -> None:
    print("05 — Consolidation")
    print("=" * 70)

    base = gpd.read_file(DATA / "artificialisation.geojson")
    print(f"  artificialisation : {len(base)} communes, {len(base.columns)} champs")

    for nom, champs in [
        ("vegetation.geojson", ["ndvi_moyen", "part_vegetation_faible_pct",
                                "densite_hab_km2", "vulnerabilite_chaleur"]),
        ("risques.geojson", ["risques", "nb_risques", "tri", "sismicite"]),
    ]:
        autre = gpd.read_file(DATA / nom)
        presents = [c for c in champs if c in autre.columns]
        base = base.merge(autre[["code"] + presents], on="code", how="left")
        print(f"  {nom:26s} : {presents}")

    # Le champ des risques est une liste, relue en tableau par le pilote
    # GeoJSON : on le serialise en chaine, ce qui convient aussi a l'interface.
    if "risques" in base.columns:
        base["risques"] = base["risques"].apply(
            lambda v: " · ".join(map(str, v)) if hasattr(v, "__iter__") and not isinstance(v, str)
            else (v or "")
        )

    # ── Simplification des contours ──────────────────────────────────────────
    avant = sum((DATA / f).stat().st_size for f in
                ("artificialisation.geojson", "vegetation.geojson", "risques.geojson"))
    base = base.to_crs(LAMBERT93)
    base["geometry"] = base.geometry.simplify(TOLERANCE_M, preserve_topology=True)
    base = base.to_crs("EPSG:4326")
    base.to_file(DATA / "territoire.geojson", driver="GeoJSON")
    apres = (DATA / "territoire.geojson").stat().st_size
    print(f"\n  contours simplifies a {TOLERANCE_M:.0f} m : {avant // 1024} Ko → {apres // 1024} Ko")
    print(f"  ecrit : territoire.geojson ({apres // 1024} Ko, {len(base.columns)} champs)")

    # ── Chiffres de tete ─────────────────────────────────────────────────────
    def somme(champ: str) -> float:
        return round(float(base[champ].sum()), 1)

    veg = json.loads((DATA / "vegetation_meta.json").read_text(encoding="utf-8"))
    ris = json.loads((DATA / "risques_meta.json").read_text(encoding="utf-8"))

    synthese = {
        "territoire": {
            "nom": "Montpellier Méditerranée Métropole",
            "communes": int(len(base)),
            "population": int(base["population"].sum()),
            "surface_ha": somme("surface_commune_ha"),
        },
        "artificialisation": {
            "periodes": [
                {
                    "etiquette": "2018-2021",
                    "artificialise_ha": somme("artif_2018-2021_ha"),
                    "desartificialise_ha": somme("desartif_2018-2021_ha"),
                    "solde_ha": somme("net_2018-2021_ha"),
                },
                {
                    "etiquette": "2021-2024",
                    "artificialise_ha": somme("artif_2021-2024_ha"),
                    "desartificialise_ha": somme("desartif_2021-2024_ha"),
                    "solde_ha": somme("net_2021-2024_ha"),
                },
            ],
        },
        "vegetation": {
            "scene": veg["scene"],
            "date": veg["date"],
            "nuages_pct": veg["couverture_nuageuse_scene_pct"],
            "ndvi_moyen_territoire": round(float(base["ndvi_moyen"].mean()), 3),
            "pixels_exploitables_pct": veg["pixels_exploitables_pct"],
        },
        "risques": {
            "communes_par_risque": ris["communes_par_risque"],
            "tri": ris["territoires_a_risque_important_inondation"],
        },
    }

    a = synthese["artificialisation"]["periodes"][0]["solde_ha"]
    b = synthese["artificialisation"]["periodes"][1]["solde_ha"]
    synthese["artificialisation"]["evolution_du_rythme_pct"] = round((b - a) / a * 100, 1)

    (DATA / "synthese.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  ecrit : synthese.json")

    print("\nChiffres de tete :")
    print(f"  {synthese['territoire']['communes']} communes, "
          f"{synthese['territoire']['population']:,} habitants, "
          f"{synthese['territoire']['surface_ha']:,.0f} ha".replace(",", " "))
    print(f"  artificialisation nette : {a:+.1f} ha puis {b:+.1f} ha, "
          f"soit {synthese['artificialisation']['evolution_du_rythme_pct']:+.1f} %")
    print(f"  indice de vegetation moyen : {synthese['vegetation']['ndvi_moyen_territoire']}")
    print(f"  scene du {synthese['vegetation']['date']}, "
          f"{synthese['vegetation']['nuages_pct']} % de nuages")


if __name__ == "__main__":
    main()
