# -*- coding: utf-8 -*-
# =====================================================================
#  OBSERVATOIRE NATIONAL DE L'INDUSTRIE DE GUINEE
#  Systeme d'Information Decisionnel (SID) - Portail Streamlit
#  Memoire M2 Statistique et Informatique Decisionnelle
#  Ansoumane CONTE - Universite Alioune Diop de Bambey
# =====================================================================

from pathlib import Path

import hmac
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------
#  Theme Streamlit : cree automatiquement .streamlit/config.toml au 1er
#  lancement, pour que les couleurs d'interface suivent la charte de
#  l'observatoire (et non le rouge par defaut de Streamlit).
# ---------------------------------------------------------------------
_CONFIG = Path(".streamlit/config.toml")
_THEME_CREE = False
if not _CONFIG.exists():
    try:
        _CONFIG.parent.mkdir(exist_ok=True)
        _CONFIG.write_text(
            "[theme]\n"
            'primaryColor = "#A0522D"\n'
            'backgroundColor = "#F7F6F3"\n'
            'secondaryBackgroundColor = "#FFFFFF"\n'
            'textColor = "#14130F"\n'
            'font = "sans serif"\n\n'
            "[browser]\n"
            "gatherUsageStats = false\n",
            encoding="utf-8")
        _THEME_CREE = True
    except Exception:
        pass

st.set_page_config(
    page_title="Observatoire National de l'Industrie - Guinée",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
#  1. SYSTEME GRAPHIQUE
# =====================================================================
# Identite (reprise du prototype Tableau)
BAUXITE = "#A0522D"        # accent de marque
BAUXITE_FONCE = "#7E3F22"
ANTHRACITE = "#2B2B2B"     # fond de la barre laterale

# Plans et encres
PLAN = "#F7F6F3"           # fond de page
SURFACE = "#FFFFFF"        # fond des cartes
ENCRE = "#14130F"          # texte principal
ENCRE_2 = "#55534E"        # texte secondaire
ENCRE_MUET = "#8A8781"     # axes, libelles
GRILLE = "#E6E4DD"
BORDURE = "rgba(11,11,11,0.09)"

# Couleurs nationales (filet decoratif de l'en-tete)
GN_ROUGE, GN_JAUNE, GN_VERT = "#CE1126", "#FCD116", "#009460"

# Rampe sequentielle une seule teinte (magnitude)
RAMPE_BAUXITE = ["#F7EDE6", "#EBD3C2", "#DDB79D", "#CB9776",
                 "#B67551", BAUXITE, BAUXITE_FONCE]

# Palette categorielle validee (separation daltonisme verifiee)
CAT = ["#2A78D6", "#EB6834", "#1BAF7A"]
COULEURS_PROFIL = {
    "Pôles industriels majeurs": CAT[0],
    "Régions intermédiaires": CAT[1],
    "Régions moins industrialisées": CAT[2],
}

# Divergente (correlations) : bleu <-> gris neutre <-> rouge
DIVERGENTE = [[0.0, "#2A78D6"], [0.5, "#F0EFEC"], [1.0, "#E34948"]]

# Statut (qualite des donnees) - jamais utilise comme couleur de serie
STATUT = {"Bonne": "#0CA30C", "À surveiller": "#FAB219", "Insuffisante": "#D03B3B"}

POLICE = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

st.markdown(f"""
<style>
.stApp {{ background:{PLAN}; }}
/* On masque le menu et le bouton de deploiement, mais SURTOUT PAS toute la
   barre d'outils : elle contient le bouton qui rouvre la barre laterale. */
#MainMenu, footer, [data-testid="stAppDeployButton"] {{ display:none !important; }}
[data-testid="stToolbar"] {{ display:flex !important; }}

/* Bouton de reouverture de la barre laterale : toujours visible et contraste */
[data-testid="stExpandSidebarButton"] {{
  display:flex !important; visibility:visible !important; opacity:1 !important;
  align-items:center; justify-content:center;
  width:2.4rem !important; height:2.4rem !important;
  background:{ANTHRACITE} !important; border-radius:8px !important;
  z-index:999999 !important; }}
[data-testid="stExpandSidebarButton"] svg {{
  color:#FFFFFF !important; fill:#FFFFFF !important; }}
[data-testid="stExpandSidebarButton"]:hover {{ background:{BAUXITE} !important; }}
.block-container {{ padding-top:1.2rem; padding-bottom:3rem; max-width:1400px; }}
html, body, [class*="css"] {{ font-family:{POLICE}; color:{ENCRE}; }}

/* ---------- Barre laterale ---------- */
[data-testid="stSidebar"] {{ background:{ANTHRACITE}; }}
[data-testid="stSidebar"] * {{ color:#EDEBE6 !important; }}
[data-testid="stSidebar"] h1 {{ font-size:1.15rem !important; letter-spacing:.02em; }}
[data-testid="stSidebar"] hr {{ border-color:rgba(255,255,255,.14); }}

/* ---------- En-tete ---------- */
.entete {{
  background:linear-gradient(100deg,{ANTHRACITE} 0%,#4A3327 55%,{BAUXITE} 100%);
  border-radius:12px; padding:1.5rem 1.75rem 1.25rem; margin-bottom:.45rem;
}}
.entete h1 {{ color:#fff; font-size:1.6rem; font-weight:650; margin:0 0 .3rem;
  letter-spacing:-.01em; line-height:1.25; }}
.entete p {{ color:rgba(255,255,255,.82); font-size:.92rem; margin:0; }}
.filet {{ display:flex; height:4px; border-radius:2px; overflow:hidden;
  margin-bottom:1.5rem; }}
.filet span {{ flex:1; }}

/* ---------- Cartes d'indicateurs ---------- */
.kpi-rangee {{ display:flex; gap:.9rem; margin-bottom:1.6rem; flex-wrap:wrap; }}
.kpi {{
  flex:1; min-width:190px; background:{SURFACE}; border:1px solid {BORDURE};
  border-left:3px solid {BAUXITE}; border-radius:10px; padding:.95rem 1.1rem;
}}
.kpi .lib {{ font-size:.7rem; text-transform:uppercase; letter-spacing:.07em;
  color:{ENCRE_MUET}; font-weight:600; margin-bottom:.4rem; }}
.kpi .val {{ font-size:1.85rem; font-weight:640; color:{ENCRE}; line-height:1.1; }}
.kpi .sub {{ font-size:.76rem; color:{ENCRE_2}; margin-top:.25rem; }}
.hausse {{ color:#006300; font-weight:600; }}
.baisse {{ color:#C0392B; font-weight:600; }}

/* ---------- Titres de section ---------- */
.titre-section {{
  font-size:1.02rem; font-weight:650; color:{ENCRE}; margin:1.6rem 0 .7rem;
  padding-left:.6rem; border-left:3px solid {BAUXITE};
}}
h2, h3 {{ color:{ENCRE}; font-weight:640; }}
[data-testid="stDataFrame"] {{ border:1px solid {BORDURE}; border-radius:10px; }}
[data-testid="stHeader"] {{ background:transparent; }}

/* ---------- Couleur d'accent (remplace le rouge Streamlit) ---------- */
:root {{ --primary-color:{BAUXITE}; }}
[data-baseweb="tag"] {{ background-color:{BAUXITE} !important; }}
[data-testid="stSidebar"] [data-baseweb="tag"] span {{ color:#fff !important; }}
input[type="radio"] {{ accent-color:{BAUXITE}; }}
[data-testid="stSidebar"] [role="radiogroup"] [data-checked="true"] div:first-child,
[data-testid="stSidebar"] [role="radiogroup"] input:checked + div {{
  background-color:{BAUXITE} !important; border-color:{BAUXITE} !important; }}
.stDownloadButton button {{ background:{BAUXITE}; color:#fff; border:none; }}
.stDownloadButton button:hover {{ background:{BAUXITE_FONCE}; color:#fff; }}

/* Champs de saisie de la barre laterale : texte noir sur fond blanc,
   sinon le texte blanc du menu rend la saisie invisible. */
[data-testid="stSidebar"] input {{
  color:#14130F !important; background:#FFFFFF !important;
  -webkit-text-fill-color:#14130F !important; }}
[data-testid="stSidebar"] input::placeholder {{ color:#8A8781 !important; }}
[data-testid="stSidebar"] .stButton button {{
  background:{BAUXITE} !important; border:none !important;
  color:#FFFFFF !important; font-weight:600; }}
[data-testid="stSidebar"] .stButton button * {{ color:#FFFFFF !important; }}
[data-testid="stSidebar"] .stButton button:hover {{
  background:{BAUXITE_FONCE} !important; }}

/* ---------- Bandeau defilant + visuel Simandou ---------- */
.bandeau-defilant {{
  overflow:hidden; background:{ANTHRACITE}; border-radius:10px 10px 0 0;
  padding:.6rem 0; margin-top:2.2rem; }}
.bandeau-defilant span {{
  display:inline-block; white-space:nowrap; padding-left:100%;
  color:{GN_JAUNE}; font-weight:650; letter-spacing:.14em; font-size:.88rem;
  text-transform:uppercase;
  animation:defile 22s linear infinite; }}
@keyframes defile {{ 0% {{ transform:translateX(0); }}
                     100% {{ transform:translateX(-100%); }} }}
.visuel-simandou img {{
  width:100%; max-height:380px; object-fit:cover; display:block;
  border-radius:0 0 10px 10px; }}
.visuel-repli {{
  border-radius:0 0 10px 10px; padding:2.6rem 2rem; color:#fff;
  background:linear-gradient(120deg,{ANTHRACITE} 0%,#4A3327 50%,{BAUXITE} 100%);
  position:relative; overflow:hidden; }}
.visuel-repli h3 {{ color:#fff !important; margin:0 0 .5rem; font-size:1.35rem;
  font-weight:650; }}
.visuel-repli p {{ color:rgba(255,255,255,.85); margin:0; max-width:60ch;
  font-size:.92rem; line-height:1.55; }}
.visuel-repli .relief {{ position:absolute; right:-40px; bottom:-30px;
  opacity:.16; }}
</style>
""", unsafe_allow_html=True)


def nb_fr(v, decimales=0):
    """Formatage francais : espace comme separateur de milliers."""
    return f"{v:,.{decimales}f}".replace(",", " ").replace(".", ",")


def styliser(fig, hauteur=360, legende=False, grille_x=False, grille_y=False):
    """Applique la charte : chrome discret, grilles au choix, marges aerees."""
    fig.update_layout(
        height=hauteur,
        margin=dict(l=8, r=16, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=POLICE, size=12, color=ENCRE_2),
        showlegend=legende,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    title_text="", font=dict(size=11)),
        hoverlabel=dict(bgcolor=SURFACE, font_size=12, font_family=POLICE,
                        bordercolor=BORDURE),
        bargap=0.32,
        separators=", ",   # virgule decimale, espace pour les milliers
    )
    fig.update_xaxes(showgrid=grille_x, gridcolor=GRILLE, gridwidth=1, zeroline=False,
                     linecolor=GRILLE, tickfont=dict(color=ENCRE_MUET, size=11),
                     title_font=dict(color=ENCRE_MUET, size=11))
    fig.update_yaxes(showgrid=grille_y, gridcolor=GRILLE, gridwidth=1, zeroline=False,
                     linecolor=GRILLE, tickfont=dict(color=ENCRE_MUET, size=11),
                     title_font=dict(color=ENCRE_MUET, size=11))
    return fig


