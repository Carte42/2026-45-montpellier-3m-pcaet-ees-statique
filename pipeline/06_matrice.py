"""06 — Matrice d'incidences, exports tableur et Shapefile.

Produit :
  public/data/matrice.json       la matrice renseignée, pour le volet 2
  public/data/matrice.csv        la même, reprenable dans un tableur
  public/data/flux.csv           les flux de couverture mesurés
  public/data/territoire.csv     les indicateurs communaux, sans géométrie
  public/data/territoire_shp.zip la couche communale au format Shapefile

La matrice croise les trois enjeux traités avec les leviers de compétence que
la Métropole exerce, tels que son cahier des charges les énumère : habitat et
logement, mobilités et transports, urbanisme et aménagement, développement
économique, réseaux énergétiques, ressource en eau, déchets, préservation des
ressources et de l'espace.

Chaque croisement renseigné est qualifié selon les cinq attributs employés en
phase 2 et porte sa justification. Les croisements sans incidence notable ne
sont pas forcés : une matrice d'évaluation réelle comporte des cases vides, et
les remplir toutes serait un artefact.

C'est une démonstration d'instrument sur un plan public. Elle n'engage pas la
Métropole et ne constitue pas une évaluation environnementale.

Usage :
    python 06_matrice.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent
DATA = RACINE.parent / "public" / "data"

ENJEUX = {
    "artificialisation": "Artificialisation et occupation du sol",
    "chaleur": "Climat — adaptation aux vagues de chaleur",
    "risques": "Risques naturels",
}

LEVIERS = [
    "Habitat et logement",
    "Mobilités et transports",
    "Urbanisme et aménagement",
    "Développement économique",
    "Réseaux énergétiques",
    "Ressource en eau et GEMAPI",
    "Gestion des déchets",
    "Préservation des ressources et de l'espace",
]

# Attributs : sens, voie, durée, horizon, intensité de 1 à 4.
# Seuls les croisements présentant une incidence notable sont renseignés.
CELLULES = [
    # ── Artificialisation ────────────────────────────────────────────────────
    ("artificialisation", "Habitat et logement", "négatif", "direct", "permanent", "2030", 3,
     "La production de logements sur un territoire qui gagne des habitants est le premier moteur de consommation d'espace. Mesuré : solde net de 78,3 ha sur 2021-2024."),
    ("artificialisation", "Mobilités et transports", "négatif", "direct", "permanent", "2040", 2,
     "Les infrastructures et leurs emprises annexes artificialisent durablement. Le flux mesuré « sols nus naturels vers zones imperméables » domine les transferts."),
    ("artificialisation", "Urbanisme et aménagement", "positif", "direct", "permanent", "2030", 3,
     "C'est le levier qui peut infléchir la trajectoire, par les règles d'urbanisme et la mobilisation du foncier déjà artificialisé. La désartificialisation mesurée, 66,1 ha sur 2021-2024, montre que le levier opère déjà."),
    ("artificialisation", "Développement économique", "négatif", "direct", "permanent", "2040", 2,
     "Les zones d'activité consomment des surfaces importantes par emploi créé."),
    ("artificialisation", "Préservation des ressources et de l'espace", "positif", "direct", "permanent", "2050", 3,
     "Levier direct de l'objectif de sobriété foncière, à l'échelle où l'évaluation le mesure."),
    # ── Climat, adaptation aux vagues de chaleur ─────────────────────────────
    ("chaleur", "Habitat et logement", "positif", "indirect", "permanent", "2040", 2,
     "La rénovation du bâti réduit l'inconfort d'été, sans agir sur l'îlot de chaleur extérieur."),
    ("chaleur", "Urbanisme et aménagement", "positif", "direct", "permanent", "2040", 3,
     "La place du végétal et la désimperméabilisation agissent directement sur la température ressentie. Mesuré : indice de végétation de 0,429 en moyenne, et 26,1 % de surface à végétation faible sur la commune-centre."),
    ("chaleur", "Mobilités et transports", "positif", "indirect", "permanent", "2040", 2,
     "La réduction des surfaces de voirie et de stationnement libère de l'emprise mobilisable pour le végétal."),
    ("chaleur", "Ressource en eau et GEMAPI", "négatif", "indirect", "temporaire", "2030", 2,
     "L'arrosage nécessaire au maintien du couvert végétal en période de canicule entre en tension avec la ressource, dans un territoire que le cahier des charges signale déjà sous tension. Point de vigilance sur la maladaptation."),
    ("chaleur", "Préservation des ressources et de l'espace", "positif", "direct", "permanent", "2050", 3,
     "La préservation des espaces naturels périurbains maintient les apports de fraîcheur vers le tissu urbain."),
    # ── Risques naturels ─────────────────────────────────────────────────────
    ("risques", "Urbanisme et aménagement", "positif", "direct", "permanent", "2030", 3,
     "Maîtrise de l'exposition par les règles de constructibilité. Mesuré : 19 des 31 communes relèvent du territoire à risque important d'inondation Montpellier-Lunel-Mauguio."),
    ("risques", "Ressource en eau et GEMAPI", "positif", "direct", "permanent", "2040", 3,
     "Compétence directe sur la prévention des inondations, qui concerne 22 communes sur 31."),
    ("risques", "Habitat et logement", "négatif", "indirect", "permanent", "2040", 2,
     "La densification en zone déjà exposée augmente le nombre de personnes exposées à aléa constant."),
    ("risques", "Préservation des ressources et de l'espace", "positif", "indirect", "permanent", "2050", 2,
     "Le maintien des espaces ouverts entretient les capacités d'expansion des crues et limite l'aléa de retrait-gonflement des argiles."),
]


def main() -> None:
    print("06 — Matrice d'incidences et exports")
    print("=" * 70)

    # ── Matrice ──────────────────────────────────────────────────────────────
    cellules = [
        {
            "enjeu": ENJEUX[e], "enjeu_cle": e, "levier": lv,
            "sens": sens, "voie": voie, "duree": duree,
            "horizon": horizon, "intensite": inten, "justification": just,
        }
        for e, lv, sens, voie, duree, horizon, inten, just in CELLULES
    ]
    matrice = {
        "titre": "Matrice d'incidences — démonstration d'instrument",
        "objet_evalue": "Leviers de compétence exercés par Montpellier Méditerranée Métropole, tels que son cahier des charges les énumère",
        "enjeux": list(ENJEUX.values()),
        "leviers": LEVIERS,
        "echelle_intensite": {
            "1": "incidence faible",
            "2": "incidence modérée",
            "3": "incidence notable",
            "4": "incidence majeure",
        },
        "attributs": ["sens", "voie", "duree", "horizon", "intensite"],
        "cellules": cellules,
        "note": (
            "Les croisements sans incidence notable identifiée ne sont pas renseignés : "
            "une matrice d'évaluation réelle comporte des cases vides. Démonstration "
            "d'instrument appliquée à un plan public ; n'engage pas la Métropole et ne "
            "constitue pas une évaluation environnementale."
        ),
    }
    (DATA / "matrice.json").write_text(
        json.dumps(matrice, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  matrice.json : {len(cellules)} croisements renseignés sur "
          f"{len(ENJEUX) * len(LEVIERS)} possibles")

    def ecrire_csv(nom: str, entetes: list[str], lignes: list[list]) -> None:
        tampon = io.StringIO()
        w = csv.writer(tampon, delimiter=";", lineterminator="\n")
        w.writerow(entetes)
        w.writerows(lignes)
        # Signature d'octets, pour que le tableur ouvre l'accentuation sans réglage.
        (DATA / nom).write_text("﻿" + tampon.getvalue(), encoding="utf-8")
        print(f"  {nom} : {len(lignes)} lignes")

    ecrire_csv(
        "matrice.csv",
        ["Enjeu", "Levier de compétence", "Sens", "Voie", "Durée", "Horizon",
         "Intensité (1 à 4)", "Justification"],
        [[c["enjeu"], c["levier"], c["sens"], c["voie"], c["duree"],
          c["horizon"], c["intensite"], c["justification"]] for c in cellules],
    )

    # ── Flux ─────────────────────────────────────────────────────────────────
    flux = json.loads((DATA / "artificialisation_flux.json").read_text(encoding="utf-8"))
    ecrire_csv(
        "flux.csv",
        ["Période", "Couverture avant", "Couverture après", "Surface (ha)"],
        [[f["periode"], f["depuis"], f["vers"], f["surface_ha"]] for f in flux],
    )

    # ── Indicateurs communaux ────────────────────────────────────────────────
    territoire = gpd.read_file(DATA / "territoire.geojson")
    colonnes = [c for c in territoire.columns if c != "geometry"]
    # Une valeur absente s'écrit comme une cellule vide : « nan » dans un export
    # tabulaire est une fuite de l'outil de calcul, pas une donnée.
    ecrire_csv(
        "territoire.csv",
        colonnes,
        territoire[colonnes].where(territoire[colonnes].notna(), "").values.tolist(),
    )

    # ── Shapefile ────────────────────────────────────────────────────────────
    # Le cahier des charges retient « Shapefile ou GeoJSON » : les deux sont
    # fournis. Le Shapefile tronque les noms de champs à dix caractères, d'où
    # la table de correspondance jointe à l'archive.
    dossier = DATA / "_shp"
    dossier.mkdir(exist_ok=True)

    def raccourcir(noms: list[str]) -> dict[str, str]:
        """Noms uniques de dix caractères au plus, suffixés en cas de collision."""
        pris: set[str] = set()
        table: dict[str, str] = {}
        for n in noms:
            base = n[:10]
            candidat, i = base, 1
            while candidat in pris:
                suffixe = str(i)
                candidat = base[: 10 - len(suffixe)] + suffixe
                i += 1
            pris.add(candidat)
            table[n] = candidat
        return table

    court = raccourcir(colonnes)
    shp = territoire.rename(columns=court)
    shp.to_file(dossier / "territoire.shp", driver="ESRI Shapefile", encoding="utf-8")
    (dossier / "champs.csv").write_text(
        "﻿" + "Nom complet;Nom tronqué\n"
        + "\n".join(f"{k};{v}" for k, v in court.items()),
        encoding="utf-8",
    )
    archive = DATA / "territoire_shp.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(dossier.iterdir()):
            z.write(f, f.name)
    for f in dossier.iterdir():
        f.unlink()
    dossier.rmdir()
    print(f"  territoire_shp.zip : {archive.stat().st_size // 1024} Ko")

    print("\nExports disponibles dans le démonstrateur :")
    for f in sorted(DATA.glob("*")):
        if f.suffix in (".csv", ".zip", ".geojson", ".json"):
            print(f"  {f.name:34s} {f.stat().st_size // 1024:5d} Ko")


if __name__ == "__main__":
    main()
