"""02 — Artificialisation par commune, sur les 31 communes de la Metropole.

Produit `public/data/artificialisation.geojson` : par commune, la surface
artificialisee sur chacune des deux periodes publiees par l'IGN, l'ecart, et la
part rapportee a la surface communale.

Source : OCS GE Artificialisation 2.0, couches de difference par departement.
L'IGN publie pour l'Herault deux periodes consecutives, ce qui donne une
trajectoire 2018 - 2021 - 2024 et non un simple ecart entre deux dates.

Les fichiers sont des couches de difference : seuls les polygones ayant change
y figurent, d'ou leur petite taille (1,2 a 1,6 Mo compresses).

Usage :
    python 02_artificialisation.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import geopandas as gpd
import py7zr

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent
SOURCES = RACINE / "sources"
SORTIE = RACINE.parent / "public" / "data"

BASE = "https://data.geopf.fr/telechargement/download/OCSGE-ARTIFICIALISATION"

PERIODES = [
    ("2018-2021", "OCS-GE-ARTIFICIALISATION_2-0_DIFF-2018-2021_GPKG_LAMB93_D034_2025-09-16"),
    ("2021-2024", "OCS-GE-ARTIFICIALISATION_2-0_DIFF-2021-2024_GPKG_LAMB93_D034_2026-08-27"),
]

LAMBERT93 = "EPSG:2154"


def telecharger(nom: str) -> Path:
    """Telecharge l'archive 7z si elle n'est pas deja presente."""
    SOURCES.mkdir(parents=True, exist_ok=True)
    cible = SOURCES / f"{nom}.7z"
    if cible.exists() and cible.stat().st_size > 10_000:
        print(f"  deja present : {cible.name} ({cible.stat().st_size // 1024} Ko)")
        return cible
    url = f"{BASE}/{nom}/{nom}.7z"
    print(f"  telechargement : {nom}.7z")
    # La Geoplateforme renvoie 403 sur l'agent par defaut d'urllib.
    req = urllib.request.Request(
        url, headers={"User-Agent": "Carte42-pipeline/1.0 (+https://carte42.fr)"}
    )
    with urllib.request.urlopen(req, timeout=300) as r, open(cible, "wb") as f:
        f.write(r.read())
    print(f"    recu : {cible.stat().st_size // 1024} Ko")
    return cible


def extraire(archive: Path) -> list[Path]:
    """Extrait l'archive et renvoie les GeoPackage trouves."""
    dossier = SOURCES / archive.stem
    if not dossier.exists():
        print(f"  extraction : {archive.name}")
        with py7zr.SevenZipFile(archive, "r") as z:
            z.extractall(path=dossier)
    gpkg = sorted(dossier.rglob("*.gpkg"))
    print(f"    GeoPackage : {[g.name for g in gpkg]}")
    return gpkg


def charger_communes() -> gpd.GeoDataFrame:
    chemin = SORTIE / "communes_3m.geojson"
    communes = gpd.read_file(chemin)
    communes = communes.to_crs(LAMBERT93)
    communes["surface_commune_ha"] = communes.geometry.area / 10_000.0
    print(f"  communes : {len(communes)}")
    return communes


# Nomenclature de couverture du sol de l'OCS GE, niveaux utiles aux flux.
# Source : arrete du 4 aout 2016 et specifications du produit.
COUVERTURE = {
    "CS1.1.1.1": "Zones baties",
    "CS1.1.1.2": "Zones non baties, revetues",
    "CS1.1.2.1": "Zones impermeables, autres",
    "CS1.1.2.2": "Zones impermeables, autres",
    "CS1.2.1": "Sols nus anthropises",
    "CS1.2.2": "Sols nus anthropises",
    "CS2.1.1.1": "Formations ligneuses hautes",
    "CS2.1.1.2": "Formations ligneuses basses",
    "CS2.1.1.3": "Formations ligneuses, autres",
    "CS2.1.2": "Formations herbacees",
    "CS2.1.3": "Autre vegetation",
    "CS2.2.1": "Sols nus naturels",
    "CS2.2.2": "Surfaces en eau",
    "CS2.2.3": "Neve et glace",
}


def libelle_cs(code: str) -> str:
    """Libelle de la classe de couverture, avec repli sur les niveaux superieurs."""
    code = str(code or "")
    while code:
        if code in COUVERTURE:
            return COUVERTURE[code]
        code = code.rsplit(".", 1)[0] if "." in code else ""
    return "Classe non renseignee"


