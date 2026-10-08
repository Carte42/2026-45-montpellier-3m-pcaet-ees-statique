"""08 — Planches imprimables des trois volets.

Produit `public/planches/planches_demonstrateur.pdf` : cinq planches A4 à
l'italienne, destinées à être jointes au pli, puisqu'un contenu accessible par
une adresse extérieure n'est pas juridiquement une pièce remise.

  1  Artificialisation nette par commune, 2021-2024
  2  Climat — vulnérabilité aux vagues de chaleur
  3  Risques naturels recensés par commune
  4  Matrice d'incidences appliquée
  5  Fiche d'indicateur et sources

Parti pris : sobriété. Fond clair pour l'impression, une seule sémiologie par
planche, la grille de notation et les sources visibles sur chaque page. Pas de
dégradé, pas d'effet.

Usage :
    python 08_planches.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.colors import ListedColormap, BoundaryNorm  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent
DATA = RACINE.parent / "public" / "data"
SORTIE = RACINE.parent / "public" / "planches"

A4_PAYSAGE = (11.69, 8.27)

def fr(x: float, d: int = 1) -> str:
    """Nombre au format francais : virgule decimale, espace de milliers,
    signe moins typographique."""
    t = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return t.replace("-", "−")


ENCRE = "#141413"
GRIS = "#6b7280"
TRAIT = "#c8ccd4"
ACCENT = "#1d4e79"

PALETTES = {
    "ocre": ["#f3ead6", "#e3c98d", "#d2a84a", "#b4852c", "#8a6418"],
    "vert": ["#e4efe8", "#b4d8c6", "#7cbda1", "#4a9b7c", "#2b7055"],
    "bleu": ["#e3ecf5", "#b9d1e8", "#8ab2d6", "#5a8fbe", "#33679b"],
}

PLANCHES = [
    ("net_2021-2024_ha", "ocre",
     "Artificialisation nette par commune",
     "Solde des surfaces artificialisées et désartificialisées, 2021-2024",
     "hectares",
     "Couches d'évolution de l'occupation du sol à grande échelle, Institut national "
     "de l'information géographique et forestière — millésimes 2018-2021 et 2021-2024",
     {"Sensibilité du milieu": 2, "Niveau de pression": 3, "Marge d'action du plan": 3}),
    ("vulnerabilite_chaleur", "vert",
     "Climat — vulnérabilité aux vagues de chaleur",
     "Croisement du rang de faible végétation et du rang de densité de population",
     "indice sur 100",
     "Sentinel-2 niveau 2A, programme Copernicus — scène du 6 août 2026, "
     "0,003 % de couverture nuageuse, calcul à 20 m",
     {"Sensibilité du milieu": 3, "Niveau de pression": 3, "Marge d'action du plan": 2}),
    ("nb_risques", "bleu",
     "Risques naturels recensés par commune",
     "Familles de risques de l'inventaire GASPAR, agrégées au niveau parent",
     "familles",
     "Géorisques, ministère de la Transition écologique — interrogation du 8 octobre 2026",
     {"Sensibilité du milieu": 3, "Niveau de pression": 2, "Marge d'action du plan": 1}),
]


def couper(texte: str, largeur: int) -> list[str]:
    """Repliement simple sur la largeur donnee, en mots entiers."""
    mots, lignes, courante = texte.split(), [], ""
    for mot in mots:
        essai = (courante + " " + mot).strip()
        if len(essai) <= largeur:
            courante = essai
        else:
            lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


def cartouche(fig, titre: str, sous_titre: str) -> None:
    """Bandeau d'identification, identique sur toutes les planches."""
    fig.text(0.045, 0.955, "M6C0007TE · Lot 1 · Carte 42", color=GRIS,
             fontsize=7.5, family="monospace")
    fig.text(0.045, 0.905, titre, color=ENCRE, fontsize=17, weight="bold")
    fig.text(0.045, 0.868, sous_titre, color=GRIS, fontsize=9.5)
    fig.add_artist(plt.Line2D([0.045, 0.955], [0.845, 0.845], color=TRAIT, lw=0.8))