def barres_h(d, x, y, couleur=BAUXITE, hauteur=360, decimales=0, suffixe=""):
    """Barres horizontales : une serie, une couleur, etiquettes directes."""
    etiquettes = [nb_fr(v, decimales) + suffixe for v in d[x]]
    fig = px.bar(d, x=x, y=y, orientation="h", color_discrete_sequence=[couleur])
    fig.update_traces(
        text=etiquettes, texttemplate="%{text}", textposition="outside",
        textfont=dict(size=11, color=ENCRE_2), cliponaxis=False,
        marker=dict(cornerradius=4),
        customdata=etiquettes,
        hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"},
                      xaxis_title="", yaxis_title="")
    fig = styliser(fig, hauteur)
    # marge a droite pour que les etiquettes ne soient jamais tronquees
    fig.update_xaxes(showticklabels=False, showgrid=False,
                     range=[0, float(d[x].max()) * 1.20])
    return fig


def entete(titre, sous_titre):
    st.markdown(
        f'<div class="entete"><h1>{titre}</h1><p>{sous_titre}</p></div>'
        f'<div class="filet"><span style="background:{GN_ROUGE}"></span>'
        f'<span style="background:{GN_JAUNE}"></span>'
        f'<span style="background:{GN_VERT}"></span></div>',
        unsafe_allow_html=True)


def section(titre):
    st.markdown(f'<div class="titre-section">{titre}</div>', unsafe_allow_html=True)


def carte_kpi(cartes):
    """cartes = liste de (libellé, valeur, sous-texte html ou '')"""
    html = '<div class="kpi-rangee">'
    for lib, val, sub in cartes:
        html += (f'<div class="kpi"><div class="lib">{lib}</div>'
                 f'<div class="val">{val}</div><div class="sub">{sub}</div></div>')
    st.markdown(html + "</div>", unsafe_allow_html=True)


# =====================================================================
#  2. DONNEES
# =====================================================================
# Le portail lit desormais l'ENTREPOT DE DONNEES (schema en etoile) et non
# plus directement le fichier Excel : la couche de stockage de l'architecture
# est ainsi reellement traversee. L'entrepot est construit par etl_observatoire.py.
ENTREPOT = "observatoire.db"

