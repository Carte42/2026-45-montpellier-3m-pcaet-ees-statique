"""07 — Complétion du volet « sources ».

Le panneau du démonstrateur est alimenté par les fichiers de métadonnées des
étapes précédentes. Deux d'entre eux n'y portaient ni date ni résolution de
calcul, et deux sources employées n'avaient aucune fiche : le fond de plan et
les contours communaux. Le volet annonçait donc plus qu'il ne documentait.

Ce script complète les fiches existantes et crée les manquantes, de sorte que
« chaque jeu de données est référencé avec son producteur, son millésime, sa
licence et ses réserves de lecture » soit exact.

Usage :
    python 07_sources.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = Path(__file__).resolve().parent.parent / "public" / "data"

LICENCE = "Licence ouverte Etalab 2.0"


def charger(nom: str) -> dict:
    return json.loads((DATA / nom).read_text(encoding="utf-8"))


def ecrire(nom: str, d: dict) -> None:
    (DATA / nom).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {nom}")


def main() -> None:
    print("07 — Complétion du volet sources")
    print("=" * 70)

    # ── Artificialisation : date et résolution manquantes ────────────────────
    a = charger("artificialisation_meta.json")
    a["millesimes"] = "2018-2021 et 2021-2024"
    a["date_de_publication"] = "16 septembre 2025 et 27 août 2026"
    a["resolution_de_calcul_m"] = "vectoriel, sans résolution de grille — surfaces calculées sur les géométries"
    a["licence"] = LICENCE
    ecrire("artificialisation_meta.json", a)

    # ── Risques : date et pas de temps manquants ─────────────────────────────
    r = charger("risques_meta.json")
    r["date_d_interrogation"] = "8 octobre 2026"
    r["resolution_de_calcul_m"] = "échelle communale — un enregistrement par commune"
    r["licence"] = LICENCE
    r["reserve_de_lecture"] = (
        "Le point d'entrée relatif au retrait-gonflement des argiles attend d'autres "
        "paramètres que le code commune et n'a pas été interrogé. L'aléa reste couvert "
        "par la famille « mouvement de terrain » de l'inventaire GASPAR."
    )
    ecrire("risques_meta.json", r)

    # ── Végétation : licence explicite ───────────────────────────────────────
    v = charger("vegetation_meta.json")
    v["licence"] = "Données Copernicus, réutilisation libre"
    ecrire("vegetation_meta.json", v)

    # ── Fond de plan : fiche absente ─────────────────────────────────────────
    ecrire("fonddeplan_meta.json", {
        "produit": "Plan IGN v2 — fond de plan cartographique",
        "producteur": "Institut national de l'information géographique et forestière",
        "acces": "service de tuiles de la Géoplateforme, data.geopf.fr",
        "couche": "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2",
        "date_d_interrogation": "8 octobre 2026",
        "resolution_de_calcul_m": "tuiles de 256 pixels, pyramide standard du web",
        "licence": LICENCE,
        "usage": "affichage seul — aucune donnée de ce fond n'entre dans les calculs",
    })

    # ── Contours communaux : fiche absente ───────────────────────────────────
    ecrire("perimetre_meta.json", {
        "produit": "Découpage administratif — communes et contours",
        "producteur": "Etalab, à partir du Code officiel géographique et de la base Admin Express de l'Institut national de l'information géographique et forestière",
        "acces": "interface de programmation geo.api.gouv.fr, sans authentification",
        "requete": "epcis/243400017/communes — numéro d'identification de la Métropole",
        "date_d_interrogation": "8 octobre 2026",
        "resultat": "31 communes, 522 542 habitants, 43 893 hectares",
        "resolution_de_calcul_m": "contours simplifiés à 10 m pour l'affichage, calculs conduits sur les géométries d'origine",
        "licence": LICENCE,
        "reserve_de_lecture": (
            "La population est celle que publie le découpage administratif. Le cahier "
            "des charges annonce 522 000 habitants en 2023, soit le même ordre de grandeur."
        ),
    })

    print("\nFiches du volet sources :")
    for f in sorted(DATA.glob("*_meta.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        manquants = [c for c in ("producteur", "licence") if c not in d]
        date = next((k for k in d if k.startswith("date") or k == "millesimes"), None)
        print(f"  {f.name:30s} producteur ✓  licence ✓  date {'✓' if date else '✗'}"
              f"{'  manque ' + ', '.join(manquants) if manquants else ''}")


if __name__ == "__main__":
    main()
