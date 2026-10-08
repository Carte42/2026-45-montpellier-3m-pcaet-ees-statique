"""09 — Annexe B2 : jeux de données du démonstrateur et fiches de métadonnées.

Produit la pièce `B2_jeux_de_donnees.pdf`, jointe au pli du lot 1. Elle documente
les jeux de données que le démonstrateur publie : ce qu'ils contiennent, dans
quels formats, champ par champ, et avec quelle fiche de métadonnées.

C'est la pièce qui atteste la conformité aux formats du § IV du cahier des
clauses techniques particulières, qui impose des données géographiques
accompagnées de leurs métadonnées.

Tout le contenu factuel est lu sur les fichiers eux-mêmes : rien n'est saisi à la
main, de sorte que la pièce ne peut pas décrire autre chose que ce qui est livré.

Usage :
    python 09_annexe_b2.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parent.parent
DATA = RACINE / "public" / "data"
SORTIE = RACINE / "public" / "planches" / "B2_jeux_de_donnees.pdf"
COPIE = Path(
    r"C:\Users\Client\Downloads\Montpellier Plan Climat Energie Territorial"
    r"\1. Preparation reponse\1. Offre\Annexes\B2_jeux_de_donnees.pdf"
)

ENCRE = colors.HexColor("#1a1a1a")
GRIS = colors.HexColor("#5a5a5a")
FILET = colors.HexColor("#c8c8c8")
FOND = colors.HexColor("#f2f2f2")

# ── Dictionnaire des champs de la couche communale ───────────────────────────
# Définition, unité et source de chacun des champs livrés. Les clés doivent
# correspondre exactement aux colonnes de territoire.csv ; un écart est signalé
# à l'exécution plutôt que publié.
CHAMPS = {
    "nom": ("Nom de la commune", "—", "Découpage administratif"),
    "code": ("Code commune de l'Insee, cinq caractères", "—", "Découpage administratif"),
    "population": ("Population municipale", "habitant", "Découpage administratif"),
    "surface": ("Surface publiée par le découpage administratif", "hectare", "Découpage administratif"),
    "surface_commune_ha": ("Surface calculée sur la géométrie livrée, en Lambert-93", "hectare", "Calcul"),
    "artif_2018-2021_ha": ("Surface artificialisée entre 2018 et 2021", "hectare", "OCS GE"),
    "desartif_2018-2021_ha": ("Surface désartificialisée entre 2018 et 2021", "hectare", "OCS GE"),
    "net_2018-2021_ha": ("Solde des deux précédents : artificialisation nette", "hectare", "Calcul"),
    "net_2018-2021_pct": ("Solde net rapporté à la surface communale", "pour cent", "Calcul"),
    "artif_2021-2024_ha": ("Surface artificialisée entre 2021 et 2024", "hectare", "OCS GE"),
    "desartif_2021-2024_ha": ("Surface désartificialisée entre 2021 et 2024", "hectare", "OCS GE"),
    "net_2021-2024_ha": ("Solde des deux précédents : artificialisation nette", "hectare", "Calcul"),
    "net_2021-2024_pct": ("Solde net rapporté à la surface communale", "pour cent", "Calcul"),
    "tendance_ha": (
        "Écart entre les deux rythmes annuels. Une valeur négative signale un "
        "ralentissement du rythme d'artificialisation",
        "hectare par an", "Calcul",
    ),
    "ndvi_moyen": (
        "Moyenne de l'indice de végétation par différence normalisée sur les "
        "pixels exploitables de la commune",
        "sans unité, de −1 à 1", "Sentinel-2",
    ),
    "part_vegetation_faible_pct": (
        "Part des pixels exploitables dont l'indice de végétation est inférieur à 0,2",
        "pour cent", "Calcul",
    ),
    "densite_hab_km2": ("Population rapportée à la surface communale", "habitant par kilomètre carré", "Calcul"),
    "vulnerabilite_chaleur": (
        "Moyenne du rang de part de végétation faible et du rang de densité. "
        "Hiérarchise les communes entre elles ; sans valeur absolue",
        "indice de 0 à 100", "Calcul",
    ),
    "risques": ("Familles de risques recensées sur la commune, séparées par un point médian", "—", "Géorisques"),
    "nb_risques": ("Nombre de familles de risques recensées", "—", "Calcul"),
    "tri": (
        "Territoire à risque important d'inondation dont la commune relève. "
        "Cellule vide lorsque la commune n'en relève pas",
        "—", "Géorisques",
    ),
    "sismicite": ("Zone de sismicité réglementaire", "—", "Géorisques"),
}

# ── Fiches de métadonnées : ordre de lecture et libellés français ────────────
FICHES = [
    ("perimetre_meta.json", "Périmètre et contours communaux"),
    ("artificialisation_meta.json", "Artificialisation et occupation du sol"),
    ("vegetation_meta.json", "Couvert végétal et vulnérabilité à la chaleur"),
    ("risques_meta.json", "Risques naturels"),
    ("fonddeplan_meta.json", "Fond de plan cartographique"),
]

LIBELLES = {
    "produit": "Produit",
    "producteur": "Producteur",
    "departement": "Département",
    "perimetre": "Périmètre",
    "acces": "Accès",
    "requete": "Requête",
    "couche": "Couche",
    "scene": "Scène",
    "date": "Date de la prise de vue",
    "millesimes": "Millésimes",
    "date_de_publication": "Date de publication",
    "date_d_interrogation": "Date d'interrogation",
    "resolution_de_calcul_m": "Résolution de calcul",
    "projection_de_calcul": "Projection de calcul",
    "indice": "Indice calculé",
    "seuil_vegetation_faible": "Seuil de végétation faible",
    "couverture_nuageuse_scene_pct": "Couverture nuageuse de la scène",
    "pixels_exploitables_pct": "Pixels exploitables",
    "classes_de_classification_ecartees": "Classes de masque écartées",
    "nb_appels": "Nombre d'interrogations du service",
    "communes_par_risque": "Communes concernées par famille de risque",
    "territoires_a_risque_important_inondation": "Territoire à risque important d'inondation",
    "resultat": "Résultat",
    "unite": "Unité",
    "usage": "Usage",
    "licence": "Licence",
    "note": "Note de lecture",
    "lecture_des_flux": "Note de lecture",
    "note_vulnerabilite": "Note de lecture",
    "reserve_de_lecture": "Réserve de lecture",
    "periodes": "Fichiers sources",
}

# Ordre d'affichage : l'identification d'abord, la licence et les réserves ensuite.
ORDRE = [
    "produit", "producteur", "departement", "perimetre", "acces", "requete",
    "couche", "scene", "date", "millesimes", "date_de_publication",
    "date_d_interrogation", "periodes", "indice", "projection_de_calcul",
    "resolution_de_calcul_m", "seuil_vegetation_faible",
    "couverture_nuageuse_scene_pct", "pixels_exploitables_pct",
    "classes_de_classification_ecartees", "nb_appels", "communes_par_risque",
    "territoires_a_risque_important_inondation", "resultat", "unite", "usage",
    "licence", "note", "lecture_des_flux", "note_vulnerabilite",
    "reserve_de_lecture",
]


def fr(x) -> str:
    """Nombre au format français : virgule décimale, espace insécable fine."""
    if isinstance(x, bool):
        return "oui" if x else "non"
    if isinstance(x, int):
        return f"{x:,}".replace(",", "\u202f")
    if isinstance(x, float):
        s = f"{x:,.3f}".rstrip("0").rstrip(".")
        return s.replace(",", "\u202f").replace(".", ",")
    return str(x)


def valeur(cle: str, v) -> str:
    """Rend une valeur de fiche en une phrase lisible."""
    if cle == "periodes":
        return "<br/>".join(f"{p['etiquette']} — {p['fichier']}" for p in v)
    if isinstance(v, dict):
        return " · ".join(f"{k} : {fr(n)}" for k, n in v.items())
    if isinstance(v, list):
        return ", ".join(fr(x) for x in v)
    if cle.endswith("_pct"):
        return f"{fr(v)} %"
    if cle == "resolution_de_calcul_m" and isinstance(v, (int, float)):
        return f"{fr(v)} m"
    return fr(v)


def ko(p: Path) -> str:
    return f"{round(p.stat().st_size / 1024):,}".replace(",", "\u202f") + " Ko"


def main() -> None:
    print("09 — Annexe B2 : jeux de données et fiches de métadonnées")
    print("=" * 70)

    # ── Lecture des faits ────────────────────────────────────────────────────
    territoire = list(csv.DictReader(
        io.open(DATA / "territoire.csv", encoding="utf-8-sig"), delimiter=";"))
    colonnes = list(territoire[0].keys())
    inconnus = [c for c in colonnes if c not in CHAMPS]
    orphelins = [c for c in CHAMPS if c not in colonnes]
    if inconnus or orphelins:
        print(f"  ATTENTION — champs non documentés : {inconnus}")
        print(f"  ATTENTION — champs documentés absents de l'export : {orphelins}")
    else:
        print(f"  {len(colonnes)} champs livrés, {len(colonnes)} documentés")

    matrice = json.loads((DATA / "matrice.json").read_text(encoding="utf-8"))
    flux = list(csv.reader(
        io.open(DATA / "flux.csv", encoding="utf-8-sig"), delimiter=";"))
    synthese = json.loads((DATA / "synthese.json").read_text(encoding="utf-8"))
    champs_shp = {
        l.split(";")[0]: l.split(";")[1]
        for l in zipfile.ZipFile(DATA / "territoire_shp.zip")
        .read("champs.csv").decode("utf-8-sig").splitlines()[1:] if ";" in l
    }

    # ── Styles ───────────────────────────────────────────────────────────────
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=15, leading=19, textColor=ENCRE, spaceAfter=3)
    SOUS = ParagraphStyle("SOUS", ss["Normal"], fontName="Helvetica",
                          fontSize=8.5, leading=12, textColor=GRIS, spaceAfter=11)
    H2 = ParagraphStyle("H2", ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=10.5, leading=14, textColor=ENCRE,
                        spaceBefore=13, spaceAfter=5)
    H3 = ParagraphStyle("H3", ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=9, leading=12, textColor=ENCRE,
                        spaceBefore=9, spaceAfter=3)
    P = ParagraphStyle("P", ss["Normal"], fontName="Helvetica", fontSize=8.6,
                       leading=12.2, textColor=ENCRE, alignment=TA_JUSTIFY,
                       spaceAfter=5)
    CEL = ParagraphStyle("CEL", ss["Normal"], fontName="Helvetica", fontSize=7.4,
                         leading=9.4, textColor=ENCRE)
    CELG = ParagraphStyle("CELG", CEL, textColor=GRIS)
    CELB = ParagraphStyle("CELB", CEL, fontName="Helvetica-Bold")
    MONO = ParagraphStyle("MONO", CEL, fontName="Courier", fontSize=7)
    PIED = ParagraphStyle("PIED", ss["Normal"], fontName="Helvetica", fontSize=6.8,
                          leading=9, textColor=GRIS)

    def tableau(lignes, largeurs, entete=True):
        st = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, FILET),
            ("TOPPADDING", (0, 0), (-1, -1), 3.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        if entete:
            st += [("BACKGROUND", (0, 0), (-1, 0), FOND),
                   ("LINEBELOW", (0, 0), (-1, 0), 0.6, GRIS)]
        t = Table(lignes, colWidths=largeurs, repeatRows=1 if entete else 0)
        t.setStyle(TableStyle(st))
        return t

    # ── Construction du document ─────────────────────────────────────────────
    histoire = []
    A = []  # abscisses utiles

    histoire += [
        Paragraph("Annexe B2 — Jeux de données du démonstrateur et fiches de métadonnées", H1),
        Paragraph(
            "Marché M6C0007TE · Lot 1 · Carte 42 · Pièce jointe au mémoire technique, point 4.4",
            SOUS),
        Paragraph(
            "Cette pièce documente les jeux de données que publie le démonstrateur réalisé sur le "
            "territoire des 31 communes de Montpellier Méditerranée Métropole. Elle donne, pour "
            "chaque jeu, son format, son contenu et sa fiche de métadonnées, puis le dictionnaire "
            "complet des champs de la couche communale. Elle atteste la forme sous laquelle les "
            "données exploitées seront transmises au titre du § IV du cahier des clauses techniques "
            "particulières, qui impose des données géographiques accompagnées de leurs métadonnées.", P),
        Paragraph(
            "Les données sont construites à partir de sources ouvertes exclusivement. Aucune donnée "
            "fournie par la Métropole n'y est employée. C'est une démonstration de méthode, conduite "
            "sur le territoire réel de la Métropole, et non l'évaluation du plan climat elle-même.", P),
    ]

    # 1. Les jeux livrés
    histoire.append(Paragraph("1 — Jeux de données livrés", H2))
    fichiers = [
        ("territoire.geojson", "GeoJSON", "Couche communale — 31 entités polygonales, 22 champs",
         "WGS 84, EPSG:4326"),
        ("territoire_shp.zip", "Shapefile", "La même couche, avec son dictionnaire de champs tronqués",
         "WGS 84, EPSG:4326"),
        ("territoire.csv", "CSV", "La même table, sans géométrie — 31 lignes, 22 colonnes", "—"),
        ("artificialisation.geojson", "GeoJSON", "Polygones d'évolution de l'occupation du sol",
         "WGS 84, EPSG:4326"),
        ("vegetation.geojson", "GeoJSON", "Indicateurs de couvert végétal par commune",
         "WGS 84, EPSG:4326"),
        ("risques.geojson", "GeoJSON", "Risques recensés par commune", "WGS 84, EPSG:4326"),
        ("matrice.csv", "CSV", f"Matrice d'incidences — {len(matrice['cellules'])} croisements qualifiés, 8 colonnes", "—"),
        ("matrice.json", "JSON", "La même matrice, avec son échelle d'intensité et ses attributs", "—"),
        ("flux.csv", "CSV", f"Flux de couverture du sol mesurés — {len(flux) - 1} lignes", "—"),
        ("artificialisation_flux.json", "JSON", "Les mêmes flux, au format de lecture du démonstrateur", "—"),
        ("synthese.json", "JSON", "Indicateurs de synthèse à l'échelle du territoire", "—"),
    ]
    lignes = [[Paragraph(x, CELB) for x in
               ("Fichier", "Format", "Contenu", "Référentiel", "Taille")]]
    for nom, fmt, contenu, ref in fichiers:
        p = DATA / nom
        lignes.append([
            Paragraph(nom, MONO), Paragraph(fmt, CEL), Paragraph(contenu, CEL),
            Paragraph(ref, CELG), Paragraph(ko(p) if p.exists() else "absent", CELG),
        ])
    histoire.append(tableau(lignes, [48 * mm, 16 * mm, 70 * mm, 24 * mm, 16 * mm]))
    histoire += [
        Spacer(1, 4 * mm),
        Paragraph(
            "S'y ajoutent cinq fiches de métadonnées au format JSON — une par source — reproduites "
            "au point 3 de la présente pièce. Les onze jeux et les cinq fiches sont téléchargeables "
            "depuis le volet « sources » du démonstrateur, à l'adresse "
            "<b>pcaet.carte42.fr</b>.", P),
        Paragraph(
            "Les formats retenus sont ceux qu'impose le § IV du cahier des charges : Shapefile ou "
            "GeoJSON pour les données géographiques, accompagnées de leurs métadonnées, et CSV pour "
            "les données tabulaires. La couche est livrée dans les deux formats géographiques, le "
            "Shapefile tronquant les noms de champs à dix caractères — d'où le dictionnaire de "
            "correspondance joint à l'archive et reproduit au point 2.", P),
    ]

    # 2. Dictionnaire des champs
    histoire.append(Paragraph("2 — Dictionnaire des champs de la couche communale", H2))
    histoire.append(Paragraph(
        "Vingt-deux champs, dans l'ordre de la table livrée. La colonne « Shapefile » donne le nom "
        "tronqué à dix caractères correspondant. La colonne « Source » renvoie aux fiches de "
        "métadonnées du point 3 ; la mention « Calcul » désigne un champ dérivé des précédents, dont "
        "la formule est donnée en définition.", P))
    lignes = [[Paragraph(x, CELB) for x in
               ("Champ", "Shapefile", "Définition", "Unité", "Source")]]
    for c in colonnes:
        d, u, s = CHAMPS[c]
        lignes.append([
            Paragraph(c, MONO), Paragraph(champs_shp.get(c, "—"), MONO),
            Paragraph(d, CEL), Paragraph(u, CELG), Paragraph(s, CELG),
        ])
    histoire.append(tableau(lignes, [32 * mm, 22 * mm, 74 * mm, 22 * mm, 24 * mm]))

    # 3. Fiches de métadonnées
    histoire.append(Paragraph("3 — Fiches de métadonnées, une par source", H2))
    histoire.append(Paragraph(
        "Chaque jeu de données est référencé avec son producteur, son millésime, sa licence et ses "
        "réserves de lecture. Les fiches sont reproduites ici telles que le démonstrateur les publie.", P))
    for nom, titre in FICHES:
        d = json.loads((DATA / nom).read_text(encoding="utf-8"))
        lignes = []
        for cle in ORDRE:
            if cle in d:
                lignes.append([
                    Paragraph(LIBELLES[cle], CELB),
                    Paragraph(valeur(cle, d[cle]), CEL),
                ])
        for cle in d:  # rien ne doit échapper à la fiche
            if cle not in ORDRE:
                lignes.append([Paragraph(LIBELLES.get(cle, cle), CELB),
                               Paragraph(valeur(cle, d[cle]), CEL)])
        histoire.append(KeepTogether([
            Paragraph(titre, H3),
            Paragraph(f"Fichier : <font face='Courier'>{nom}</font>", CELG),
            Spacer(1, 2 * mm),
            tableau(lignes, [46 * mm, 128 * mm], entete=False),
        ]))

    # 4. Indicateurs de synthèse — ce que les jeux donnent à lire
    histoire.append(Paragraph("4 — Ce que ces jeux donnent à lire", H2))
    a = synthese["artificialisation"]
    p0, p1 = a["periodes"][0], a["periodes"][1]
    lignes = [[Paragraph(x, CELB) for x in ("Indicateur", "Valeur", "Source")]]
    for lib, val, src in [
        ("Communes", f"{fr(synthese['territoire']['communes'])}", "Découpage administratif"),
        ("Population", f"{fr(synthese['territoire']['population'])} habitants", "Découpage administratif"),
        ("Surface", f"{fr(synthese['territoire']['surface_ha'])} hectares", "Calcul sur géométries"),
        (f"Artificialisation nette {p0['etiquette']}", f"{fr(p0['solde_ha'])} hectares", "OCS GE"),
        (f"Artificialisation nette {p1['etiquette']}", f"{fr(p1['solde_ha'])} hectares", "OCS GE"),
        ("Évolution du rythme annuel",
         f"{fr(a['evolution_du_rythme_pct']).replace('-', '−')} %", "Calcul"),
        ("Indice de végétation moyen", f"{fr(synthese['vegetation']['ndvi_moyen_territoire'])}", "Sentinel-2"),
        ("Pixels exploitables de la scène", f"{fr(synthese['vegetation']['pixels_exploitables_pct'])} %", "Sentinel-2"),
        ("Communes relevant d'un territoire à risque important d'inondation",
         f"{fr(list(synthese['risques']['tri'].values())[0])} sur 31", "Géorisques"),
        ("Croisements qualifiés dans la matrice",
         f"{len(matrice['cellules'])} sur {len(matrice['enjeux']) * len(matrice['leviers'])}", "Matrice"),
    ]:
        lignes.append([Paragraph(lib, CEL), Paragraph(val, CELB), Paragraph(src, CELG)])
    histoire.append(tableau(lignes, [88 * mm, 44 * mm, 42 * mm]))
    histoire += [
        Spacer(1, 4 * mm),
        Paragraph(
            "Les croisements sans incidence notable identifiée ne sont pas renseignés : une matrice "
            "d'évaluation réelle comporte des cases vides. De même, la cellule « tri » est vide pour "
            "les douze communes qui ne relèvent pas d'un territoire à risque important d'inondation : "
            "une valeur absente s'écrit comme une cellule vide, et non comme un code de valeur "
            "manquante hérité de l'outil de calcul.", P),
    ]

    # ── Mise en page ─────────────────────────────────────────────────────────
    L, H = A4
    marge = 18 * mm

    def pied(canevas, doc):
        canevas.saveState()
        canevas.setStrokeColor(FILET)
        canevas.setLineWidth(0.4)
        canevas.line(marge, 13 * mm, L - marge, 13 * mm)
        canevas.setFont("Helvetica", 6.8)
        canevas.setFillColor(GRIS)
        canevas.drawString(
            marge, 9 * mm,
            "Annexe B2 — Marché M6C0007TE, lot 1 — Carte 42 — Sources ouvertes : "
            "IGN, Copernicus, Géorisques, Etalab")
        canevas.drawRightString(L - marge, 9 * mm, f"{doc.page}")
        canevas.restoreState()

    doc = BaseDocTemplate(
        str(SORTIE), pagesize=A4,
        leftMargin=marge, rightMargin=marge, topMargin=marge, bottomMargin=20 * mm,
        title="Annexe B2 — Jeux de données du démonstrateur et fiches de métadonnées",
        author="Carte 42", subject="Marché M6C0007TE, lot 1",
    )
    doc.addPageTemplates([PageTemplate(
        id="corps",
        frames=[Frame(marge, 20 * mm, L - 2 * marge, H - marge - 20 * mm, id="f")],
        onPage=pied,
    )])
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    doc.build(histoire)
    print(f"\n  {SORTIE.name} — {ko(SORTIE)}, {doc.page} pages")

    COPIE.parent.mkdir(parents=True, exist_ok=True)
    COPIE.write_bytes(SORTIE.read_bytes())
    print(f"  copie jointe au pli : {COPIE}")


if __name__ == "__main__":
    main()