LIBELLES = {
    "nb_entreprises_actives": "Entreprises actives",
    "emploi_direct": "Emploi direct",
    "indice_production_industrielle": "Indice de production industrielle",
    "chiffre_affaires_milliards_gnf": "Chiffre d'affaires (Mds GNF)",
    "valeur_ajoutee_milliards_gnf": "Valeur ajoutée (Mds GNF)",
    "exportations_milliards_gnf": "Exportations (Mds GNF)",
    "investissement_milliards_gnf": "Investissement (Mds GNF)",
    "consommation_energie_mwh": "Consommation d'énergie (MWh)",
    "consommation_eau_m3": "Consommation d'eau (m³)",
    "jours_arret_production": "Jours d'arrêt de production",
    "coupures_electricite_heures": "Coupures d'électricité (heures)",
    "taux_utilisation_capacite_pct": "Taux d'utilisation des capacités (%)",
    "part_femmes_emploi_pct": "Part des femmes dans l'emploi (%)",
    "accidents_travail_declares": "Accidents du travail déclarés",
    "emissions_co2_tonnes": "Émissions de CO2 (tonnes)",
    "conformite_fiscale_pct": "Conformité fiscale (%)",
    "maturite_numerique_score_100": "Maturité numérique (/100)",
}

DIMENSIONS = {
    # Cinq dimensions alignees sur le memoire (3.3 et tableau 4, section 4.4.2)
    "Activité économique": ["nb_entreprises_actives", "chiffre_affaires_milliards_gnf",
                            "valeur_ajoutee_milliards_gnf", "exportations_milliards_gnf",
                            "investissement_milliards_gnf"],
    "Emploi et conditions sociales": ["emploi_direct", "part_femmes_emploi_pct",
                                      "accidents_travail_declares"],
    "Production et capacité": ["indice_production_industrielle",
                               "taux_utilisation_capacite_pct", "jours_arret_production"],
    "Énergie et environnement": ["consommation_energie_mwh", "consommation_eau_m3",
                                 "coupures_electricite_heures", "emissions_co2_tonnes"],
    "Conformité et maturité": ["conformite_fiscale_pct", "maturite_numerique_score_100"],
}


# Convention territoriale : le rattachement des 8 regions administratives aux
# 4 regions naturelles n'est plus code ici. Il est porte par la table de
# dimension Dim_Region de l'entrepot, et lu avec les donnees (voir plus bas).
ORDRE_NATUREL = ["Basse-Guinée", "Moyenne-Guinée", "Haute-Guinée",
                 "Guinée forestière"]


# Colonnes indispensables au fonctionnement du portail
COLONNES_REQUISES = ["annee", "region", "secteur_industriel",
                     "chiffre_affaires_milliards_gnf"]


def empreinte(chemin):
    """Taille + date de modification : change des que le fichier est remplacé.
    Sert de cle de cache, sinon de nouvelles données resteraient invisibles."""
    p = Path(chemin)
    return (p.stat().st_size, p.stat().st_mtime) if p.exists() else None


REQUETE_ENTREPOT = """
    SELECT da.annee            AS annee,
           dr.libelle_region   AS region,
           dr.region_naturelle AS region_naturelle,
           ds.libelle_secteur  AS secteur_industriel,
           f.*
    FROM Fait_industrie f
    JOIN Dim_Region  dr ON dr.id_region  = f.id_region
    JOIN Dim_Secteur ds ON ds.id_secteur = f.id_secteur
    JOIN Dim_Annee   da ON da.id_annee   = f.id_annee;
"""


@st.cache_data
def charger_donnees(chemin, _empreinte):
    """Lit l'entrepôt : la table de faits jointe à ses trois dimensions.
    Le resultat a exactement la meme forme que l'ancien fichier à plat, de
    sorte que le reste du portail est inchangé."""
    import sqlite3
    con = sqlite3.connect(chemin)
    d = pd.read_sql_query(REQUETE_ENTREPOT, con)
    con.close()
    return d.drop(columns=["id_region", "id_secteur", "id_annee"])


def formater(n):
    return "—" if pd.isna(n) else f"{n:,.0f}".replace(",", " ")


@st.cache_data
def image_simandou():
    """Cherche une photo nommée 'simandou' dans le dossier de l'application.
    Si aucune n'est trouvée, un visuel graphique de repli est utilisé."""
    import base64
    for nom in ("simandou.jpg", "simandou.jpeg", "simandou.png", "simandou.webp"):
        p = Path(nom)
        if p.exists():
            ext = "jpeg" if p.suffix in (".jpg", ".jpeg") else p.suffix[1:]
            return f"data:image/{ext};base64," + base64.b64encode(
                p.read_bytes()).decode()
    return None


def bloc_simandou():
    """Bandeau defilant + visuel du Programme Simandou 2040 (bas de page)."""
    texte = ("Programme Simandou 2040 &nbsp;·&nbsp; Transformation structurelle "
             "de l'économie guinéenne &nbsp;·&nbsp; Valorisation locale des "
             "ressources &nbsp;·&nbsp; Diversification du tissu industriel "
             "&nbsp;·&nbsp; ")
    st.markdown(f'<div class="bandeau-defilant"><span>{texte * 2}</span></div>',
                unsafe_allow_html=True)

    src = image_simandou()
    if src:
        st.markdown(f'<div class="visuel-simandou"><img src="{src}" '
                    f'alt="Programme Simandou 2040"></div>',
                    unsafe_allow_html=True)
    else:
        # Visuel de repli : relief stylise (aucune image externe requise)
        relief = (
            '<svg class="relief" width="420" height="200" viewBox="0 0 420 200" '
            'fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M0 200 L110 70 L180 140 L250 40 L330 130 L420 60 L420 200 Z" '
            'fill="#ffffff"/>'
            '<path d="M0 200 L90 120 L160 175 L240 105 L320 180 L420 120 L420 200 Z" '
            'fill="#ffffff" opacity="0.6"/></svg>')
        st.markdown(
            f'<div class="visuel-repli">{relief}'
            '<h3>Programme Simandou 2040</h3>'
            "<p>L'observatoire s'inscrit dans la perspective de transformation "
            "structurelle portée par le Programme Simandou 2040 : valorisation "
            "locale des ressources, développement des chaînes de valeur "
            "industrielles et diversification du tissu productif national.</p>"
            '</div>', unsafe_allow_html=True)


if not Path(ENTREPOT).exists():
    st.error(f"Entrepôt de données introuvable : « {ENTREPOT} ». "
             "Construisez-le en lançant `python etl_observatoire.py` dans ce "
             "dossier, puis relancez le portail.")
    st.stop()

df = charger_donnees(ENTREPOT, empreinte(ENTREPOT))

# La convention territoriale est lue dans l'entrepot, pas redefinie ici.
REGIONS_NATURELLES = (df[["region", "region_naturelle"]].drop_duplicates()
                      .set_index("region")["region_naturelle"].to_dict())

_manquantes = [c for c in COLONNES_REQUISES if c not in df.columns]
if _manquantes:
    st.error("Colonnes obligatoires absentes du fichier de données : "
             + ", ".join(_manquantes)
             + ". Renommez-les dans le fichier source, ou adaptez le "
               "dictionnaire LIBELLES en tête de ce script.")
    st.stop()

