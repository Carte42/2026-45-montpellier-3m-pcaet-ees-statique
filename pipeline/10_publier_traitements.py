"""10 — Publication des chaînes de traitement et inventaire des fichiers servis.

Le mémoire affirme que les chaînes de traitement sont versionnées et livrées
avec les résultats. Les scripts vivent dans `pipeline/`, qui est hors de
`public/` : ils sont donc versionnés, mais pas livrés. Ce script produit
`public/data/traitements.zip` pour que les deux moitiés de la phrase soient
vraies, et `public/data/fichiers.json`, l'inventaire que le volet « sources »
emploie pour offrir chaque fichier en téléchargement.

L'inventaire est construit en parcourant le dossier servi : il ne peut pas
annoncer un fichier absent, ni en oublier un.

Usage :
    python 10_publier_traitements.py
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent.parent
PIPELINE = RACINE / "pipeline"
PUBLIC = RACINE / "public"
DATA = PUBLIC / "data"
ARCHIVE = DATA / "traitements.zip"
INVENTAIRE = DATA / "fichiers.json"

# Ce que chaque fichier servi contient, en une ligne. Un fichier présent sur le
# disque et absent de cette table est signalé plutôt que publié sans légende.
LEGENDES = {
    "territoire.geojson": "Couche communale — 31 entités, 22 champs",
    "territoire_shp.zip": "La même couche au format Shapefile, avec son dictionnaire de champs",
    "territoire.csv": "Les mêmes indicateurs en tableur, sans géométrie",
    "communes_3m.geojson": "Contours communaux bruts, avant calcul",
    "artificialisation.geojson": "Polygones d'évolution de l'occupation du sol",
    "artificialisation_flux.json": "Flux de couverture du sol mesurés",
    "vegetation.geojson": "Indicateurs de couvert végétal par commune",
    "risques.geojson": "Risques recensés par commune",
    "matrice.json": "Matrice d'incidences, avec son échelle d'intensité et ses attributs",
    "matrice.csv": "La même matrice en tableur",
    "flux.csv": "Les mêmes flux en tableur",
    "synthese.json": "Indicateurs de synthèse à l'échelle du territoire",
    "traitements.zip": "Les scripts qui produisent tout ce qui précède",
    "artificialisation_meta.json": "Fiche de métadonnées — artificialisation",
    "vegetation_meta.json": "Fiche de métadonnées — couvert végétal",
    "risques_meta.json": "Fiche de métadonnées — risques naturels",
    "perimetre_meta.json": "Fiche de métadonnées — périmètre et contours",
    "fonddeplan_meta.json": "Fiche de métadonnées — fond de plan",
    "fichiers.json": None,  # l'inventaire ne s'inventorie pas lui-même
    "planches_demonstrateur.pdf": "Cinq planches imprimables des trois volets",
    "B2_jeux_de_donnees.pdf": "Dictionnaire des données et fiches de métadonnées",
}

ORDRE = ["donnees", "fiches", "documents"]
FAMILLES = {
    "donnees": "Données et traitements",
    "fiches": "Fiches de métadonnées",
    "documents": "Documents imprimables",
}


def famille(nom: str, dossier: str) -> str:
    if dossier == "planches":
        return "documents"
    return "fiches" if nom.endswith("_meta.json") else "donnees"


def main() -> None:
    print("10 — Chaînes de traitement et inventaire des fichiers servis")
    print("=" * 70)

    # ── Archive des scripts ──────────────────────────────────────────────────
    scripts = sorted(PIPELINE.glob("*.py"))

    def objet(script: Path) -> str:
        """Première ligne de la chaîne de documentation du script."""
        premiere = script.read_text(encoding="utf-8").splitlines()[0]
        return premiere.strip('"').strip() or "—"

    lisez_moi = (
        "Chaînes de traitement du démonstrateur — Carte 42\n"
        "Marché M6C0007TE, lot 1, Montpellier Méditerranée Métropole\n\n"
        "Les scripts s'exécutent dans l'ordre de leur numéro. Chacun lit ce que le\n"
        "précédent a écrit dans public/data et n'a besoin d'aucun identifiant : toutes\n"
        "les sources sont ouvertes et interrogées sans authentification.\n\n"
        + "\n".join(f"  {s.name:26s} {objet(s)}" for s in scripts)
        + "\n\nDépendances : geopandas, rasterio, pyogrio, shapely, py7zr, pystac-client,\n"
          "matplotlib, reportlab, requests.\n"
    )
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LISEZ-MOI.txt", lisez_moi)
        for s in scripts:
            z.write(s, s.name)
    print(f"  traitements.zip : {len(scripts)} scripts, "
          f"{ARCHIVE.stat().st_size // 1024} Ko")

    # ── Inventaire ───────────────────────────────────────────────────────────
    entrees = []
    inconnus = []
    for dossier in ("data", "planches"):
        for f in sorted((PUBLIC / dossier).iterdir()):
            if not f.is_file():
                continue
            if f.name not in LEGENDES:
                inconnus.append(f"{dossier}/{f.name}")
                continue
            if LEGENDES[f.name] is None:
                continue
            entrees.append({
                "chemin": f"{dossier}/{f.name}",
                "nom": f.name,
                "legende": LEGENDES[f.name],
                "famille": famille(f.name, dossier),
                "octets": f.stat().st_size,
            })
    if inconnus:
        print(f"  ATTENTION — fichiers servis sans légende : {inconnus}")

    entrees.sort(key=lambda e: (ORDRE.index(e["famille"]), e["nom"]))
    INVENTAIRE.write_text(
        json.dumps({"familles": FAMILLES, "fichiers": entrees},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")

    for fam in ORDRE:
        n = sum(1 for e in entrees if e["famille"] == fam)
        print(f"  {FAMILLES[fam]:28s} {n} fichiers")
    print(f"  fichiers.json : {len(entrees)} entrées au total")


if __name__ == "__main__":
    main()
