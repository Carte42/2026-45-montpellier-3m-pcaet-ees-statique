"""Habillage cartographique des planches : fond de plan, habillage, étiquettes.

Une carte jointe à une offre doit porter ce que porte une carte publiée : un
fond de plan qui situe le territoire, une échelle graphique, une orientation,
une bordure cotée en coordonnées, et le nom de chaque commune représentée.

Tout est calculé en **RGF93 / Lambert-93 (EPSG:2154)**, la projection légale
pour la France métropolitaine. Le fond de plan est demandé au service de carte
en ligne de la Géoplateforme directement dans cette projection, ce qui évite
toute reprojection d'image : un pixel du fond correspond exactement au terrain
que la couche communale recouvre.

Usage : importé par `08_planches.py`.
"""
from __future__ import annotations

import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import requests
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = Path(__file__).resolve().parent / "sources" / "fond_plan_ign"
WMS = "https://data.geopf.fr/wms-r/wms"
COUCHE = "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2"
# Le service refuse les requêtes sans agent identifiable.
AGENT = {"User-Agent": "Carte42/1.0 (+https://carte42.fr ; contact@carte42.fr)"}

ENCRE = "#141413"
GRIS = "#6b7280"
TRAIT = "#c8ccd4"


# ── Emprise ──────────────────────────────────────────────────────────────────

def emprise(gdf, rapport: float, marge: float = 0.045) -> tuple[float, float, float, float]:
    """Emprise au rapport largeur/hauteur demandé, centrée sur le territoire.

    L'emprise est étirée sur l'axe le plus court plutôt que l'image déformée :
    la carte garde ses proportions réelles et le cadre reste plein.
    """
    minx, miny, maxx, maxy = gdf.total_bounds
    dx, dy = maxx - minx, maxy - miny
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    dx *= 1 + 2 * marge
    dy *= 1 + 2 * marge
    if dx / dy < rapport:
        dx = dy * rapport
    else:
        dy = dx / rapport
    return cx - dx / 2, cy - dy / 2, cx + dx / 2, cy + dy / 2


# ── Fond de plan ─────────────────────────────────────────────────────────────

def fond_de_plan(bbox, largeur_px: int = 2600, eclaircir: float = 0.62):
    """Image du plan IGN pour l'emprise donnée, en Lambert-93.

    Le fond est désaturé et éclairci : il situe le territoire sans concurrencer
    la donnée thématique qui se superpose. Le résultat est mis en cache sur
    disque, de sorte qu'une regénération des planches ne réinterroge pas le
    service.
    """
    minx, miny, maxx, maxy = bbox
    hauteur_px = max(1, round(largeur_px * (maxy - miny) / (maxx - minx)))
    cle = hashlib.sha1(
        f"{COUCHE}|{minx:.1f}|{miny:.1f}|{maxx:.1f}|{maxy:.1f}|{largeur_px}|{eclaircir}"
        .encode()).hexdigest()[:16]
    CACHE.mkdir(parents=True, exist_ok=True)
    fichier = CACHE / f"{cle}.png"

    if fichier.exists():
        image = Image.open(fichier)
    else:
        parametres = {
            "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
            "LAYERS": COUCHE, "STYLES": "", "CRS": "EPSG:2154",
            "BBOX": f"{minx},{miny},{maxx},{maxy}",
            "WIDTH": largeur_px, "HEIGHT": hauteur_px, "FORMAT": "image/png",
        }
        reponse = requests.get(WMS, params=parametres, timeout=120, headers=AGENT)
        reponse.raise_for_status()
        if not reponse.headers.get("content-type", "").startswith("image"):
            raise RuntimeError(f"le service de carte a répondu : {reponse.text[:300]}")
        brute = Image.open(io.BytesIO(reponse.content)).convert("L")
        tableau = np.asarray(brute).astype(float)
        # Éclaircissement : on réduit le contraste vers le blanc.
        tableau = 255 - (255 - tableau) * eclaircir
        image = Image.fromarray(tableau.astype("uint8")).convert("RGB")
        image.save(fichier)
        print(f"    fond de plan : {largeur_px}×{hauteur_px} px, {fichier.name}")

    return np.asarray(image)