# Seuls les indicateurs reellement presents sont exploites : le portail
# s'adapte donc a un jeu de donnees reel plus riche ou plus pauvre.
LIBELLES = {c: l for c, l in LIBELLES.items() if c in df.columns}
DIMENSIONS = {d: [c for c in cols if c in df.columns]
              for d, cols in DIMENSIONS.items()}
DIMENSIONS = {d: cols for d, cols in DIMENSIONS.items() if cols}

# =====================================================================
#  3. ACCES DIFFERENCIES (chapitre 3.1.4)
# =====================================================================
PAGES_PUBLIC = ["Accueil", "L'Observatoire"]
PAGES_INVEST = PAGES_PUBLIC + ["Analyse régionale & sectorielle", "Fiche régionale",
                               "Dimensions complémentaires"]
PAGES_AUTORITE = PAGES_INVEST + ["Analyse avancée", "Qualité des données",
                                 "Données & indicateurs"]
DROITS = {"Grand public": PAGES_PUBLIC, "Investisseurs et bailleurs (PTF)": PAGES_INVEST,
          "Pouvoirs publics": PAGES_AUTORITE}
# Les comptes de demonstration ne figurent pas dans le code : ils sont lus
# dans les "secrets" de l'application (Streamlit Cloud > Settings > Secrets,
# ou fichier local .streamlit/secrets.toml exclu du depot). Aucun identifiant
# n'est donc publie avec le code source.
def charger_comptes():
    try:
        brut = dict(st.secrets["comptes"])
    except Exception:
        return {}
    comptes = {}
    for identifiant, champs in brut.items():
        profil = str(champs.get("profil", "")).strip()
        mdp = str(champs.get("mdp", ""))
        if profil in DROITS and mdp:
            comptes[identifiant.strip().lower()] = {"mdp": mdp, "profil": profil}
    return comptes


COMPTES = charger_comptes()

if "profil" not in st.session_state:
    st.session_state["profil"] = "Grand public"

st.sidebar.markdown("# 🏭 Observatoire")
st.sidebar.caption("National de l'Industrie — Guinée")
st.sidebar.divider()

if st.session_state["profil"] == "Grand public":
    st.sidebar.markdown("**🔐 Espace utilisateur**")
    st.sidebar.caption("Accès libre aux données agrégées. "
                       "Connectez-vous pour les analyses détaillées.")
    ident = st.sidebar.text_input("Identifiant")
    mdp = st.sidebar.text_input("Mot de passe", type="password")
    if st.sidebar.button("Se connecter", use_container_width=True):
        c = COMPTES.get(ident.strip().lower())
        # comparaison a duree constante : ne revele pas la longueur du mot de passe
        if c and hmac.compare_digest(str(c["mdp"]), str(mdp)):
            st.session_state["profil"] = c["profil"]
            st.rerun()
        else:
            st.sidebar.error("Identifiant ou mot de passe incorrect.")
else:
    st.sidebar.success(f"Connecté : {st.session_state['profil']}")
    if st.sidebar.button("Se déconnecter", use_container_width=True):
        st.session_state["profil"] = "Grand public"
        st.rerun()

profil = st.session_state["profil"]
st.sidebar.divider()
page = st.sidebar.radio("Navigation", DROITS[profil])

if _THEME_CREE:
    st.sidebar.info("Thème de l'observatoire installé. Arrêtez l'application "
                    "(Ctrl + C) et relancez `streamlit run app.py` pour "
                    "l'appliquer — à faire une seule fois.")

st.sidebar.divider()
st.sidebar.subheader("Filtres")
annees = sorted(df["annee"].unique())
annee_choisie = st.sidebar.selectbox("Année", annees, index=len(annees) - 1)
regions = sorted(df["region"].unique())
regions_choisies = st.sidebar.multiselect("Région(s)", regions, default=regions)
secteurs = sorted(df["secteur_industriel"].unique())
secteurs_choisis = st.sidebar.multiselect("Secteur(s)", secteurs, default=secteurs)

df_annee = df[(df["annee"] == annee_choisie)
              & df["region"].isin(regions_choisies)
              & df["secteur_industriel"].isin(secteurs_choisis)]
df_filtre = df[df["region"].isin(regions_choisies)
               & df["secteur_industriel"].isin(secteurs_choisis)]