def analyser_periode(
    gpkg: Path, communes: gpd.GeoDataFrame, etiquette: str
) -> tuple[gpd.GeoDataFrame, list[dict]]:
    """Decoupe la couche d'evolution sur les communes et separe les deux sens.

    Le produit porte un champ `artificialisation` valant 1 pour une
    artificialisation — passage de non artificialise a artificialise — et -1
    pour une desartificialisation. Le solde des deux est l'indicateur de
    l'objectif de zero artificialisation nette, et c'est celui qui compte pour
    une politique de sobriete fonciere.
    """
    couches = gpd.list_layers(gpkg)
    nom_couche = couches["name"].iloc[0]
    diff = gpd.read_file(gpkg, layer=nom_couche).to_crs(LAMBERT93)
    print(f"  couche : {nom_couche} — {len(diff)} polygones sur le departement")

    annees = sorted({c.split("_")[-1] for c in diff.columns if c.startswith("cs_")})
    av, ap = annees[0], annees[-1]

    garde = ["geometry", "artificialisation", f"cs_{av}", f"cs_{ap}"]
    decoupe = gpd.overlay(
        diff[garde], communes[["code", "geometry"]], how="intersection", keep_geom_type=True
    )
    decoupe["surface_ha"] = decoupe.geometry.area / 10_000.0

    artif = decoupe[decoupe["artificialisation"] > 0]
    desartif = decoupe[decoupe["artificialisation"] < 0]

    communes[f"artif_{etiquette}_ha"] = (
        communes["code"].map(artif.groupby("code")["surface_ha"].sum()).fillna(0.0).round(2)
    )
    communes[f"desartif_{etiquette}_ha"] = (
        communes["code"].map(desartif.groupby("code")["surface_ha"].sum()).fillna(0.0).round(2)
    )
    communes[f"net_{etiquette}_ha"] = (
        communes[f"artif_{etiquette}_ha"] - communes[f"desartif_{etiquette}_ha"]
    ).round(2)
    communes[f"net_{etiquette}_pct"] = (
        communes[f"net_{etiquette}_ha"] / communes["surface_commune_ha"] * 100
    ).round(3)

    print(
        f"    {etiquette} sur les 31 communes : "
        f"{artif['surface_ha'].sum():.1f} ha artificialises, "
        f"{desartif['surface_ha'].sum():.1f} ha desartificialises, "
        f"solde {artif['surface_ha'].sum() - desartif['surface_ha'].sum():+.1f} ha"
    )

    # ── Flux de couverture, pour la lecture qualitative ──────────────────────
    flux = (
        artif.assign(
            depuis=artif[f"cs_{av}"].map(libelle_cs),
            vers=artif[f"cs_{ap}"].map(libelle_cs),
        )
        .groupby(["depuis", "vers"])["surface_ha"]
        .sum()
        .round(1)
        .sort_values(ascending=False)
        .head(8)
    )
    liste_flux = [
        {"periode": etiquette, "depuis": d, "vers": v, "surface_ha": float(s)}
        for (d, v), s in flux.items()
    ]
    print(f"    trois flux principaux :")
    for f in liste_flux[:3]:
        print(f"      {f['depuis']} → {f['vers']} : {f['surface_ha']} ha")

    return communes, liste_flux


def main() -> None:
    print("02 — Artificialisation par commune")
    print("=" * 70)
    communes = charger_communes()

    etiquettes: list[str] = []
    tous_flux: list[dict] = []
    for etiquette, nom in PERIODES:
        print(f"\nPeriode {etiquette}")
        archive = telecharger(nom)
        gpkg = extraire(archive)
        if not gpkg:
            print("  aucun GeoPackage trouve, periode ignoree")
            continue
        communes, flux = analyser_periode(gpkg[0], communes, etiquette)
        etiquettes.append(etiquette)
        tous_flux.extend(flux)

    # ── Assemblage de la sortie ──────────────────────────────────────────────
    print("\nAssemblage")
    if len(etiquettes) == 2:
        a, b = etiquettes
        communes["tendance_ha"] = (
            communes[f"net_{b}_ha"] - communes[f"net_{a}_ha"]
        ).round(2)

    communes["surface_commune_ha"] = communes["surface_commune_ha"].round(1)
    (SORTIE / "artificialisation_flux.json").write_text(
        json.dumps(tous_flux, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  ecrit : artificialisation_flux.json")

    sortie = communes.to_crs("EPSG:4326")
    cible = SORTIE / "artificialisation.geojson"
    sortie.to_file(cible, driver="GeoJSON")
    print(f"  ecrit : {cible.name} ({cible.stat().st_size // 1024} Ko)")

    # ── Metadonnees, pour le volet « sources » du demonstrateur ──────────────
    meta = {
        "produit": "OCS GE Artificialisation 2.0, couches de difference",
        "producteur": "Institut national de l'information geographique et forestiere",
        "departement": "34 — Herault",
        "periodes": [{"etiquette": e, "fichier": n} for e, n in PERIODES if e in etiquettes],
        "projection_de_calcul": LAMBERT93,
        "perimetre": "31 communes de Montpellier Mediterranee Metropole",
        "unite": "hectare",
        "licence": "Licence ouverte Etalab",
        "note": (
            "Surfaces calculees par intersection des couches d'evolution avec les contours "
            "communaux, en Lambert-93. Ces couches ne contiennent que les polygones ayant "
            "change entre les deux millesimes. Le champ artificialisation vaut 1 pour une "
            "artificialisation et -1 pour une desartificialisation ; le solde des deux est "
            "l'indicateur de l'objectif de zero artificialisation nette."
        ),
        "lecture_des_flux": (
            "L'artificialisation se definit au produit par la combinaison de la couverture "
            "et de l'usage du sol. Un flux peut donc apparaitre sans changement de classe "
            "de couverture, lorsque seul l'usage a change."
        ),
    }
    (SORTIE / "artificialisation_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  ecrit : artificialisation_meta.json")

    # ── Controle a l'ecran ───────────────────────────────────────────────────
    cols = ["nom"] + [f"artif_{e}_ha" for e in etiquettes]
    apercu = communes[cols].sort_values(cols[-1], ascending=False).head(8)
    print("\nHuit communes les plus concernees :")
    print(apercu.to_string(index=False))


if __name__ == "__main__":
    main()