# ── Habillage ────────────────────────────────────────────────────────────────

def _pas_rond(etendue: float, cibles: int = 6) -> float:
    """Pas de graduation « rond » donnant environ `cibles` graduations."""
    brut = etendue / cibles
    exposant = 10 ** np.floor(np.log10(brut))
    for facteur in (1, 2, 2.5, 5, 10):
        if facteur * exposant >= brut:
            return facteur * exposant
    return 10 * exposant


def bordure_cotee(ax, taille: float = 6.5) -> None:
    """Cadre de la carte et graduations en coordonnées Lambert-93, en kilomètres.

    Les graduations sont portées sur les quatre côtés, les valeurs sur le bas et
    la gauche : c'est la convention des cartes d'étude, et elle permet de relire
    une position sans sortir du cadre.
    """
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    pas = _pas_rond(max(x1 - x0, y1 - y0))

    ax.set_xticks(np.arange(np.ceil(x0 / pas) * pas, x1, pas))
    ax.set_yticks(np.arange(np.ceil(y0 / pas) * pas, y1, pas))
    ax.set_xticklabels([f"{v / 1000:,.0f}".replace(",", " ") for v in ax.get_xticks()])
    ax.set_yticklabels([f"{v / 1000:,.0f}".replace(",", " ") for v in ax.get_yticks()])
    ax.tick_params(axis="both", which="major", direction="out", length=3.2, width=0.7,
                   color=ENCRE, labelsize=taille, labelcolor=GRIS, pad=2,
                   top=True, right=True, labeltop=False, labelright=False)
    for cote in ax.spines.values():
        cote.set_linewidth(0.9)
        cote.set_edgecolor(ENCRE)
    ax.set_xlabel("Coordonnées RGF93 / Lambert-93, en kilomètres",
                  color=GRIS, fontsize=taille, labelpad=3)


def fleche_nord(ax, x: float = 0.955, y: float = 0.955, taille: float = 0.052) -> None:
    """Flèche d'orientation, en coordonnées relatives à la carte.

    En Lambert-93 le nord de la projection et le nord géographique ne coïncident
    exactement que sur le méridien central ; l'écart est ici inférieur au degré
    et la flèche est portée verticale, comme sur toute carte d'étude.
    """
    h = taille
    ax.add_patch(Polygon(
        [(x, y), (x - h * 0.30, y - h), (x, y - h * 0.72), (x + h * 0.30, y - h)],
        closed=True, facecolor=ENCRE, edgecolor=ENCRE, lw=0.5,
        transform=ax.transAxes, zorder=6))
    ax.text(x, y + 0.012, "N", transform=ax.transAxes, ha="center", va="bottom",
            fontsize=8, weight="bold", color=ENCRE, zorder=6)


def echelle_graphique(ax, x: float = 0.035, y: float = 0.045, cible: float = 0.24) -> None:
    """Échelle graphique à segments alternés, longueur ronde en kilomètres."""
    x0, x1 = ax.get_xlim()
    largeur_m = (x1 - x0) * cible
    longueur = min((v for v in (500, 1000, 2000, 5000, 10000, 20000, 50000)
                    if v >= largeur_m * 0.6), default=50000)
    part = longueur / (x1 - x0)
    hauteur = 0.011

    for i in range(4):
        ax.add_patch(Rectangle(
            (x + i * part / 4, y), part / 4, hauteur,
            facecolor=ENCRE if i % 2 == 0 else "white",
            edgecolor=ENCRE, lw=0.6, transform=ax.transAxes, zorder=6))
    for i, part_i in enumerate((0, 0.5, 1)):
        valeur = longueur * part_i
        texte = f"{valeur / 1000:,.1f}".replace(",", " ").replace(".", ",").rstrip("0").rstrip(",")
        ax.text(x + part * part_i, y + hauteur + 0.006, texte or "0",
                transform=ax.transAxes, ha="center", va="bottom",
                fontsize=6.2, color=ENCRE, zorder=6)
    ax.text(x + part + 0.012, y + hauteur + 0.006, "km", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=6.2, color=GRIS, zorder=6)