# =====================================================================
#  PAGE : ACCUEIL
# =====================================================================
def page_accueil():
    entete("Observatoire National de l'Industrie de Guinée",
           f"Système d'information décisionnel · données {annees[0]}–{annees[-1]} "
           f"· année affichée : {annee_choisie}")

    ca = df_annee["chiffre_affaires_milliards_gnf"].sum()
    prec = df[(df["annee"] == annee_choisie - 1)
              & df["region"].isin(regions_choisies)
              & df["secteur_industriel"].isin(secteurs_choisis)]
    ca_prec = prec["chiffre_affaires_milliards_gnf"].sum()
    if ca_prec > 0:
        v = (ca - ca_prec) / ca_prec * 100
        cls = "hausse" if v >= 0 else "baisse"
        var = f'<span class="{cls}">{v:+.1f} %</span> vs {annee_choisie-1}'.replace('.', ',')
    else:
        var = "année de référence"

    _ent = df_annee["nb_entreprises_actives"].sum() if \
        "nb_entreprises_actives" in df.columns else float("nan")
    _emp = df_annee["emploi_direct"].sum() if \
        "emploi_direct" in df.columns else float("nan")
    carte_kpi([
        ("Entreprises actives", formater(_ent),
         f"{len(regions_choisies)} régions · {len(secteurs_choisis)} secteurs"),
        ("Emploi direct", formater(_emp), "emplois recensés"),
        ("Chiffre d'affaires", formater(ca), "milliards GNF"),
        ("Évolution du CA", f"{(ca-ca_prec)/ca_prec*100:+.1f} %".replace(".", ",") if ca_prec else "—", var),
    ])

    c1, c2 = st.columns(2)
    with c1:
        section(f"Chiffre d'affaires par région · {annee_choisie}")
        d = (df_annee.groupby("region")["chiffre_affaires_milliards_gnf"]
             .sum().sort_values(ascending=False).reset_index())
        st.plotly_chart(barres_h(d, "chiffre_affaires_milliards_gnf", "region"),
                        use_container_width=True)
    with c2:
        section(f"Chiffre d'affaires par secteur · {annee_choisie}")
        d = (df_annee.groupby("secteur_industriel")["chiffre_affaires_milliards_gnf"]
             .sum().sort_values(ascending=False).reset_index())
        st.plotly_chart(barres_h(d, "chiffre_affaires_milliards_gnf",
                                 "secteur_industriel"), use_container_width=True)

    section(f"Évolution du chiffre d'affaires · {annees[0]}–{annees[-1]}")
    d = df_filtre.groupby("annee")["chiffre_affaires_milliards_gnf"].sum().reset_index()
    fig = px.line(d, x="annee", y="chiffre_affaires_milliards_gnf", markers=True)
    fig.update_traces(line=dict(color=BAUXITE, width=2),
                      marker=dict(size=9, color=BAUXITE,
                                  line=dict(width=2, color=SURFACE)),
                      hovertemplate="<b>%{x}</b><br>%{y:,.0f} Mds GNF<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title="Mds GNF")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(styliser(fig, 320, grille_y=True), use_container_width=True)

    if profil == "Grand public":
        st.info("Vous consultez l'observatoire en accès libre (données agrégées). "
                "Les analyses détaillées sont accessibles aux investisseurs et "
                "partenaires sur inscription, et l'ensemble des analyses avancées "
                "aux pouvoirs publics authentifiés — voir « Espace utilisateur » "
                "dans le menu de gauche.")

    bloc_simandou()


# =====================================================================
#  PAGE : L'OBSERVATOIRE
# =====================================================================
def page_presentation():
    entete("L'Observatoire", "Mission, architecture, sources et règles d'accès")

    section("Mission")
    st.write("L'Observatoire National de l'Industrie de Guinée a pour mission de "
             "centraliser, structurer, analyser et diffuser l'information relative au "
             "secteur industriel guinéen, afin d'éclairer la décision publique, "
             "d'orienter les investisseurs et d'informer le grand public.")

    section("Objectifs")
    st.markdown(
        "- Identifier les besoins informationnels des parties prenantes\n"
        "- Inventorier et évaluer les sources de données disponibles\n"
        "- Concevoir l'architecture technique du système décisionnel\n"
        "- Définir les règles de gouvernance des données\n"
        "- Mettre à disposition un portail de diffusion\n"
        "- Proposer un jeu d'indicateurs sectoriels de référence")

    section("Architecture du système d'information décisionnel")
    for col, (t, d) in zip(st.columns(4), [
        ("1 · Collecte", "Identifiant unique par entreprise, uniformisation des formats"),
        ("2 · Entrepôt", "Stockage et organisation par année, région et secteur"),
        ("3 · Analyse", "Calcul des agrégats et des indicateurs"),
        ("4 · Diffusion", "Portail avec accès différenciés selon les publics")]):
        col.markdown(
            f'<div class="kpi"><div class="lib">{t}</div>'
            f'<div class="sub" style="font-size:.85rem;margin-top:.4rem">{d}</div></div>',
            unsafe_allow_html=True)

    section("Ancrage national et stratégique")
    st.write(
        "L'observatoire s'inscrit dans le cadre de la politique industrielle de la "
        "République de Guinée et, en particulier, dans la perspective de "
        "transformation structurelle portée par le **Programme Simandou 2040**, qui "
        "vise la valorisation locale des ressources et la diversification du tissu "
        "industriel. Placé sous la tutelle du ministère en charge de l'industrie, il "
        "a vocation à s'articuler avec l'écosystème économique national — Chambre de "
        "Commerce, d'Industrie et d'Artisanat de Guinée, organisations patronales, "
        "institutions de financement et partenaires techniques et financiers — qui "
        "sont à la fois fournisseurs de données et utilisateurs des analyses "
        "produites.")

    section("Conventions territoriales")
    st.write(
        "Les analyses sont conduites à deux mailles : les **8 régions "
        "administratives** et les **4 régions naturelles**, qui traduisent mieux les "
        "réalités économiques du pays. Le rattachement retenu est le suivant :")
    st.dataframe(pd.DataFrame([
        {"Région naturelle": rn,
         "Régions administratives": ", ".join(
             sorted(r for r, v in REGIONS_NATURELLES.items() if v == rn))}
        for rn in ORDRE_NATUREL]), use_container_width=True, hide_index=True)
    st.caption("Ce rattachement est appliqué de manière uniforme à l'ensemble "
               "des analyses du portail. Il est porté par la table de dimension "
               "Dim_Region de l'entrepôt de données.")

    section("Sources de données")
    st.markdown(
        "- **Institutionnelles** — Institut National de la Statistique, Direction "
        "Nationale de l'Industrie, agences de promotion des investissements\n"
        "- **Administratives** — Douanes, EDG, ministères des Mines et du Commerce, "
        "Environnement, Travail\n"
        "- **Sectorielles** — chambres de commerce, associations professionnelles")

    section("Les cinq dimensions d'indicateurs")
    # Tableau HTML (et non st.dataframe) : le texte long passe a la ligne au lieu
    # d'etre coupe au bord de la colonne.
    lignes = "".join(
        f"<tr><td style='padding:8px 12px;border-top:1px solid #E6E3DD;"
        f"white-space:nowrap;vertical-align:top'>{d}</td>"
        f"<td style='padding:8px 12px;border-top:1px solid #E6E3DD'>"
        f"{', '.join(LIBELLES[c] for c in cols)}</td></tr>"
        for d, cols in DIMENSIONS.items())
    st.markdown(
        "<table style='width:100%;border-collapse:collapse;background:#FFFFFF;"
        "border:1px solid #E6E3DD;border-radius:8px;font-size:0.92rem'>"
        "<tr style='color:#6B675F;text-align:left'>"
        "<th style='padding:8px 12px;font-weight:500'>Dimension</th>"
        "<th style='padding:8px 12px;font-weight:500'>Indicateurs</th></tr>"
        + lignes + "</table>", unsafe_allow_html=True)

    section("Accès différenciés")
    st.dataframe(pd.DataFrame([
        {"Profil": "Grand public", "Accès": "Libre, sans inscription",
         "Périmètre": "Données agrégées et présentation de l'observatoire"},
        {"Profil": "Investisseurs et bailleurs de fonds (PTF)",
         "Accès": "Sur inscription",
         "Périmètre": "Analyses détaillées par région, secteur et dimension"},
        {"Profil": "Pouvoirs publics", "Accès": "Authentifié",
         "Périmètre": "Accès complet : analyses avancées, qualité, export"}]),
        use_container_width=True, hide_index=True)
    st.caption("Le mécanisme d'authentification implémenté ici a valeur de "
               "démonstration : il illustre la logique d'accès différenciés décrite "
               "dans l'architecture, sans constituer un dispositif de sécurité de "
               "niveau production.")

    st.warning("**Note méthodologique** — Ce portail est un prototype académique "
               "réalisé dans le cadre d'un mémoire de Master. Il ne constitue pas "
               "un site officiel de la République de Guinée. Les données affichées "
               "sont issues d'un jeu synthétique construit pour la démonstration "
               "(240 observations, 8 régions, 6 secteurs, 2021-2025) et ne "
               "constituent pas des statistiques officielles.")

    section("Chaîne de traitement")
    st.write(
        "Les données affichées ne sont pas lues dans un fichier : elles sont "
        "extraites d'un **entrepôt de données** structuré en schéma en étoile "
        "(une table de faits au grain région x secteur x année, reliée aux "
        "dimensions Région, Secteur et Année). Cet entrepôt est alimenté par une "
        "chaîne ETL qui extrait le fichier source brut, le nettoie et le charge. "
        "Les quatre couches de l'architecture — collecte, prétraitement, stockage "
        "et diffusion — sont donc effectivement traversées à chaque consultation.")


# =====================================================================
#  PAGE : ANALYSE REGIONALE & SECTORIELLE
# =====================================================================
def page_analyse():
    entete("Analyse régionale & sectorielle",
           f"Comparaison des territoires et des branches · année {annee_choisie}")

    g1, g2 = st.columns([2, 1])
    with g1:
        _choix = [c for c in ["chiffre_affaires_milliards_gnf", "emploi_direct",
                              "exportations_milliards_gnf",
                              "valeur_ajoutee_milliards_gnf",
                              "investissement_milliards_gnf",
                              "nb_entreprises_actives"] if c in df.columns]
        col = st.selectbox("Indicateur analysé", _choix,
                           format_func=lambda c: LIBELLES[c])
    with g2:
        maille = st.radio("Maille territoriale",
                          ["Régions administratives (8)", "Régions naturelles (4)"],
                          horizontal=False)
    titre = LIBELLES[col]
    champ_geo = "region" if maille.startswith("Régions a") else "region_naturelle"

    c1, c2 = st.columns(2)
    with c1:
        section(f"{titre} — par {'région' if champ_geo=='region' else 'région naturelle'}")
        d = (df_annee.groupby(champ_geo)[col].sum()
             .sort_values(ascending=False).reset_index())
        st.plotly_chart(barres_h(d, col, champ_geo), use_container_width=True)
        if champ_geo == "region_naturelle":
            part = d[col] / d[col].sum() * 100
            tete = d.iloc[0]
            st.caption(f"Lecture : la {tete[champ_geo]} concentre "
                       f"{part.iloc[0]:.0f} % du total national pour cet indicateur.")
    with c2:
        section(f"{titre} — par secteur")
        d = (df_annee.groupby("secteur_industriel")[col].sum()
             .sort_values(ascending=False).reset_index())
        st.plotly_chart(barres_h(d, col, "secteur_industriel"), use_container_width=True)

    # Eclairage automatique sur le poids du secteur minier (calcul sur les donnees)
    mine = df_annee[df_annee["secteur_industriel"] == "Transformation minière"]
    ca_t = df_annee["chiffre_affaires_milliards_gnf"].sum()
    ex_t = df_annee["exportations_milliards_gnf"].sum()
    if ca_t > 0 and ex_t > 0 and not mine.empty:
        p_ca = mine["chiffre_affaires_milliards_gnf"].sum() / ca_t * 100
        p_ex = mine["exportations_milliards_gnf"].sum() / ex_t * 100
        st.info(f"**Éclairage — poids du secteur minier ({annee_choisie}).** "
                f"La transformation minière représente {p_ca:.0f} % du chiffre "
                f"d'affaires industriel mais {p_ex:.0f} % des exportations : "
                "le secteur est nettement plus tourné vers l'extérieur que la "
                "moyenne de l'industrie guinéenne.")

    section(f"Évolution · {annees[0]}–{annees[-1]}")
    d = df_filtre.groupby("annee")[col].sum().reset_index()
    fig = px.line(d, x="annee", y=col, markers=True)
    fig.update_traces(line=dict(color=BAUXITE, width=2),
                      marker=dict(size=9, color=BAUXITE,
                                  line=dict(width=2, color=SURFACE)),
                      hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title=titre)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(styliser(fig, 320, grille_y=True), use_container_width=True)

    section(f"Croisement {'région' if champ_geo=='region' else 'région naturelle'} × secteur")
    # min_count=1 : une case sans aucune valeur renseignee reste vide (NaN)
    # au lieu d'etre comptee comme un zero, ce qui fausserait la lecture.
    pivot = (df_annee.groupby([champ_geo, "secteur_industriel"])[col]
             .sum(min_count=1).unstack())
    texte = np.where(pivot.isna(), "n.d.",
                     pivot.round(0).fillna(0).astype(int).astype(str).values)
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale=RAMPE_BAUXITE)
    fig.update_traces(text=texte, texttemplate="%{text}", textfont=dict(size=10),
                      hovertemplate="<b>%{y}</b><br>%{x}<br>%{text}<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title="",
                      coloraxis_colorbar=dict(title="", thickness=10))
    st.plotly_chart(styliser(fig, 420), use_container_width=True)
    st.caption(f"Lecture : plus la case est foncée, plus « {titre} » est élevé. "
               "n.d. : donnée non disponible (valeur manquante dans l'entrepôt, "
               "voir la page Qualité des données).")


