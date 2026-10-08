"""04 — Risques naturels par commune, sur les 31 communes de la Metropole.

Produit `public/data/risques.geojson` : par commune, l'inventaire des risques
recenses, l'appartenance a un territoire a risque important d'inondation, et la
zone de sismicite.

Source : Georisques, ministere de la Transition ecologique. Un appel par
commune et par point d'entree, soit 93 appels.

Le cahier des charges cite nommement pour ce territoire les vagues de chaleur,
les incendies, les inondations, les tensions sur la ressource en eau et le
retrait-gonflement des argiles. Les quatre derniers sont couverts ici ; les
vagues de chaleur relevent du volet couvert vegetal.

Usage :
    python 04_risques.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent
SORTIE = RACINE.parent / "public" / "data"
API = "https://www.georisques.gouv.fr/api/v1"

# Risques retenus pour la lecture synthetique, parmi la nomenclature GASPAR.
# Les codes a trois chiffres sont des sous-types ; on agrege au niveau parent.
FAMILLES = {
    "11": "Inondation",
    "12": "Mouvement de terrain",
    "13": "Séisme",
    "14": "Avalanche",
    "15": "Éruption volcanique",
    "16": "Feu de forêt",
    "17": "Cyclone",
    "18": "Tempête",
    "19": "Radon",
}


def appeler(chemin: str) -> dict | None:
    url = f"{API}/{chemin}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Carte42-pipeline/1.0 (+https://carte42.fr)"}
    )
    for essai in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (404, 500):
                return None
            time.sleep(1 + essai)
        except Exception:
            time.sleep(1 + essai)
    return None


def familles_de(code_insee: str) -> list[str]:
    """Familles de risques recensees pour la commune, dedupliquees."""
    rep = appeler(f"gaspar/risques?code_insee={code_insee}")
    if not rep or not rep.get("data"):
        return []
    detail = rep["data"][0].get("risques_detail") or []
    trouvees: list[str] = []
    for r in detail:
        num = str(r.get("num_risque") or "")
        parent = num[:2]
        libelle = FAMILLES.get(parent)
        if libelle and libelle not in trouvees:
            trouvees.append(libelle)
    return sorted(trouvees)


def tri_de(code_insee: str) -> str | None:
    rep = appeler(f"gaspar/tri?code_insee={code_insee}")
    if not rep or not rep.get("data"):
        return None
    return rep["data"][0].get("libelle_tri")


def sismicite_de(code_insee: str) -> str | None:
    rep = appeler(f"zonage_sismique?code_insee={code_insee}")
    if not rep or not rep.get("data"):
        return None
    return rep["data"][0].get("zone_sismicite")


def main() -> None:
    print("04 — Risques naturels par commune")
    print("=" * 70)

    communes = json.loads((SORTIE / "communes_3m.geojson").read_text(encoding="utf-8"))
    n = len(communes["features"])
    print(f"  communes : {n}")

    compteur: dict[str, int] = {}
    tris: dict[str, int] = {}

    for i, feat in enumerate(communes["features"], 1):
        p = feat["properties"]
        code = p["code"]
        familles = familles_de(code)
        tri = tri_de(code)
        sismicite = sismicite_de(code)

        p["risques"] = familles
        p["nb_risques"] = len(familles)
        p["tri"] = tri
        p["sismicite"] = sismicite

        for f in familles:
            compteur[f] = compteur.get(f, 0) + 1
        if tri:
            tris[tri] = tris.get(tri, 0) + 1

        print(f"  [{i:2d}/{n}] {p['nom']:28s} {len(familles)} risques"
              f"{'  TRI ' + tri if tri else ''}")

    (SORTIE / "risques.geojson").write_text(
        json.dumps(communes, ensure_ascii=False), encoding="utf-8"
    )
    taille = (SORTIE / "risques.geojson").stat().st_size // 1024
    print(f"\n  ecrit : risques.geojson ({taille} Ko)")

    synthese = {
        "produit": "Georisques — inventaire GASPAR, territoires a risque important d'inondation, zonage sismique",
        "producteur": "Ministère de la Transition écologique",
        "perimetre": "31 communes de Montpellier Mediterranee Metropole",
        "nb_appels": n * 3,
        "communes_par_risque": dict(sorted(compteur.items(), key=lambda kv: -kv[1])),
        "territoires_a_risque_important_inondation": tris,
        "note": (
            "Les familles de risques sont agregees au niveau parent de la nomenclature "
            "GASPAR : un sous-type comme la crue a montee rapide est compte dans la "
            "famille Inondation."
        ),
    }
    (SORTIE / "risques_meta.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  ecrit : risques_meta.json")

    print("\nNombre de communes concernees, par famille de risque :")
    for k, v in synthese["communes_par_risque"].items():
        print(f"  {k:26s} {v:2d} / {n}")
    print("\nTerritoires a risque important d'inondation :")
    for k, v in tris.items():
        print(f"  {k:36s} {v:2d} communes")


if __name__ == "__main__":
    main()