def pied(fig, source: str, numero: int, total: int) -> None:
    fig.add_artist(plt.Line2D([0.045, 0.955], [0.075, 0.075], color=TRAIT, lw=0.8))
    fig.text(0.045, 0.048, "Source : " + source, color=GRIS, fontsize=7, wrap=True)
    fig.text(0.045, 0.022,
             "Démonstration de méthode établie à partir de données ouvertes exclusivement. "
             "Ne constitue pas une évaluation environnementale et n'engage pas "
             "Montpellier Méditerranée Métropole.",
             color=GRIS, fontsize=6.5)
    fig.text(0.955, 0.022, f"{numero} / {total}", color=GRIS, fontsize=7.5,
             ha="right", family="monospace")


def planche_carte(pdf, gdf, champ, palette, titre, sous_titre, unite, source,
                  notes, numero, total) -> None:
    fig = plt.figure(figsize=A4_PAYSAGE)
    fig.patch.set_facecolor("white")
    cartouche(fig, titre, sous_titre)
    pied(fig, source, numero, total)

    ax = fig.add_axes([0.045, 0.11, 0.60, 0.72])
    valeurs = gdf[champ].astype(float)
    vmin, vmax = valeurs.min(), valeurs.max()
    bornes = [vmin + (vmax - vmin) * i / 5 for i in range(6)]
    cmap = ListedColormap(PALETTES[palette])
    gdf.plot(column=champ, ax=ax, cmap=cmap, norm=BoundaryNorm(bornes, cmap.N),
             edgecolor="white", linewidth=0.5)
    ax.set_axis_off()

    # Nom des cinq communes aux valeurs les plus élevées.
    for _, r in gdf.nlargest(5, champ).iterrows():
        c = r.geometry.representative_point()
        ax.annotate(r["nom"], (c.x, c.y), fontsize=6.5, color=ENCRE,
                    ha="center", va="center")

    # ── Colonne de droite : échelle et grille de hiérarchisation ────────────
    x0 = 0.68
    fig.text(x0, 0.80, "ÉCHELLE", color=GRIS, fontsize=7.5)
    for i, c in enumerate(PALETTES[palette]):
        fig.add_artist(Rectangle((x0 + i * 0.047, 0.755), 0.045, 0.022,
                                 facecolor=c, edgecolor="white", lw=0.6,
                                 transform=fig.transFigure))
    fig.text(x0, 0.728, fr(bornes[0]), color=GRIS, fontsize=7.5)
    fig.text(x0 + 0.235, 0.728, f"{fr(bornes[-1])} {unite}",
             color=GRIS, fontsize=7.5, ha="right")
    fig.text(x0, 0.702, "5 classes, bornes égales", color=GRIS, fontsize=7)

    fig.text(x0, 0.645, "HIÉRARCHISATION DE L'ENJEU", color=GRIS, fontsize=7.5)
    y = 0.605
    for libelle, note in notes.items():
        fig.text(x0, y, libelle, color=ENCRE, fontsize=8.5)
        fig.text(x0 + 0.235, y, str(note), color=ACCENT, fontsize=9,
                 ha="right", family="monospace", weight="bold")
        y -= 0.033
    fig.add_artist(plt.Line2D([x0, x0 + 0.235], [y + 0.012, y + 0.012], color=TRAIT, lw=0.8))
    fig.text(x0, y - 0.022, "Niveau d'enjeu retenu", color=ENCRE, fontsize=8.5, weight="bold")
    fig.text(x0 + 0.235, y - 0.022, f"{sum(notes.values())} / 9", color=ACCENT,
             fontsize=9, ha="right", family="monospace", weight="bold")

    fig.text(x0, y - 0.085,
             "La note figure à côté de son résultat :\nle classement est vérifiable, "
             "non pas seulement\nconstaté.", color=GRIS, fontsize=7.5, va="top")

    # Cinq premières communes
    fig.text(x0, y - 0.175, "CINQ PREMIÈRES COMMUNES", color=GRIS, fontsize=7.5)
    yy = y - 0.212
    for _, r in gdf.nlargest(5, champ).iterrows():
        fig.text(x0, yy, r["nom"], color=ENCRE, fontsize=8)
        fig.text(x0 + 0.235, yy, fr(r[champ]), color=ENCRE,
                 fontsize=8, ha="right", family="monospace")
        yy -= 0.028

    pdf.savefig(fig)
    plt.close(fig)
    print(f"  planche {numero} : {titre}")