# =====================================================================
#  PAGE : FICHE REGIONALE
# =====================================================================
def page_fiche():
    region = st.selectbox("Région", regions)
    entete(f"Fiche régionale · {region}",
           f"Profil industriel du territoire · année {annee_choisie}")

    d_reg = df[(df["region"] == region) & (df["annee"] == annee_choisie)]
    d_nat = df[df["annee"] == annee_choisie]

    cartes = []
    for c in [c for c in ["nb_entreprises_actives", "emploi_direct",
                          "chiffre_affaires_milliards_gnf",
                          "exportations_milliards_gnf"] if c in df.columns]:
        v = d_reg[c].sum()
        moy = d_nat.groupby("region")[c].sum().mean()
        e = (v - moy) / moy * 100 if moy else 0
        cls = "hausse" if e >= 0 else "baisse"
        cartes.append((LIBELLES[c], formater(v),
                       f'<span class="{cls}">{e:+.0f} %</span> vs moyenne nationale'))
    carte_kpi(cartes)

    c1, c2 = st.columns(2)
    with c1:
        section("Répartition du chiffre d'affaires par secteur")
        d = (d_reg.groupby("secteur_industriel")["chiffre_affaires_milliards_gnf"]
             .sum(min_count=1).dropna().sort_values(ascending=False).reset_index())
        st.plotly_chart(barres_h(d, "chiffre_affaires_milliards_gnf",
                                 "secteur_industriel"), use_container_width=True)
    with c2:
        section("Positionnement parmi les régions")
        d = (d_nat.groupby("region")["chiffre_affaires_milliards_gnf"]
             .sum().sort_values(ascending=False).reset_index())
        d["mise_en_avant"] = np.where(d["region"] == region, BAUXITE, "#D9D6CE")
        fig = go.Figure(go.Bar(
            x=d["chiffre_affaires_milliards_gnf"], y=d["region"], orientation="h",
            marker=dict(color=d["mise_en_avant"], cornerradius=4),
            text=[nb_fr(v) for v in d["chiffre_affaires_milliards_gnf"]],
            texttemplate="%{text}", textposition="outside",
            textfont=dict(size=11, color=ENCRE_2), cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{text} Mds GNF<extra></extra>"))
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          xaxis_title="", yaxis_title="")
        fig = styliser(fig, 360)
        fig.update_xaxes(showticklabels=False, showgrid=False,
                         range=[0, float(d["chiffre_affaires_milliards_gnf"].max()) * 1.20])
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"La région {region} est mise en évidence.")

    section(f"Évolution · {region}")
    ind = st.radio("Indicateur", ["chiffre_affaires_milliards_gnf", "emploi_direct",
                                  "nb_entreprises_actives"],
                   format_func=lambda c: LIBELLES[c], horizontal=True)
    # Une annee dont une valeur sectorielle manque n'a pas de total fiable :
    # on ne la trace pas (au lieu d'afficher une chute artificielle).
    g = df[df["region"] == region].groupby("annee")[ind]
    d = pd.DataFrame({"total": g.sum(), "manquantes": g.apply(lambda x: x.isna().sum())})
    d.loc[d["manquantes"] > 0, "total"] = np.nan
    d = d.rename(columns={"total": ind}).reset_index()
    fig = px.line(d, x="annee", y=ind, markers=True)
    fig.update_traces(line=dict(color=BAUXITE, width=2),
                      marker=dict(size=9, color=BAUXITE,
                                  line=dict(width=2, color=SURFACE)),
                      hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title=LIBELLES[ind])
    fig.update_xaxes(dtick=1)
    st.plotly_chart(styliser(fig, 320, grille_y=True), use_container_width=True)
    inc = d.loc[d[ind].isna(), "annee"].tolist()
    if inc:
        st.caption("Total non calculé pour " + ", ".join(str(a) for a in inc) +
                   " : au moins une valeur sectorielle est manquante dans l'entrepôt "
                   "(voir la page Qualité des données). Le point n'est pas tracé "
                   "pour ne pas suggérer une baisse qui n'existe pas.")