def cadre_blanc(ax, x, y, largeur, hauteur, alpha: float = 0.82) -> None:
    """Fond clair sous un élément d'habillage, pour le détacher de la carte."""
    ax.add_patch(Rectangle((x, y), largeur, hauteur, facecolor="white", alpha=alpha,
                           edgecolor="none", transform=ax.transAxes, zorder=5))


# ── Étiquettes des communes ──────────────────────────────────────────────────

def etiquettes_communes(ax, gdf, champ: str = "nom", taille: float = 5.3,
                        largeur_pouces: float = 7.0) -> int:
    """Nomme chaque commune, en écartant les étiquettes qui se recouvrent.

    L'encombrement d'une étiquette est estimé en coordonnées terrain à partir de
    la largeur de la carte en pouces ; les étiquettes sont posées de la plus
    grande commune à la plus petite, chacune cherchant la première position
    libre autour de son point d'ancrage. Celle qui a dû s'écarter porte un trait
    de rappel vers sa commune.
    """
    from matplotlib import patheffects

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    # Unités terrain par point typographique.
    u_pt = (x1 - x0) / (largeur_pouces * 72)
    halo = [patheffects.withStroke(linewidth=1.8, foreground="white")]

    ancres = []
    for _, r in gdf.assign(_a=gdf.geometry.area).sort_values("_a", ascending=False).iterrows():
        p = r.geometry.representative_point()
        nom = str(r[champ])
        demi_l = len(nom) * taille * 0.50 * u_pt / 2
        demi_h = taille * 1.05 * u_pt / 2
        ancres.append((nom, p.x, p.y, demi_l, demi_h))

    def chevauche(boite, posees) -> bool:
        ax0, ay0, ax1, ay1 = boite
        for bx0, by0, bx1, by1 in posees:
            if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                return True
        return False

    posees: list[tuple[float, float, float, float]] = []
    ecartees = 0
    for nom, px, py, dl, dh in ancres:
        meilleure = None
        for rayon in (0, 1, 1.6, 2.4, 3.4, 4.6, 6.0):
            if meilleure:
                break
            pas = dh * 2.6 * rayon
            directions = [(0, 0)] if rayon == 0 else [
                (0, 1), (0, -1), (1, 0), (-1, 0),
                (0.75, 0.75), (-0.75, 0.75), (0.75, -0.75), (-0.75, -0.75)]
            for ux, uy in directions:
                cx, cy = px + ux * pas, py + uy * pas
                boite = (cx - dl, cy - dh, cx + dl, cy + dh)
                if boite[0] < x0 or boite[2] > x1 or boite[1] < y0 or boite[3] > y1:
                    continue
                if not chevauche(boite, posees):
                    meilleure = (cx, cy, boite)
                    break
        if meilleure is None:
            continue  # aucune place : l'étiquette est tue plutôt que superposée
        cx, cy, boite = meilleure
        posees.append(boite)
        if abs(cx - px) > dh or abs(cy - py) > dh * 1.2:
            ecartees += 1
            ax.add_line(Line2D([px, cx], [py, cy], color=GRIS, lw=0.45, zorder=4))
            ax.plot([px], [py], marker="o", markersize=1.1, color=GRIS, zorder=4)
        ax.text(cx, cy, nom, fontsize=taille, color=ENCRE, ha="center", va="center",
                zorder=5, path_effects=halo)
    return len(posees)