def planche_matrice(pdf, matrice, numero, total) -> None:
    fig = plt.figure(figsize=A4_PAYSAGE)
    fig.patch.set_facecolor("white")
    cartouche(fig, "Matrice d'incidences appliquée",
              f"{len(matrice['cellules'])} croisements renseignés sur "
              f"{len(matrice['enjeux']) * len(matrice['leviers'])} — les croisements sans "
              "incidence notable ne sont pas forcés")
    pied(fig, matrice["objet_evalue"], numero, total)

    entetes = ["Levier de compétence", "Enjeu", "Sens", "Voie", "Durée", "Horizon", "Int."]
    largeurs = [0.255, 0.155, 0.060, 0.075, 0.085, 0.070, 0.045]
    # Les intitules complets debordent de la colonne : on abrege a l'affichage,
    # l'export en tableur portant les libelles entiers.
    COURT = {
        "Artificialisation et occupation du sol": "Artificialisation",
        "Climat — adaptation aux vagues de chaleur": "Climat",
        "Risques naturels": "Risques naturels",
        "Préservation des ressources et de l'espace": "Préservation des ressources",
        "Ressource en eau et GEMAPI": "Ressource en eau, GEMAPI",
    }
    x = 0.045
    for e, w in zip(entetes, largeurs):
        fig.text(x, 0.805, e.upper(), color=GRIS, fontsize=7)
        x += w
    fig.add_artist(plt.Line2D([0.045, 0.785], [0.792, 0.792], color=TRAIT, lw=0.8))

    y = 0.762
    for c in matrice["cellules"]:
        x = 0.045
        vals = [c["levier"], c["enjeu"].split(" —")[0],
                "+" if c["sens"] == "positif" else "−",
                c["voie"], c["duree"], c["horizon"], str(c["intensite"])]
        for v, w in zip(vals, largeurs):
            couleur = ENCRE
            if v == "+":
                couleur = "#2b7055"
            elif v == "−":
                couleur = "#b4852c"
            fig.text(x, y, v, color=couleur, fontsize=7.8,
                     weight="bold" if v in ("+", "−") else "normal")
            x += w
        y -= 0.0315

    fig.text(0.80, 0.762, "ÉCHELLE D'INTENSITÉ", color=GRIS, fontsize=7.5)
    yy = 0.728
    for k, v in matrice["echelle_intensite"].items():
        fig.text(0.80, yy, f"{k}  {v}", color=ENCRE, fontsize=8)
        yy -= 0.028
    fig.text(0.80, yy - 0.025,
             "L'échelle est publiée\navant tout résultat.\n\nLes justifications de\nchaque croisement\n"
             "figurent dans l'export\nen tableur.", color=GRIS, fontsize=7.5, va="top")

    pdf.savefig(fig)
    plt.close(fig)
    print(f"  planche {numero} : matrice d'incidences")