# =====================================================================
#  PAGE : DIMENSIONS COMPLEMENTAIRES
# =====================================================================
def page_dimensions():
    entete("Dimensions complémentaires",
           "Emploi, production, énergie et environnement, conformité et maturité")

    dim = st.selectbox("Dimension", list(DIMENSIONS.keys()))
    for col in DIMENSIONS[dim]:
        taux = df[col].notna().mean() * 100
        section(LIBELLES[col])
        if taux < 50:
            st.warning(f"Indicateur peu renseigné — {taux:.0f} % des observations "
                       "disponibles. Résultats donnés à titre indicatif.")
        d = (df_filtre.groupby("region")[col].mean().dropna()
             .sort_values(ascending=False).reset_index())
        if d.empty:
            st.info("Aucune donnée disponible pour cette sélection.")
            continue
        st.plotly_chart(barres_h(d, col, "region", hauteur=300, decimales=1),
                        use_container_width=True)
        st.caption("Moyenne par région sur la période 2021-2025.")


# =====================================================================
#  PAGE : ANALYSE AVANCEE
# =====================================================================
@st.cache_data
def segmentation(data):
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    # Variables identiques a celles decrites en 4.3 du memoire
    feats = ["chiffre_affaires_milliards_gnf", "exportations_milliards_gnf",
             "investissement_milliards_gnf", "taux_utilisation_capacite_pct",
             "maturite_numerique_score_100"]
    agg = data.groupby("region").mean(numeric_only=True)
    km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(
        StandardScaler().fit_transform(agg[feats]))
    agg["cluster"] = km.labels_
    ordre = (agg.groupby("cluster")["chiffre_affaires_milliards_gnf"]
             .mean().sort_values(ascending=False).index.tolist())
    noms = ["Pôles industriels majeurs", "Régions intermédiaires",
            "Régions moins industrialisées"]
    agg["profil"] = agg["cluster"].map({c: noms[i] for i, c in enumerate(ordre)})
    return agg.reset_index()


def page_avancee():
    entete("Analyse avancée",
           f"Corrélations et segmentation · ensemble des données {annees[0]}–{annees[-1]}")

    section("Matrice de corrélation des indicateurs")
    ind = ["nb_entreprises_actives", "emploi_direct", "indice_production_industrielle",
           "chiffre_affaires_milliards_gnf", "valeur_ajoutee_milliards_gnf",
           "exportations_milliards_gnf", "investissement_milliards_gnf",
           "consommation_energie_mwh", "taux_utilisation_capacite_pct",
           "maturite_numerique_score_100"]
    ind = [c for c in ind if c in df.columns]
    if len(ind) < 2:
        st.info("Pas assez d'indicateurs numériques pour calculer des corrélations.")
        return
    corr = df[ind].corr().round(2)
    noms = [LIBELLES[c].split(" (")[0] for c in ind]
    corr.index, corr.columns = noms, noms
    texte_r = corr.apply(lambda col: col.map(
        lambda v: f"{v:.2f}".replace(".", ",").replace("-", "−"))).values
    fig = px.imshow(corr, aspect="auto",
                    color_continuous_scale=DIVERGENTE, zmin=-1, zmax=1)
    fig.update_traces(text=texte_r, texttemplate="%{text}", textfont=dict(size=10),
                      hovertemplate="<b>%{y}</b><br>%{x}<br>r = %{text}<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title="",
                      coloraxis_colorbar=dict(title="r", thickness=10))
    fig.update_xaxes(tickangle=-40)
    st.plotly_chart(styliser(fig, 560), use_container_width=True)
    st.info("Corrélations les plus fortes : chiffre d'affaires ↔ investissement "
            "(r = 0,90) et valeur ajoutée ↔ investissement (r = 0,87) — cohérent "
            "avec les résultats du chapitre 4 du mémoire.")

    section("Segmentation des régions (k-means, 3 profils)")
    _feats = ["chiffre_affaires_milliards_gnf", "exportations_milliards_gnf",
              "investissement_milliards_gnf", "taux_utilisation_capacite_pct",
              "maturite_numerique_score_100"]
    _absentes = [c for c in _feats if c not in df.columns]
    if _absentes:
        st.warning("Segmentation indisponible : variables absentes du jeu de "
                   "données — " + ", ".join(_absentes) + ".")
        return
    if df["region"].nunique() < 3:
        st.warning("Segmentation indisponible : au moins trois régions sont "
                   "nécessaires pour former trois profils.")
        return
    seg = segmentation(df)
    fig = px.scatter(seg, x="chiffre_affaires_milliards_gnf", y="emploi_direct",
                     color="profil", text="region", size="nb_entreprises_actives",
                     size_max=42, color_discrete_map=COULEURS_PROFIL,
                     category_orders={"profil": list(COULEURS_PROFIL)},
                     labels={"chiffre_affaires_milliards_gnf": "CA moyen (Mds GNF)",
                             "emploi_direct": "Emploi direct moyen"})
    fig.update_traces(textposition="top center",
                      textfont=dict(size=11, color=ENCRE_2),
                      marker=dict(line=dict(width=2, color=SURFACE)),
                      hovertemplate="<b>%{text}</b><br>CA %{x:,.0f} Mds GNF"
                                    "<br>Emploi %{y:,.0f}<extra></extra>")
    st.plotly_chart(styliser(fig, 500, legende=True, grille_y=True),
                    use_container_width=True)

    st.markdown("**Composition des trois profils**")
    st.dataframe(pd.DataFrame([
        {"Profil": p, "Régions": ", ".join(seg[seg.profil == p]["region"]),
         "CA moyen (Mds GNF)": nb_fr(seg[seg.profil == p]
                                     ["chiffre_affaires_milliards_gnf"].mean())}
        for p in COULEURS_PROFIL]), use_container_width=True, hide_index=True)


# =====================================================================
#  PAGE : QUALITE DES DONNEES
# =====================================================================
def page_qualite():
    entete("Qualité des données",
           "Complétude du jeu de données · volet gouvernance de l'observatoire")

    st.write("La gouvernance des données suppose de mesurer et de publier la qualité "
             "de l'information diffusée. Chaque indicateur est évalué sur les "
             f"{len(df)} observations du jeu de données.")

    def niveau(t):
        return "Bonne" if t >= 80 else ("À surveiller" if t >= 50 else "Insuffisante")

    q = pd.DataFrame([{"Indicateur": lib,
                       "Complétude (%)": round(df[c].notna().mean() * 100, 1),
                       "Manquantes": int(df[c].isna().sum())}
                      for c, lib in LIBELLES.items()])
    q["Niveau"] = q["Complétude (%)"].apply(niveau)
    q = q.sort_values("Complétude (%)", ascending=False)

    n_ins = (q["Niveau"] == "Insuffisante").sum()
    carte_kpi([
        ("Observations", formater(len(df)), "lignes du jeu de données"),
        ("Indicateurs suivis", str(len(LIBELLES)), "variables documentées"),
        ("Complétude moyenne", f"{nb_fr(q['Complétude (%)'].mean(), 1)} %", "toutes variables"),
        ("Indicateurs à renforcer", str(n_ins), "complétude inférieure à 50 %"),
    ])

    section("Complétude par indicateur")
    fig = px.bar(q, x="Complétude (%)", y="Indicateur", orientation="h",
                 color="Niveau", color_discrete_map=STATUT,
                 text=[nb_fr(v, 1) + " %" for v in q["Complétude (%)"]])
    fig.update_traces(texttemplate="%{text}", textposition="outside",
                      textfont=dict(size=11, color=ENCRE_2), cliponaxis=False,
                      marker=dict(cornerradius=4),
                      hovertemplate="<b>%{y}</b><br>%{x:.1f} %<extra></extra>")
    fig.update_layout(yaxis={"categoryorder": "total ascending"},
                      xaxis_title="", yaxis_title="", xaxis_range=[0, 112])
    fig.update_xaxes(showticklabels=False, showgrid=False)
    st.plotly_chart(styliser(fig, 560, legende=True), use_container_width=True)

    # Tableau entierement deplie (pas de defilement interne) et decimales a la francaise
    q_aff = q.assign(**{"Complétude (%)": [nb_fr(v, 1) for v in q["Complétude (%)"]]})
    st.dataframe(q_aff, use_container_width=True, hide_index=True,
                 height=35 * (len(q_aff) + 1) + 3,
                 column_config={"Complétude (%)": st.column_config.TextColumn(
                     "Complétude (%)", width="small")})

    # Le texte des limites est CALCULE, jamais fige : il suit toujours le
    # nombre reellement affiche dans la carte « Indicateurs a renforcer ».
    faibles = q[q["Niveau"] == "Insuffisante"].sort_values("Complétude (%)")
    if len(faibles):
        liste = ", ".join(f"{(lambda t: t[0].lower() + t[1:])(r['Indicateur'].split(' (')[0])} "
                          f"({nb_fr(r['Complétude (%)'], 1)} %)"
                          for _, r in faibles.iterrows())
        accord = "indicateur présente" if len(faibles) == 1 else "indicateurs présentent"
        st.warning(f"**Limites identifiées** — {len(faibles)} {accord} une complétude "
                   f"inférieure à 50 % des observations : {liste}. Leur collecte devra "
                   "être renforcée avant toute exploitation décisionnelle. Ces "
                   "indicateurs n'étant produits par aucune source administrative "
                   "existante, leur alimentation suppose une collecte primaire auprès "
                   "des unités industrielles.")
    else:
        st.success("**Aucun indicateur** ne présente une complétude inférieure à 50 %.")

    a_surveiller = q[q["Niveau"] == "À surveiller"]
    if len(a_surveiller):
        liste2 = ", ".join(f"{(lambda t: t[0].lower() + t[1:])(r['Indicateur'].split(' (')[0])} "
                           f"({nb_fr(r['Complétude (%)'], 1)} %)"
                           for _, r in a_surveiller.iterrows())
        st.info(f"**À surveiller** — complétude comprise entre 50 et 80 % : {liste2}.")


# =====================================================================
#  PAGE : DONNEES & INDICATEURS
# =====================================================================
def page_donnees():
    entete("Données & indicateurs", "Consultation, export et définitions")

    section("Table des données")
    st.caption(f"{len(df_filtre)} lignes correspondant aux filtres actifs.")
    # Affichage lisible : libelles en clair, decimales a la francaise,
    # valeur manquante notee n.d. ; l'export CSV garde les noms de colonnes bruts.
    aff = df_filtre.copy()
    for c in LIBELLES:
        if c in aff.columns:
            dec = 0 if c in ("nb_entreprises_actives", "emploi_direct",
                             "accidents_travail_declares", "jours_arret_production") else 1
            aff[c] = [("n.d." if pd.isna(v) else nb_fr(float(v), dec)) for v in aff[c]]
    aff = aff.rename(columns={**LIBELLES, "annee": "Année", "region": "Région",
                              "region_naturelle": "Région naturelle",
                              "secteur_industriel": "Secteur"})
    aff = aff[[c for c in aff.columns if not c.startswith("id_")]]
    st.dataframe(aff, use_container_width=True, height=420, hide_index=True)
    st.download_button("⬇️  Télécharger ces données (CSV)",
                       df_filtre.to_csv(index=False).encode("utf-8"),
                       "donnees_observatoire.csv", "text/csv")

    section("Dictionnaire des variables")
    dico = pd.DataFrame([{"Variable": k, "Libellé": v} for k, v in LIBELLES.items()])
    st.dataframe(dico, use_container_width=True, hide_index=True,
                 height=35 * (len(dico) + 1) + 3)


# =====================================================================
#  ROUTAGE
# =====================================================================
{"Accueil": page_accueil, "L'Observatoire": page_presentation,
 "Analyse régionale & sectorielle": page_analyse, "Fiche régionale": page_fiche,
 "Dimensions complémentaires": page_dimensions, "Analyse avancée": page_avancee,
 "Qualité des données": page_qualite, "Données & indicateurs": page_donnees}[page]()

st.sidebar.divider()
st.sidebar.caption("Observatoire National de l'Industrie de Guinée  \n"
                   "Mémoire M2 SID — Ansoumane CONTE  \n"
                   "Université Alioune Diop de Bambey  \n"
                   "  \n"
                   "**Prototype académique** — ne constitue pas un site officiel "
                   "de la République de Guinée. Données de démonstration.")