def planche_indicateur(pdf, synthese, metas, numero, total) -> None:
    fig = plt.figure(figsize=A4_PAYSAGE)
    fig.patch.set_facecolor("white")
    cartouche(fig, "Fiche d'indicateur et sources",
              "Artificialisation nette annuelle — la brique élémentaire du tableau "
              "des indicateurs de suivi renseignés pour l'état initial")
    pied(fig, "Ensemble des sources documentées dans le volet « sources et méthode » "
              "du démonstrateur", numero, total)

    art = synthese["artificialisation"]
    lignes = [
        ("Définition", "Solde des surfaces artificialisées et désartificialisées, rapporté à l'année"),
        ("Unité", "hectare par an"),
        ("Valeur 2018-2021", f"{fr(art['periodes'][0]['solde_ha'] / 3)} ha/an"),
        ("Valeur 2021-2024", f"{fr(art['periodes'][1]['solde_ha'] / 3)} ha/an"),
        ("Tendance", f"{fr(art['evolution_du_rythme_pct'])} %"),
        ("Source", "Couches d'évolution de l'occupation du sol à grande échelle, Institut national de l'information géographique et forestière"),
        ("Porteur pressenti", "Direction de l'urbanisme et de l'aménagement"),
        ("Pas de temps", "triennal, au rythme des millésimes"),
        ("Seuil d'alerte", "retour au rythme de la période précédente"),
        ("Reproductible", "oui — chaîne de traitement livrée avec la valeur"),
    ]
    y = 0.775
    for k, v in lignes:
        fig.text(0.045, y, k.upper(), color=GRIS, fontsize=7)
        morceaux = couper(v, 58)
        gras = "bold" if k.startswith("Valeur") or k == "Tendance" else "normal"
        for i, morceau in enumerate(morceaux):
            fig.text(0.205, y - i * 0.026, morceau, color=ENCRE, fontsize=9, weight=gras)
        y -= 0.042 + (len(morceaux) - 1) * 0.026
        fig.add_artist(plt.Line2D([0.045, 0.56], [y + 0.026, y + 0.026], color=TRAIT, lw=0.5))

    fig.text(0.62, 0.775, "SOURCES EMPLOYÉES", color=GRIS, fontsize=7.5)
    yy = 0.738
    for m in metas:
        for i, morceau in enumerate(couper(m["produit"], 46)):
            fig.text(0.62 if i == 0 else 0.632, yy - i * 0.021,
                     ("· " if i == 0 else "") + morceau, color=ENCRE, fontsize=8)
        yy -= 0.021 * len(couper(m["produit"], 46)) + 0.004
        for i, morceau in enumerate(couper(m.get("producteur", ""), 50)):
            fig.text(0.632, yy - i * 0.019, morceau, color=GRIS, fontsize=7)
        yy -= 0.019 * len(couper(m.get("producteur", ""), 50)) + 0.016

    fig.text(0.62, yy - 0.02,
             "Chaque source est documentée dans le\ndémonstrateur avec son millésime ou sa\n"
             "date d'interrogation, sa licence, sa\nrésolution de calcul et ses réserves\nde lecture.",
             color=GRIS, fontsize=7.5, va="top")

    fig.text(0.045, 0.165,
             "Toutes les données et les chaînes de traitement sont téléchargeables depuis "
             "l'interface : couche communale en GeoJSON et en Shapefile,\nindicateurs communaux, "
             "matrice d'incidences et flux de couverture en tableur, chiffres de synthèse.",
             color=ENCRE, fontsize=8, va="top")

    pdf.savefig(fig)
    plt.close(fig)
    print(f"  planche {numero} : fiche d'indicateur")


def main() -> None:
    print("08 — Planches imprimables")
    print("=" * 70)
    SORTIE.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(DATA / "territoire.geojson").to_crs("EPSG:2154")
    synthese = json.loads((DATA / "synthese.json").read_text(encoding="utf-8"))
    matrice = json.loads((DATA / "matrice.json").read_text(encoding="utf-8"))
    metas = [json.loads((DATA / f"{n}_meta.json").read_text(encoding="utf-8"))
             for n in ("perimetre", "artificialisation", "vegetation", "risques", "fonddeplan")]

    cible = SORTIE / "planches_demonstrateur.pdf"
    total = len(PLANCHES) + 2
    with PdfPages(cible) as pdf:
        for i, (champ, pal, titre, st, unite, src, notes) in enumerate(PLANCHES, 1):
            planche_carte(pdf, gdf, champ, pal, titre, st, unite, src, notes, i, total)
        planche_matrice(pdf, matrice, len(PLANCHES) + 1, total)
        planche_indicateur(pdf, synthese, metas, total, total)
        d = pdf.infodict()
        d["Title"] = "Démonstrateur — évaluation environnementale stratégique du PCAET de Montpellier Méditerranée Métropole"
        d["Author"] = "Carte 42"
        d["Subject"] = "Consultation M6C0007TE, lot 1 — annexe B1 du mémoire technique"

    print(f"\n  écrit : {cible.relative_to(RACINE.parent)} "
          f"({cible.stat().st_size // 1024} Ko, {total} planches)")


if __name__ == "__main__":
    main()
