#pour lancer (depuis la racine du projet) : streamlit run interface/interface_for_dispatch.py

import streamlit as st
import datetime
import math
import sys, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.utils import construire_p_max_cat, construire_pas_indispo
from instances import CENTRALES, CAT, YATE, NEAOUA, COUT_BR, PRIX_ACHAT_SLN_ENR, E_CIN_MIN

# Import BCC (DATA-YYYYMMDD.csv) : module partagé src/donnees_bcc.py, indépendant
# de generer_bcc.py — les deux scripts n'ont pas besoin d'être au même endroit.
# Si le module est introuvable, l'import automatique est simplement désactivé
# (l'interface reste utilisable en saisie manuelle).
try:
    from donnees_bcc import (
        extraire_date_nom_fichier, charger_et_moyenner, filtrer_jour, sommer_colonnes,
        ENR_COLS, DP_COL, PRNC_COLS, SLN_COLS,
        YATE_COLS, NEAOUA_COLS, CAT_COLS, CSV_COLS_PAR_CENTRALE,
        COULEUR_ENR, COULEUR_YATE, COULEUR_NEAOUA, COULEUR_CAT, COULEUR_DEMANDE,
    )
    _IMPORT_BCC_DISPONIBLE = True
except ImportError:
    _IMPORT_BCC_DISPONIBLE = False

PANDAS_RULE_UI = {1/6: "10min", 0.5: "30min", 1.0: "1h"}


st.set_page_config(page_title="Dispatch Enercal", page_icon="⚡", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family:'Inter',sans-serif; color:#1a2332; font-size:13px; }
h1 { font-size:1.3rem !important; font-weight:600; color:#1a2332; margin-bottom:0.1rem !important; }
.stApp { background-color:#f4f6f9; color:#1a2332; }
.block-container { padding-top:1rem; padding-bottom:1.5rem; max-width:1500px; }
.sh {
    font-size:0.62rem; font-weight:700; letter-spacing:0.13em;
    text-transform:uppercase; color:#1a6fb5;
    border-bottom:2px solid #d0e4f7; padding-bottom:4px;
    margin-top:0.9rem; margin-bottom:0.5rem;
}
.horizon-info {
    font-family:'IBM Plex Mono',monospace; font-size:1.05rem;
    font-weight:600; color:#1a6fb5; letter-spacing:0.02em;
}
.tag-on  { background:#e6f4ea; color:#1e7e34; padding:1px 7px; border-radius:3px;
           font-size:0.68rem; font-family:'IBM Plex Mono',monospace; font-weight:600;
           border:1px solid #b7dfbf; }
.tag-off { background:#fdecea; color:#c0392b; padding:1px 7px; border-radius:3px;
           font-size:0.68rem; font-family:'IBM Plex Mono',monospace; font-weight:600;
           border:1px solid #f5c6c2; }
.tag-hs  { background:#fef9e7; color:#b7770d; padding:1px 7px; border-radius:3px;
           font-size:0.68rem; font-family:'IBM Plex Mono',monospace; font-weight:600;
           border:1px solid #f0d58c; }
.tag-indispo { background:#fdecea; color:#c0392b; padding:2px 8px; border-radius:3px;
               font-size:0.68rem; font-family:'IBM Plex Mono',monospace; font-weight:600;
               border:1px solid #f5c6c2; }

/* Bouton principal lancer */
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#1a6fb5,#1e88e5); color:white;
    font-family:'Inter',sans-serif; font-size:0.85rem; font-weight:600;
    border:none; border-radius:6px; padding:0.55rem 1.2rem;
    width:100%; transition:all 0.2s;
    box-shadow:0 2px 5px rgba(26,111,181,0.25);
}
.stButton > button[kind="primary"]:hover {
    background:linear-gradient(135deg,#1565c0,#1976d2);
    box-shadow:0 4px 10px rgba(26,111,181,0.35); transform:translateY(-1px);
}

/* Boutons +/- des number inputs — plus nets, mieux délimités */
div[data-testid="stNumberInput"] button {
    background: #f0f4fa !important;
    border: 1px solid #b8c9e0 !important;
    border-radius: 4px !important;
    color: #1a6fb5 !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    width: 28px !important;
    height: 28px !important;
    padding: 0 !important;
    margin: 0 2px !important;
    transition: background 0.15s, border-color 0.15s !important;
    box-shadow: 0 1px 2px rgba(26,111,181,0.08) !important;
}
div[data-testid="stNumberInput"] button:hover {
    background: #dbeafe !important;
    border-color: #1a6fb5 !important;
}
div[data-testid="stNumberInput"] button:active {
    background: #bfdbfe !important;
    transform: scale(0.96) !important;
}
div[data-testid="stNumberInput"] input {
    font-size:0.8rem; padding:4px 8px;
    border: 1px solid #b8c9e0;
    border-radius: 4px;
}

label { font-size:0.74rem !important; color:#4a5568 !important; font-weight:500 !important; }
div[data-testid="stSelectbox"] { font-size:0.8rem; }
div[data-testid="stExpander"] {
    background:#fff; border:1px solid #dde3ed;
    border-radius:7px; box-shadow:0 1px 3px rgba(0,0,0,0.04);
}
div[data-testid="stExpander"] summary { font-size:0.82rem; font-weight:600; color:#1a2332 !important; }
hr { border-color:#dde3ed; margin:0.6rem 0; }
div[data-testid="stAlert"] { border-radius:6px; font-size:0.8rem; }
div[data-testid="stMetricValue"] { font-size:1rem !important; color:#1a6fb5; font-weight:600; }
div[data-testid="stMetricLabel"] { font-size:0.7rem !important; color:#5a6a7e; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Données catalogue — valeurs issues de instances.py
# =============================================================================


BATT_OFF = {"p_max": 0.0, "p_min": 0.0, "e_max": 0.0, "e_min": 0.0,
            "stock_fin_min": 0.0, "stock_init": 0.0,
            "rampe_max": 0.0, "p_charge_init": 0.0, "p_decharge_init": 0.0,
            "rho": math.sqrt(0.89), "cout_cycle": 0.0, "cout_lissage": 0.0,
            "nb_cycles_max": 0}

def tag(on):
    return f'<span class="tag-on">ON</span>' if on else '<span class="tag-off">OFF</span>'

def selectbox_heure(label, key, horizon_h, pas_h=0.5):
    """Selectbox d'heure avec un pas aligné sur le pas de temps du modèle (10 min, 30 min, 1h…)."""
    nb_steps = int(round(horizon_h / pas_h))
    options = [round(i * pas_h, 6) for i in range(nb_steps + 1)]
    def fmt(v):
        hh = int(v)
        mm = int(round((v - hh) * 60))
        return f"{hh}h{mm:02d}"
    return st.selectbox(label, options, format_func=fmt, key=key)

def fmt_heure_tag(v):
    """Formate une heure en float (ex: 16.5) en 'HHhMM' (ex: '16h30'), pour l'affichage."""
    hh = int(v)
    mm = int(round((v - hh) * 60))
    return f"{hh}h{mm:02d}"

def heure_to_hhmm(v):
    """Formate une heure en float (ex: 16.5) en chaîne 'HH:MM' (ex: '16:30'),
    au format attendu par le modèle (cf. instances.py)."""
    hh = int(v)
    mm = int(round((v - hh) * 60))
    return f"{hh:02d}:{mm:02d}"

def saisir_indispos_groupe(nb_groupes, key_prefix, horizon_h, pas_h, max_plages=3):
    """UI de saisie des indisponibilités, par groupe, avec prise en charge de
    plusieurs plages par groupe (cf. construire_pas_indispo dans utils.py, qui
    accepte pour chaque groupe soit une plage unique, soit une liste de plages).

    Une plage laissée à 0h00 → 0h00 est considérée comme "non renseignée" et
    ignorée silencieusement. Toute autre plage où l'heure de fin n'est pas
    strictement après l'heure de début est signalée comme une erreur.

    Retourne (indispos, erreurs) où indispos = {r: [(h_deb_str, h_fin_str), ...]}.
    """
    indispos = {}
    erreurs = []
    for r in range(nb_groupes):
        r_aff = r + 1  # numérotation "fictive" côté affichage (1 à nb_groupes) ; le modèle indexe toujours à partir de 0
        st.markdown(
            f'<span style="font-size:0.76rem;color:#4a5568;font-weight:600;">Groupe {r_aff}</span>',
            unsafe_allow_html=True,
        )
        nb_plages = st.number_input(
            f"Nb de plages — G{r_aff}", min_value=0, max_value=max_plages, value=0,
            step=1, key=f"{key_prefix}_nbp_{r}",
        )
        plages_r = []
        for i in range(int(nb_plages)):
            ic1, ic2 = st.columns(2)
            with ic1:
                h_deb = selectbox_heure(f"G{r_aff} — plage {i + 1} début", f"{key_prefix}_deb_{r}_{i}", horizon_h, pas_h)
            with ic2:
                h_fin = selectbox_heure(f"G{r_aff} — plage {i + 1} fin",   f"{key_prefix}_fin_{r}_{i}", horizon_h, pas_h)
            if h_deb == 0 and h_fin == 0:
                continue
            if h_fin <= h_deb:
                erreurs.append(
                    f"G{r_aff} plage {i + 1} : heure de fin ({fmt_heure_tag(h_fin)}) "
                    f"doit être après l'heure de début ({fmt_heure_tag(h_deb)})"
                )
                st.error(f"⚠ G{r_aff} plage {i + 1} : l'heure de fin doit être après l'heure de début")
            else:
                plages_r.append((heure_to_hhmm(h_deb), heure_to_hhmm(h_fin)))
                st.markdown(
                    f'<span class="tag-indispo">G{r_aff} plage {i + 1} &nbsp;{fmt_heure_tag(h_deb)} → {fmt_heure_tag(h_fin)}</span>',
                    unsafe_allow_html=True,
                )
        if plages_r:
            indispos[r] = plages_r
    return indispos, erreurs

# =============================================================================
# En-tête
# =============================================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<h1 style="font-weight:700;">Analyse du placement journalier</h1>', unsafe_allow_html=True)

# =============================================================================
# Horizon
# =============================================================================

st.markdown('<div class="sh">⌛ Chargement des données, pas de temps & paramètres globaux</div>', unsafe_allow_html=True)

if not _IMPORT_BCC_DISPONIBLE:
    st.error(
        "⚠ Module `src/donnees_bcc.py` introuvable. C'est l'unique source de données "
        "de cette interface (plus de saisie manuelle) : place `donnees_bcc.py` dans le "
        "dossier `src/` du projet pour pouvoir continuer."
    )
    st.stop()

fu1, fu2 = st.columns([3, 1.2])
fichier_bcc = fu1.file_uploader(
    "📁 Fichier SCADA du placement BCC sur la journée — DATA-YYYYMMDD.csv ",
    type="csv", key="fichier_bcc",
)
seuil_bruit_mwh = fu2.number_input(
    "Seuil bruit capteur (MWh)", min_value=0.0, value=2.0, step=0.5, key="seuil_bruit_mwh",
    help="Si la production totale d'un groupe sur toute la journée est inférieure à ce "
         "seuil, elle est considérée comme du bruit capteur (groupe en réalité à "
         "l'arrêt) et ramenée à 0 sur tout l'horizon.",
)
import_bcc_actif = fichier_bcc is not None

hx1, hx2, hx3, hx4, hx5, hx6 = st.columns([1.2, 1.2, 2, 1.4, 1.4, 1.4])
pas_options = {"10 min": 1/6, "30 min": 0.5, "1 h": 1.0}
pas_label   = hx1.selectbox("Pas de temps", list(pas_options.keys()), index=0, key="pas_label")
PAS_H_ui    = pas_options[pas_label]

horizon_h = 24
hx2.markdown(
    '<div style="padding-top:22px;font-size:0.78rem;color:#5a6a7e;">'
    '<b>Horizon fixé à 24h</b><br></div>',
    unsafe_allow_html=True,
)
NB_PAS_ui   = int(horizon_h / PAS_H_ui)
hx3.markdown(f'<div style="padding-top:22px;"><span class="horizon-info">{NB_PAS_ui} pas</span>'
             f'<span style="color:#5a6a7e;font-size:0.78rem;margin-left:10px;">× {pas_label} = {horizon_h}h</span></div>',
             unsafe_allow_html=True)
COUT_BR_ui      = COUT_BR
PRIX_SLN_ENR_ui = PRIX_ACHAT_SLN_ENR
hx4.metric("Coût bridage ENR (F/MWh)", f"{COUT_BR_ui:,.0f}")
hx5.metric("Prix ENR pour SLN (F/MWh)", f"{PRIX_SLN_ENR_ui:,.0f}")
e_cin_min_reseau = hx6.number_input("E. cin. minimale sur le réseau", min_value=0.0, value= E_CIN_MIN, step=1.0)
E_CIN_MIN_ui = e_cin_min_reseau
st.markdown("---")

# =============================================================================
# Données d'entrée — exclusivement via import du fichier BCC ci-dessus
# =============================================================================

st.markdown('<div class="sh">📊 Visualisation des données d\'entrée : placement ENR et consommation électrique</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="color:#5a6a7e;font-size:0.8rem;margin-top:-4px;margin-bottom:8px;">'
    f'<b>Attention, deux biais affectent les données d\'entrée :</b>'
    f'<ul style="margin-top:4px;margin-bottom:0;padding-left:18px;">'
    f'<li><b>Disponibilité ENR :</b> à défaut de pouvoir donner à l\'optimiseur la disponibilité ENR effective de la journée, on lui donne le placement ENR qui a été réalisé. Cela biaise les résultats : impossible pour l\'optimiseur de placer plus d\'ENR que le placement réel, et donc impossible d\'analyser les décisions de limitation.</li>'
    f'<li><b>Écart placement / consommation :</b> dans les données SCADA, le placement total du BCC et la demande totale (DP + PRNC + SLN) ne correspondent pas exactement sur un pas de temps donné, l\'écart étant généralement de quelques MW. Pour obtenir des résultats interprétables, la demande de la SLN est utilisée comme variable d\'ajustement : elle est recalculée comme la différence entre la production totale et la demande de DP + PRNC. Ainsi, les 2 placements comparés répondent bien à une même demande. </li>'
    f'</ul>'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown("---")
def _zero_si_bruit_capteur(serie, pas_h, seuil_mwh, nom=None, filtres=None):
    """Si le volume total (MWh) d'un groupe sur tout l'horizon est en dessous du
    seuil, on considère qu'il s'agit d'un artefact de capteur (le groupe est en
    réalité resté à l'arrêt) et on ramène toute sa série à 0. Sinon, la série est
    renvoyée inchangée. Si `filtres` (liste) et `nom` sont fournis, le nom du
    groupe filtré y est ajouté pour information."""
    if sum(serie) * pas_h < seuil_mwh:
        if filtres is not None and nom is not None:
            filtres.append(nom)
        return [0.0] * len(serie)
    return serie


def _traiter_fichier_bcc(fichier, pas_h, nb_pas_attendu, seuil_bruit_mwh=2.0):
    """Lit le CSV BCC uploadé, le rééchantillonne au pas du modèle et en extrait :
      - les 3 séries d'entrée de l'optimiseur (ENR, DEMANDE_DP+PRNC, DEMANDE_SLN) ;
      - le placement réel du BCC par moyen de production, pour comparaison ultérieure.
    Un filtre anti-bruit capteur ramène à 0 tout groupe de production dont le volume
    total sur la journée reste sous `seuil_bruit_mwh` (les demandes DP/SLN ne sont
    pas concernées par ce filtre).
    Renvoie (enr_liste, dp_liste, sln_liste, placement_bcc, date_detectee, erreur, groupes_filtres).
    """
    import tempfile

    pas_pandas = PANDAS_RULE_UI.get(pas_h, "10min")
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(fichier.getvalue())
            chemin_tmp = tmp.name
        try:
            date_detectee = extraire_date_nom_fichier(fichier.name)
            df = charger_et_moyenner(chemin_tmp, pas=pas_pandas)
        finally:
            os.remove(chemin_tmp)
    except Exception as e:
        return None, None, None, None, None, f"Lecture du fichier impossible : {e}", None

    if date_detectee is None:
        return None, None, None, None, None, (
            "Impossible de détecter la date (motif AAAAMMJJ) dans le nom du fichier "
            f"« {fichier.name} »."
        ), None

    df = filtrer_jour(df, date_detectee)

    if len(df) != nb_pas_attendu:
        return None, None, None, None, date_detectee, (
            f"{len(df)} pas trouvés pour le {date_detectee.strftime('%d/%m/%Y')} au pas "
            f"{pas_pandas}, {nb_pas_attendu} attendus (données manquantes ou incomplètes "
            "dans le CSV pour cette journée)."
        ), None

    def s(cols):
        return sommer_colonnes(df, cols)

    groupes_filtres = []

    enr_liste = _zero_si_bruit_capteur(
        s(ENR_COLS).clip(lower=0).round(3).tolist(), pas_h, seuil_bruit_mwh, "ENR", groupes_filtres
    )
    dp_liste  = (s([DP_COL]) + s(PRNC_COLS)).round(3).tolist()
    sln_liste = s(SLN_COLS).round(3).tolist()

    placement_bcc = {
        "horodatage": df["Horodatage"].tolist(),
        "enr":    enr_liste,
        "dp":     dp_liste,
        "sln":    sln_liste,
        "yate":   _zero_si_bruit_capteur(s(YATE_COLS).round(3).tolist(), pas_h, seuil_bruit_mwh, "Yaté", groupes_filtres),
        "neaoua": _zero_si_bruit_capteur(s(NEAOUA_COLS).round(3).tolist(), pas_h, seuil_bruit_mwh, "Néaoua", groupes_filtres),
        "cat":    _zero_si_bruit_capteur(s(CAT_COLS).round(3).tolist(), pas_h, seuil_bruit_mwh, "CAT", groupes_filtres),
        "th_par_ct": {
            ct: _zero_si_bruit_capteur(
                (s(cols).round(3).tolist() if any(c in df.columns for c in cols) else [0.0] * len(df)),
                pas_h, seuil_bruit_mwh, ct, groupes_filtres,
            )
            for ct, cols in CSV_COLS_PAR_CENTRALE.items()
        },
        "date": date_detectee,
    }

    sln_liste = [
    round(
        placement_bcc["enr"][i]
        + placement_bcc["yate"][i]
        + placement_bcc["neaoua"][i]
        + placement_bcc["cat"][i]
        + sum(ct[i] for ct in placement_bcc["th_par_ct"].values())
        - placement_bcc["dp"][i],
        3,
    )
    for i in range(len(df))
]

    placement_bcc["sln"] = sln_liste

    return enr_liste, dp_liste, sln_liste, placement_bcc, date_detectee, None, groupes_filtres


enr_ui, dp_ui, sln_ui = [], [], []
_donnees_ok = False

if not import_bcc_actif:
    st.info("⬆ Importer un fichier DATA-YYYYMMDD.csv ci-dessus pour charger les données d'entrée.")
    st.session_state["bcc_placement"] = None
else:
    import pandas as pd
    (enr_bcc, dp_bcc, sln_bcc, placement_bcc,
     date_bcc, erreur_bcc, groupes_filtres_bcc) = _traiter_fichier_bcc(
        fichier_bcc, PAS_H_ui, NB_PAS_ui, seuil_bruit_mwh
    )

    if erreur_bcc:
        st.error(f"⚠ Import BCC : {erreur_bcc}")
        st.session_state["bcc_placement"] = None
    else:
        enr_ui, dp_ui, sln_ui = enr_bcc, dp_bcc, sln_bcc
        _donnees_ok = True
        st.session_state["bcc_placement"] = placement_bcc

        st.success(
            f"✓ Données BCC du {date_bcc.strftime('%d/%m/%Y')} chargées"
        )
        if groupes_filtres_bcc:
            st.info(
                f"🧹 Groupe(s) ramené(s) à 0 sur toute la journée (production totale "
                f"< {seuil_bruit_mwh:g} MWh, probable bruit capteur) : "
                f"**{', '.join(groupes_filtres_bcc)}**."
            )

        gc1, gc2 = st.columns(2)
        heures = [t.strftime("%H:%M") for t in placement_bcc["horodatage"]]
        with gc1:
            fig, ax = plt.subplots(figsize=(5, 1.8))
            ax.plot(heures, enr_bcc, color=COULEUR_ENR, linewidth=1.3)
            ax.fill_between(range(len(enr_bcc)), enr_bcc, color=COULEUR_ENR, alpha=0.25)
            ax.set_title("Placement ENR — BCC (MW)", fontsize=8, fontweight="600")
            ax.tick_params(labelsize=6, rotation=45)
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(8))
            ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        with gc2:
            fig, ax = plt.subplots(figsize=(5, 1.8))
            ax.plot(heures, dp_bcc,  color=COULEUR_DEMANDE, linewidth=1.3, linestyle="--", label="DP+PRNC")
            ax.plot(heures, sln_bcc, color=COULEUR_DEMANDE, linewidth=1.3, linestyle=":",  label="SLN")
            ax.set_title("Demande DP+PRNC / SLN (MW)", fontsize=8, fontweight="600")
            ax.tick_params(labelsize=6, rotation=45)
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(8))
            ax.legend(fontsize=6, loc="upper right")
            ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        # ── Alerte seuils minima techniques (DP / SLN) ─────────────────
        # DP+PRNC : si la demande DP passe sous le total des minima techniques
        # obligatoires (Prony + Népoui1 + Yaté), l'optimiseur est contraint de
        # placer ces moyens sur la SLN au lieu de la DP.
        # SLN : si la demande SLN passe sous le minimum technique du CAT,
        # l'optimiseur est contraint de placer le CAT sur la DP au lieu de la SLN.
        SEUIL_DP_MIN_TECH  = 52.0
        SEUIL_SLN_MIN_TECH = 54.0

        pas_dp_sous_seuil = [heures[t] for t, v in enumerate(dp_bcc) if v < SEUIL_DP_MIN_TECH]
        if pas_dp_sous_seuil:
            n_aff = pas_dp_sous_seuil[:8]
            suffixe = "…" if len(pas_dp_sous_seuil) > len(n_aff) else ""
            st.warning(
                f"⚠ Demande DP+PRNC sous {SEUIL_DP_MIN_TECH:g} MW (min. technique cumulé des "
                f"moyens dédiés à la DP) à {len(pas_dp_sous_seuil)} pas de temps : "
                f"{', '.join(n_aff)}{suffixe} "
            )

        pas_sln_sous_seuil = [heures[t] for t, v in enumerate(sln_bcc) if v < SEUIL_SLN_MIN_TECH]
        if pas_sln_sous_seuil:
            n_aff = pas_sln_sous_seuil[:8]
            suffixe = "…" if len(pas_sln_sous_seuil) > len(n_aff) else ""
            st.warning(
                f"⚠ Demande SLN sous {SEUIL_SLN_MIN_TECH:g} MW (min. technique de la CAT) à "
                f"{len(pas_sln_sous_seuil)} pas de temps : {', '.join(n_aff)}{suffixe} "
            )

st.markdown("---")

# =============================================================================
# Centrales thermiques
# =============================================================================

st.markdown('<div class="sh">🏭 Thermique</div>', unsafe_allow_html=True)
centrales_out = {}
CT_LISTE = list(CENTRALES.keys())
_errs_th = []

_lignes_centrales = [
    [ct for ct in CT_LISTE if ct.startswith("Prony")],
    [ct for ct in CT_LISTE if ct.startswith("Népoui")],
    [ct for ct in CT_LISTE if ct.startswith("TAC") or ct == "CTSP"],
]
# Toute centrale qui ne rentrerait dans aucun des groupes ci-dessus (nouvelle
# centrale ajoutée dans instances.py) est affichée sur une ligne supplémentaire,
# pour ne jamais la faire disparaître silencieusement.
_classees = {ct for ligne in _lignes_centrales for ct in ligne}
_reste = [ct for ct in CT_LISTE if ct not in _classees]
if _reste:
    _lignes_centrales.append(_reste)
_lignes_centrales = [ligne for ligne in _lignes_centrales if ligne]

for ligne in _lignes_centrales:
    cols = st.columns(len(ligne))
    for col, ct in zip(cols, ligne):
        p = CENTRALES[ct]
        nb_gr    = p["nb_groupes"]
        p_max_gr = p["p_max_groupe"]
        mt_gr    = p["min_technique_groupe"]
        ecin_gr  = p["e_cin_groupe"]
        cp       = p["cout_prop"]
        cd       = p["cout_demarrage"]
        ps       = p["prix_achat_sln"]
        with col:
            with st.expander(f"**{ct}** — {nb_gr} gr.", expanded=True):
                # Caractéristiques figées (données instances.py)
                fg1, fg2, fg3 = st.columns(3)
                fg1.metric("Pmax / gr (MW)", f"{p_max_gr:.1f}")
                fg2.metric("Min tech. / gr (MW)", f"{mt_gr:.1f}")
                fg3.metric("E. cin. / gr (MWs)", f"{ecin_gr:.1f}")
                fc1, fc2, fc3 = st.columns(3)
                fc1.metric("Coût prop. (F/MWh)", f"{cp:,.0f}")
                fc2.metric("Coût démarr. (F)", f"{cd:,.0f}")
                fc3.metric("Prix SLN (F/MWh)", f"{ps:,.0f}")

                # États initiaux
                u_init = {}
                st.markdown('<span style="font-size:0.9rem;color:#5a6a7e;font-weight:500;">Quels groupes sont actifs au pas de temps initial? </span>', unsafe_allow_html=True)
                gcols = st.columns(min(nb_gr, 5))
                for r in range(nb_gr):
                    d = bool(p["u_init"].get(r, 0))
                    with gcols[r % 5]:
                        u_init[r] = int(st.checkbox(f"G{r + 1}", value=d, key=f"u_{ct}_{r}"))
                        st.markdown(tag(bool(u_init[r])), unsafe_allow_html=True)

                # ── Indisponibilités partielles ───────────────────────────
                st.markdown("---")
                indispo_active = st.toggle("Indisponibilité", value=False, key=f"indispo_toggle_{ct}")
                indispos_ct = {}
                if indispo_active:
                    st.markdown(
                        '<span style="font-size:0.75rem;color:#5a6a7e;font-weight:500;">'
                        'Une ou plusieurs plages d\'indisponibilité par groupe '
                        '(laisser à 0 plage si aucune)</span>',
                        unsafe_allow_html=True,
                    )
                    indispos_ct, _err_ct = saisir_indispos_groupe(
                        nb_gr, f"indispo_{ct}", horizon_h, PAS_H_ui
                    )
                    _errs_th.extend(f"{ct} {e}" for e in _err_ct)

                    tous_hs = nb_gr > 0 and all(
                        any(pl[0] == "00:00" and pl[1] == heure_to_hhmm(horizon_h)
                            for pl in indispos_ct.get(r, []))
                        for r in range(nb_gr)
                    )
                    if tous_hs:
                        st.markdown('<span class="tag-hs">Hors service sur tout l\'horizon</span>', unsafe_allow_html=True)
                    st.markdown("---")

                centrales_out[ct] = {
                    "nb_groupes"           : nb_gr,
                    "p_max_groupe"         : p_max_gr,
                    "min_technique_groupe" : mt_gr,
                    "e_cin_groupe"         : ecin_gr,
                    "cout_prop"            : cp,
                    "cout_demarrage"       : cd,
                    "prix_achat_sln"       : ps,
                    "u_init"               : u_init,
                    "indispos"             : indispos_ct,
                }
                centrales_out[ct]["indispos_liste"] = construire_pas_indispo(
                    centrales_out[ct], NB_PAS_ui, PAS_H_ui
                )

# ── Validation thermiques ─────────────────────────────────────────────────────
if _errs_th:
    for _e in _errs_th: st.error(f"⚠ {_e}")
else:
    _cap_th = sum(cfg["nb_groupes"] * cfg["p_max_groupe"] for cfg in centrales_out.values())
    st.success(f"✓ Paramètres cohérents")

st.markdown("---")

# =============================================================================
# Hydraulique
# =============================================================================

st.markdown('<div class="sh">💧 Hydraulique</div>', unsafe_allow_html=True)
col_yate, col_neaoua = st.columns([2.2, 1.2], gap="medium")
_errs_hyd = []

# ── Yaté ─────────────────────────────────────────────────────────────────────
with col_yate:
    with st.expander(f"**Yaté** — {YATE['nb_groupes']} gr.", expanded=True):
        yate_nb_gr    = YATE["nb_groupes"]
        yate_p_max_gr = YATE["p_max_groupe"]
        yate_mt_gr    = YATE["min_technique_groupe"]
        yate_ecin_gr  = YATE["e_cin_groupe"]

        # Caractéristiques figées
        fg1, fg2, fg3 = st.columns(3)
        fg1.metric("Pmax / gr (MW)", f"{yate_p_max_gr:.1f}")
        fg2.metric("Min tech. / gr (MW)", f"{yate_mt_gr:.1f}")
        fg3.metric("E. cin. / gr (MWs)", f"{yate_ecin_gr:.1f}")
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Coût démarr. (F)", f"{YATE['cout_demarrage']:,.0f}")
        fc2.metric("Prix SLN sous. (F/MWh)", f"{YATE['prix_achat_sln_yate']:,.0f}")
        fc3.metric("Prix SLN hors sous. (F/MWh)", f"{YATE['prix_achat_sln_yate_hs']:,.0f}")

        st.markdown('<span style="font-size:0.9rem;color:#5a6a7e;font-weight:500;">Quels groupes sont actifs au pas de temps initial?</span>', unsafe_allow_html=True)
        gcols_y = st.columns(yate_nb_gr)
        u_yate  = {}
        for r in range(yate_nb_gr):
            with gcols_y[r]:
                u_yate[r] = int(st.checkbox(f"G{r + 1}", value=bool(YATE["u_init"].get(r, 1)), key=f"uy_{r}"))
                st.markdown(tag(bool(u_yate[r])), unsafe_allow_html=True)

        # ── Indisponibilités Yaté ─────────────────────────────────────
        st.markdown("---")
        indispo_yate_active = st.toggle("Indisponibilité", value=False, key="indispo_toggle_yate")
        indispos_yate = {}
        if indispo_yate_active:
            st.markdown(
                '<span style="font-size:0.75rem;color:#5a6a7e;font-weight:500;">'
                'Une ou plusieurs plages d\'indisponibilité par groupe '
                '(laisser à 0 plage si aucune)</span>',
                unsafe_allow_html=True,
            )
            indispos_yate, _err_yate = saisir_indispos_groupe(
                yate_nb_gr, "indispo_yate", horizon_h, PAS_H_ui
            )
            _errs_hyd.extend(f"Yaté {e}" for e in _err_yate)
        st.markdown("---")

        yate_capa_dispo = yate_nb_gr * yate_p_max_gr

        # Souscription SLN jour / nuit
        ys1, ys2, ys3 = st.columns(3)
        yate_sous_jour = ys1.number_input("Puissance souscrite par la SLN — jour (MW)",
                                          value=min(YATE["puissance_souscrite_sln_jour"], yate_capa_dispo),
                                          min_value=0.0, max_value=float(yate_capa_dispo),
                                          step=1.0, key="yate_sous_jour")
        
        yate_sous_nuit = ys2.number_input("Puissance souscrite par la SLN — nuit (MW)",
                                          value=min(YATE["puissance_souscrite_sln_nuit"], yate_capa_dispo),
                                          min_value=0.0, max_value=float(yate_capa_dispo),
                                          step=1.0, key="yate_sous_nuit")
    

        vente_hs_sln = ys3.toggle("Vente ENR à la SLN", value=True, key="vente_hs_sln")
        ys3.caption("Si cette option est activée, la vente de Yaté à la SLN au tarif ENR est autorisée.")
        
        



        y1, y2, y3 = st.columns(3)
        y1.metric("Puissance résérvée à la DP — jour (MW)",  f"{yate_capa_dispo - yate_sous_jour:.0f}")
        y1.caption("Heures de jour (6h–18h)")
        y2.metric("Puissance résérvée à la DP — nuit (MW)",  f"{yate_capa_dispo - yate_sous_nuit:.0f}")
        yate_cout_opp = y3.number_input("Coût opp. (F/MWh)", value=YATE["cout_opp"],
                                        step=100.0, key="yate_copp")
        y2.caption("Heures de nuit (18h–6h)")

    yate_out = {
        **YATE,
        "nb_groupes"                    : yate_nb_gr,
        "p_max_groupe"                  : yate_p_max_gr,
        "min_technique_groupe"          : yate_mt_gr,
        "e_cin_groupe"                  : yate_ecin_gr,
        "u_init"                        : u_yate,
        "puissance_souscrite_sln_jour"  : yate_sous_jour,
        "puissance_souscrite_sln_nuit"  : yate_sous_nuit,
        "cout_opp"                      : yate_cout_opp,
        "cout_demarrage"                : YATE["cout_demarrage"],
        "prix_achat_sln_yate"           : YATE["prix_achat_sln_yate"],
        "prix_achat_sln_yate_hs"        : YATE["prix_achat_sln_yate_hs"],
        "vente_hs_SLN"                  : int(vente_hs_sln),
        "indispos"                      : indispos_yate,
    }
    yate_out["indispos_liste"] = construire_pas_indispo(yate_out, NB_PAS_ui, PAS_H_ui)

# ── Néaoua ─────────────────────────────────────────────────────────────────────
with col_neaoua:
    with st.expander(f"**Néaoua** — {NEAOUA['nb_groupes']} groupes", expanded=True):
        nea_nb_gr    = NEAOUA["nb_groupes"]
        nea_p_max_gr = NEAOUA["p_max_groupe"]
        nea_mt_gr    = NEAOUA["min_technique_groupe"]
        nea_ecin_gr  = NEAOUA["e_cin_groupe"]

        # Caractéristiques figées
        fg1, fg2 = st.columns(2)
        fg1.metric("Pmax / gr (MW)", f"{nea_p_max_gr:.1f}")
        fg2.metric("Min tech. / gr (MW)", f"{nea_mt_gr:.1f}")
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("E. cin. / gr (MWs)", f"{nea_ecin_gr:.1f}")
        fc2.metric("Coût démarr. (F)", f"{NEAOUA['cout_demarrage']:,.0f}")
        fc3.metric("Prix SLN (F/MWh)", f"{NEAOUA['prix_achat_sln']:,.0f}")

        st.markdown('<span style="font-size:0.9rem;color:#5a6a7e;font-weight:500;">Quels groupes sont actifs au pas de temps initial?</span>', unsafe_allow_html=True)
        gcols_n  = st.columns(nea_nb_gr)
        u_neaoua = {}
        for r in range(nea_nb_gr):
            with gcols_n[r]:
                u_neaoua[r] = int(st.checkbox(f"G{r + 1}", value=bool(NEAOUA["u_init"].get(r, 1)), key=f"un_{r}"))
                st.markdown(tag(bool(u_neaoua[r])), unsafe_allow_html=True)

        # ── Indisponibilités Néaoua ───────────────────────────────────
        st.markdown("---")
        indispo_nea_active = st.toggle("Indisponibilité", value=False, key="indispo_toggle_nea")
        indispos_nea = {}
        if indispo_nea_active:
            st.markdown(
                '<span style="font-size:0.75rem;color:#5a6a7e;font-weight:500;">'
                'Une ou plusieurs plages d\'indisponibilité par groupe '
                '(laisser à 0 plage si aucune)</span>',
                unsafe_allow_html=True,
            )
            indispos_nea, _err_nea = saisir_indispos_groupe(
                nea_nb_gr, "indispo_nea", horizon_h, PAS_H_ui
            )
            _errs_hyd.extend(f"Néaoua {e}" for e in _err_nea)
        st.markdown("---")

        OPTIONS_COUT_OPP = {
            0.0: "Disponibilité importante (0 F/MWh)",
            10_000.0: "Disponibilité intermédiaire (10 000 F/MWh)",
            50_000.0: "Disponibilité faible / nulle (50 000 F/MWh)",
        }
        options = list(OPTIONS_COUT_OPP.keys())

        # Présélectionne la valeur par défaut si elle fait partie des options, sinon la première
        defaut = float(NEAOUA["cout_opp"])
        index_defaut = options.index(defaut) if defaut in options else 0

        neaoua_cout_opp = st.selectbox(
            "Coût opp. (F/MWh)",
            options=options,
            index=index_defaut,
            format_func=lambda v: OPTIONS_COUT_OPP[v],
            key="nea_cout_opp",
        )


        
        st.caption(
    "Disponibilité en eau importante : la production de Néaoua sera considérée comme gratuite.<br>"
    "Disponibilité intermédiaire : Néaoua sera mobilisé avant de monter Népoui au-delà des minimums techniques.<br>"
    "Disponibilité faible / nulle : Néaoua ne sera pas mobilisé / très ponctuellement pour éviter le démarrage d'un groupe",
    unsafe_allow_html=True,
)
    neaoua_out = {
        **NEAOUA,
        "nb_groupes"           : nea_nb_gr,
        "p_max_groupe"         : nea_p_max_gr,
        "min_technique_groupe" : nea_mt_gr,
        "e_cin_groupe"         : nea_ecin_gr,
        "u_init"               : u_neaoua,
        "cout_opp"             : neaoua_cout_opp,
        "cout_demarrage"       : NEAOUA["cout_demarrage"],
        "prix_achat_sln"       : NEAOUA["prix_achat_sln"],
        "indispos"             : indispos_nea,
    }
    neaoua_out["indispos_liste"] = construire_pas_indispo(neaoua_out, NB_PAS_ui, PAS_H_ui)

# ── Validation hydraulique ────────────────────────────────────────────────────
yate_capa = yate_out["nb_groupes"] * yate_out["p_max_groupe"]
if yate_out["puissance_souscrite_sln_jour"] > yate_capa:
    _errs_hyd.append(f"Yaté : souscription SLN jour ({yate_out['puissance_souscrite_sln_jour']:.0f} MW) > capacité totale ({yate_capa:.0f} MW)")
if yate_out["puissance_souscrite_sln_nuit"] > yate_capa:
    _errs_hyd.append(f"Yaté : souscription SLN nuit ({yate_out['puissance_souscrite_sln_nuit']:.0f} MW) > capacité totale ({yate_capa:.0f} MW)")
if _errs_hyd:
    for _e in _errs_hyd: st.error(f"⚠ {_e}")
else:
    _cap_hyd = (yate_out["nb_groupes"] * yate_out["p_max_groupe"]
                + neaoua_out["nb_groupes"] * neaoua_out["p_max_groupe"])
    st.success(f"✓ Paramètres cohérents")

st.markdown("---")

# =============================================================================
# CAT
# =============================================================================

st.markdown('<div class="sh">⚓ CAT</div>', unsafe_allow_html=True)
with st.expander("**CAT**", expanded=True):
    cat_nb_gr       = CAT["nb_groupes"]
    cat_p_max_gr    = CAT["p_max_groupe"]
    # cat_min_tech_ct = CAT["min_technique_ct"]
    cat_ecin_gr     = CAT["e_cin_groupe"]
    cat_prop        = CAT["cout_prop"]
    cat_enl         = CAT["prix_achat_enl"]
    cat_pmax_calc   = cat_nb_gr * cat_p_max_gr

    cc1, cc2, cc3, cc4, cc5, cc6 = st.columns(6, gap="medium")
    cc1.metric("Nb groupes", f"{cat_nb_gr}")
    cc2.metric("Puissance nominale (MW)", f"{cat_pmax_calc:.0f}")
    cc2.caption(f"{cat_nb_gr} × {cat_p_max_gr:.1f} MW/groupe")
    # cc3.metric("Min tech. CT (MW)", f"{cat_min_tech_ct:,.1f}")

    cat_min_tech_ct = cc3.number_input(
    "Minimum technique de la CAT (MW)",
    value=float(CAT["min_technique_ct"]),
    min_value=0.0, max_value=200.0,
    step=1.0, key="cat_min_tech_ct",
)
    
    
    cc4.metric("E. cin. / gr (MWs)", f"{cat_ecin_gr:.1f}")
    cc5.metric("Coût prop. (F/MWh)", f"{cat_prop:,.0f}")
    cc6.metric("Prix pour ENL (F/MWh)", f"{cat_enl:,.0f}")

    # ── Indisponibilités partielles ─────────────────────────────────────────
    st.markdown("---")
    indispo_cat_active = st.toggle("Indisponibilité", value=False, key="indispo_toggle_cat")
    indispos_cat = []
    if indispo_cat_active:
        st.markdown(
            '<span style="font-size:0.75rem;color:#5a6a7e;font-weight:500;">'
            'Plages d\'indisponibilité — chaque plage retire l\'équivalent d\'1 groupe '
            f'({cat_p_max_gr:.1f} MW) pendant l\'intervalle indiqué. Superposez plusieurs '
            'plages sur le même créneau pour retirer plusieurs groupes en même temps.</span>',
            unsafe_allow_html=True,
        )
        nb_plages_cat = st.number_input(
            "Nombre de plages d'indisponibilité", min_value=0,
            max_value=max(cat_nb_gr, 1), value=min(1, cat_nb_gr),
            step=1, key="nb_plages_cat",
        )
        _errs_cat = []
        for i in range(int(nb_plages_cat)):
            pc1, pc2 = st.columns(2)
            with pc1:
                h_deb = selectbox_heure(f"Plage {i + 1} — début", f"indispo_cat_deb_{i}", horizon_h, PAS_H_ui)
            with pc2:
                h_fin = selectbox_heure(f"Plage {i + 1} — fin",   f"indispo_cat_fin_{i}", horizon_h, PAS_H_ui)
            if h_deb == 0 and h_fin == 0:
                continue
            if h_fin <= h_deb:
                _errs_cat.append(
                    f"CAT plage {i + 1} : heure de fin ({fmt_heure_tag(h_fin)}) "
                    f"doit être après l'heure de début ({fmt_heure_tag(h_deb)})"
                )
                st.error(f"⚠ Plage {i + 1} : l'heure de fin doit être après l'heure de début")
            else:
                indispos_cat.append((heure_to_hhmm(h_deb), heure_to_hhmm(h_fin)))
                st.markdown(
                    f'<span class="tag-indispo">Plage {i + 1} &nbsp;{fmt_heure_tag(h_deb)} → {fmt_heure_tag(h_fin)}</span>',
                    unsafe_allow_html=True,
                )
    else:
        _errs_cat = []

cat_out = {
    "nb_groupes"     : cat_nb_gr,
    "p_max_groupe"   : cat_p_max_gr,
    "min_technique_ct" : cat_min_tech_ct,
    "e_cin_groupe"   : cat_ecin_gr,
    "cout_prop"      : cat_prop,
    "prix_achat_enl" : cat_enl,
    "indispos"       : indispos_cat,
}
cat_out["p_max_liste"] = construire_p_max_cat(cat_out, NB_PAS_ui, PAS_H_ui)

if _errs_cat:
    for _e in _errs_cat: st.error(f"⚠ {_e}")
else:
    p_max_min = min(cat_out["p_max_liste"]) if cat_out["p_max_liste"] else cat_pmax_calc
    if indispo_cat_active and indispos_cat and p_max_min < cat_pmax_calc:
        st.success(
            f"✓ Capacité nominale : {cat_pmax_calc:.0f} MW — "
            f"minimum pendant les indisponibilités : {p_max_min:.0f} MW"
        )
    else:
        st.success(f"✓ Paramètres cohérents")

st.markdown("---")

# =============================================================================
# Batterie : désactivée en permanence (exploitation sans batterie).
# =============================================================================

batt_out = BATT_OFF

# =============================================================================
# Validation + bouton
# =============================================================================

def _verifier_params():
    alertes = []
    if not _donnees_ok:           alertes.append("Données d'entrée invalides ou incomplètes")
    if _errs_th:                  alertes.append("Erreurs dans la section Thermique")
    if _errs_hyd:                 alertes.append("Erreurs dans la section Hydraulique")
    if _errs_cat:                 alertes.append("Erreurs dans la section CAT")
    if alertes:
        return alertes

    cap_max = (
        sum(cfg["nb_groupes"] * cfg["p_max_groupe"] for cfg in centrales_out.values())
        + yate_out["nb_groupes"] * yate_out["p_max_groupe"]
        + neaoua_out["nb_groupes"] * neaoua_out["p_max_groupe"]
        + cat_out["nb_groupes"] * cat_out["p_max_groupe"]
        + (max(enr_ui) if enr_ui else 0)
    )
    dem_max = (max(dp_ui) if dp_ui else 0) + (max(sln_ui) if sln_ui else 0)
    if cap_max < dem_max:
        alertes.append(f"Capacité totale ({cap_max:.0f} MW) insuffisante face à la demande max ({dem_max:.0f} MW)")

    min_fixe = 0.0
    if "Prony"   in centrales_out: min_fixe += centrales_out["Prony"]["min_technique_groupe"]
    if "Népoui1" in centrales_out: min_fixe += centrales_out["Népoui1"]["min_technique_groupe"]
    min_fixe += yate_out["nb_groupes"] * yate_out["min_technique_groupe"]
    dem_dp_max = max(dp_ui) if dp_ui else 0
    if min_fixe > dem_dp_max:
        alertes.append(f"Min technique obligatoire ({min_fixe:.0f} MW) > demande DP max ({dem_dp_max:.0f} MW)")

    return alertes


ac1, ac2 = st.columns([3, 1])
with ac1:
    alertes = _verifier_params()
    if alertes:
        for a in alertes: st.error(f"⚠ {a}")
    else:
        st.success("✓ Paramètres cohérents — prêt à lancer")
with ac2:
    lancer = st.button("▶  LANCER L'OPTIMISATION", type="primary")

if lancer:
    alertes = _verifier_params()
    if alertes:
        st.error("Corrigez les incohérences avant de lancer.")
    if not alertes:
        with st.spinner("Optimisation en cours…"):
            try:
                from src.model import resoudre_probleme
                from output.visualize_results import visualiser_production
                from output.create_table import exporter_resultats_excel

                enr_ui_run     = enr_ui
                demande_dp_ui  = dp_ui
                demande_sln_ui = sln_ui

                resultats = resoudre_probleme(
                    NB_PAS_ui, PAS_H_ui,
                    centrales_out, cat_out, yate_out, neaoua_out,
                    enr_ui_run, demande_dp_ui, demande_sln_ui,
                    COUT_BR_ui, PRIX_SLN_ENR_ui,
                    batt_out, E_CIN_MIN_ui
                )

                (
                    cout_total,
                    prod_th_dp_val, prod_th_sln_val, u_th_val, v_th_val,
                    prod_cat_dp_val, prod_cat_sln_val,
                    prod_yate_val, prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
                    u_yate_val, v_yate_val,
                    prod_neaoua_dp_val, prod_neaoua_sln_val,
                    u_neaoua_val, v_neaoua_val,
                    enr_u_dp_val, enr_u_sln_val, enr_bridee_val,
                    p_charge_enr_val, p_charge_th_val, p_charge_cat_val, p_charge_yate_val, p_charge_neaoua_val,
                    p_charge_val, p_decharge_val, u_charge_val, u_decharge_val,
                    stock_batt_val, prod_bat_dp_val, prod_bat_sln_val,
                    delta_charge_val, delta_decharge_val,
                ) = resultats

                visualiser_production(
                    NB_PAS_ui, PAS_H_ui,
                    centrales_out, yate_out, neaoua_out,
                    prod_th_dp_val, prod_th_sln_val,
                    prod_cat_dp_val, prod_cat_sln_val,
                    prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
                    prod_neaoua_dp_val, prod_neaoua_sln_val,
                    enr_u_dp_val, enr_u_sln_val, enr_bridee_val,
                    prod_bat_dp_val, prod_bat_sln_val,
                    p_charge_val, enr_ui_run, demande_dp_ui, demande_sln_ui,
                    p_charge_enr_val, p_charge_yate_val, p_charge_neaoua_val, p_charge_th_val, p_charge_cat_val
                )

                exporter_resultats_excel(
                    NB_PAS_ui, PAS_H_ui,
                    centrales_out, cat_out, yate_out, neaoua_out,
                    prod_th_dp_val, prod_th_sln_val,
                    prod_cat_dp_val, prod_cat_sln_val,
                    prod_yate_val, prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
                    prod_neaoua_dp_val, prod_neaoua_sln_val,
                    v_th_val, v_yate_val, v_neaoua_val,
                    enr_u_dp_val, enr_u_sln_val, enr_bridee_val,
                    enr_ui_run, COUT_BR_ui, PRIX_SLN_ENR_ui,
                    demande_dp_ui, demande_sln_ui,
                    stock_batt_val, p_charge_val, p_decharge_val,
                    batt_out,
                    p_charge_enr_val, p_charge_th_val, p_charge_cat_val, p_charge_yate_val, p_charge_neaoua_val,
                    prod_bat_dp_val, prod_bat_sln_val,
                    delta_charge_val, delta_decharge_val,
                )

                periodes = range(NB_PAS_ui)
                rho      = batt_out["rho"]

                mwh_enr_direct  = sum((enr_u_dp_val[t] + enr_u_sln_val[t]) * PAS_H_ui for t in periodes)
                mwh_enr_charge  = sum(p_charge_enr_val[t] * PAS_H_ui for t in periodes)
                mwh_enr_produit = mwh_enr_direct + mwh_enr_charge
                mwh_enr_bridage = sum(enr_bridee_val[t] * PAS_H_ui for t in periodes)
                mwh_bat_reseau  = sum(p_decharge_val[t] * rho * PAS_H_ui for t in periodes)
                mwh_yate_inj    = sum((prod_yate_dp_val[t] + prod_yate_sln_sous_val[t] + prod_yate_sln_sup_val[t]) * PAS_H_ui for t in periodes)
                mwh_yate_charge = sum(sum(p_charge_yate_val[r, t] for r in range(yate_out["nb_groupes"])) * PAS_H_ui for t in periodes)
                mwh_yate        = mwh_yate_inj + mwh_yate_charge
                mwh_neaoua_inj  = sum(sum(prod_neaoua_dp_val[r, t] + prod_neaoua_sln_val[r, t] for r in range(neaoua_out["nb_groupes"])) * PAS_H_ui for t in periodes)
                mwh_neaoua_charge = sum(sum(p_charge_neaoua_val[r, t] for r in range(neaoua_out["nb_groupes"])) * PAS_H_ui for t in periodes)
                mwh_neaoua      = mwh_neaoua_inj + mwh_neaoua_charge
                mwh_cat_inj     = sum((prod_cat_dp_val[t] + prod_cat_sln_val[t]) * PAS_H_ui for t in periodes)
                mwh_cat_charge  = sum(p_charge_cat_val[t] * PAS_H_ui for t in periodes)
                mwh_cat         = mwh_cat_inj + mwh_cat_charge
                mwh_th_par_ct_inj = {
                    ct: sum((prod_th_dp_val[ct, r, t] + prod_th_sln_val[ct, r, t]) * PAS_H_ui
                            for r in range(centrales_out[ct]["nb_groupes"]) for t in periodes)
                    for ct in centrales_out
                }
                mwh_th_par_ct_charge = {
                    ct: sum(p_charge_th_val[ct, r, t] * PAS_H_ui
                            for r in range(centrales_out[ct]["nb_groupes"]) for t in periodes)
                    for ct in centrales_out
                }
                mwh_th_par_ct = {ct: mwh_th_par_ct_inj[ct] + mwh_th_par_ct_charge[ct] for ct in centrales_out}
                mwh_th_total  = sum(mwh_th_par_ct.values())
                mwh_injecte   = (mwh_enr_direct + mwh_bat_reseau + mwh_yate_inj + mwh_neaoua_inj + mwh_cat_inj
                                 + sum(sum((prod_th_dp_val[ct, r, t] + prod_th_sln_val[ct, r, t]) * PAS_H_ui
                                          for r in range(centrales_out[ct]["nb_groupes"]) for t in periodes)
                                       for ct in centrales_out))
                mwh_besoins   = sum(demande_dp_ui[t] + demande_sln_ui[t] for t in periodes) * PAS_H_ui

                # ── Coût du mix électrique (prod injectée × coût prop) ────
                # ENR et hydro : coût opp / 0 ; thermiques et CAT : cout_prop
                cout_mix = (
                    sum(
                        centrales_out[ct]["cout_prop"] * mwh_th_par_ct[ct]
                        for ct in centrales_out
                    )
                    + cat_out["cout_prop"] * mwh_cat
                    + yate_out["cout_opp"] * mwh_yate
                    + neaoua_out["cout_opp"] * mwh_neaoua
                )

                mwh_enr_dp      = sum(enr_u_dp_val[t]  * PAS_H_ui for t in periodes)
                mwh_enr_sln     = sum(enr_u_sln_val[t] * PAS_H_ui for t in periodes)
                mwh_yate_dp     = sum(prod_yate_dp_val[t] * PAS_H_ui for t in periodes)
                mwh_yate_sln    = sum((prod_yate_sln_sous_val[t] + prod_yate_sln_sup_val[t]) * PAS_H_ui for t in periodes)
                mwh_neaoua_dp   = sum(sum(prod_neaoua_dp_val[r, t]  for r in range(neaoua_out["nb_groupes"])) * PAS_H_ui for t in periodes)
                mwh_neaoua_sln  = sum(sum(prod_neaoua_sln_val[r, t] for r in range(neaoua_out["nb_groupes"])) * PAS_H_ui for t in periodes)
                mwh_cat_dp      = sum(prod_cat_dp_val[t]  * PAS_H_ui for t in periodes)
                mwh_cat_sln     = sum(prod_cat_sln_val[t] * PAS_H_ui for t in periodes)
                mwh_th_par_ct_dp  = {
                    ct: sum(sum(prod_th_dp_val[ct, r, t]  for r in range(centrales_out[ct]["nb_groupes"])) * PAS_H_ui for t in periodes)
                    for ct in centrales_out
                }
                mwh_th_par_ct_sln = {
                    ct: sum(sum(prod_th_sln_val[ct, r, t] for r in range(centrales_out[ct]["nb_groupes"])) * PAS_H_ui for t in periodes)
                    for ct in centrales_out
                }
                mwh_dp_total    = sum(demande_dp_ui[t]  * PAS_H_ui for t in periodes)
                mwh_sln_total   = sum(demande_sln_ui[t] * PAS_H_ui for t in periodes)

                st.session_state["resultats_ok"] = True
                st.session_state["cout_total"]   = cout_total
                st.session_state["cout_mix"]     = cout_mix
                st.session_state["centrales_snapshot"] = centrales_out
                st.session_state["volumes"] = {
                    "mwh_enr_direct": mwh_enr_direct, "mwh_enr_charge": mwh_enr_charge,
                    "mwh_enr_produit": mwh_enr_produit, "mwh_enr_bridage": mwh_enr_bridage,
                    "mwh_enr_dp": mwh_enr_dp, "mwh_enr_sln": mwh_enr_sln,
                    "mwh_bat_reseau": mwh_bat_reseau,
                    "mwh_yate": mwh_yate, "mwh_yate_inj": mwh_yate_inj, "mwh_yate_charge": mwh_yate_charge,
                    "mwh_yate_dp": mwh_yate_dp, "mwh_yate_sln": mwh_yate_sln,
                    "mwh_neaoua": mwh_neaoua, "mwh_neaoua_inj": mwh_neaoua_inj, "mwh_neaoua_charge": mwh_neaoua_charge,
                    "mwh_neaoua_dp": mwh_neaoua_dp, "mwh_neaoua_sln": mwh_neaoua_sln,
                    "mwh_cat": mwh_cat, "mwh_cat_inj": mwh_cat_inj, "mwh_cat_charge": mwh_cat_charge,
                    "mwh_cat_dp": mwh_cat_dp, "mwh_cat_sln": mwh_cat_sln,
                    "mwh_cat_achat_enl": sum(prod_cat_dp_val[t] * PAS_H_ui for t in periodes),
                    "mwh_th_par_ct_inj": mwh_th_par_ct_inj, "mwh_th_par_ct_charge": mwh_th_par_ct_charge,
                    "mwh_th_par_ct": mwh_th_par_ct, "mwh_th_total": mwh_th_total,
                    "mwh_th_par_ct_dp": mwh_th_par_ct_dp, "mwh_th_par_ct_sln": mwh_th_par_ct_sln,
                    "mwh_injecte": mwh_injecte, "mwh_besoins": mwh_besoins,
                    "mwh_dp_total": mwh_dp_total, "mwh_sln_total": mwh_sln_total,
                }

                # Séries pas-à-pas (injection réseau uniquement, hors charge batterie),
                # utilisées pour la comparaison graphique BCC réel / optimisation.
                st.session_state["series_optim"] = {
                    "enr":    [enr_u_dp_val[t] + enr_u_sln_val[t] for t in periodes],
                    "yate":   [prod_yate_dp_val[t] + prod_yate_sln_sous_val[t] + prod_yate_sln_sup_val[t]
                               for t in periodes],
                    "neaoua": [sum(prod_neaoua_dp_val[r, t] + prod_neaoua_sln_val[r, t]
                                   for r in range(neaoua_out["nb_groupes"])) for t in periodes],
                    "cat":    [prod_cat_dp_val[t] + prod_cat_sln_val[t] for t in periodes],
                    "th_par_ct": {
                        ct: [sum(prod_th_dp_val[ct, r, t] + prod_th_sln_val[ct, r, t]
                                 for r in range(centrales_out[ct]["nb_groupes"])) for t in periodes]
                        for ct in centrales_out
                    },
                    "demande_dp":  list(demande_dp_ui),
                    "demande_sln": list(demande_sln_ui),
                }
                st.rerun()

            except ImportError as e:
                st.warning(f"Module non trouvé : {e}")
            except Exception as e:
                st.error(f"Erreur lors de l'optimisation : {e}")

# =============================================================================
# Résultats
# =============================================================================

if st.session_state.get("resultats_ok"):
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("Agg")

    st.markdown("---")
    st.markdown('<div class="sh"> 🔍 Résultats : Comparaison placement BCC / Optimisé</div>', unsafe_allow_html=True)


    st.info(
        "ℹ Si les résultats semblent incohérents (placements erratiques, productions "
        "négatives, etc.), cela signifie que le problème est infaisable. Parmi les raisons fréquentes : \n "
        "- la capacité des moyens de production disponibles ne permet pas de satisfaire la demande ;\n"
        "- la demande totale du système est inférieure à la somme des minimums "
        "techniques ;\n"
        "- les moyens disponibles ne permettent pas de satisfaire la contrainte "
        "d'énergie cinétique du réseau."
    )
    
    vol = st.session_state.get("volumes", {})

    # Couleurs par source de production — réutilisées pour les graphiques ET le
    # tableau de la section Comparaison ci-dessous.
    # Thermiques : rampe Oranges(0.30 → 1.00) sur nb_ct centrales
    ct_liste    = list(vol.get("mwh_th_par_ct_inj", {}).keys())
    nb_ct       = len(ct_liste)
    orange_cmap = plt.colormaps["Oranges"]
    nuances_th  = [orange_cmap(0.30 + 0.70 * i / max(nb_ct - 1, 1)) for i in range(nb_ct)]

    def rgba_to_hex(rgba):
        return "#{:02x}{:02x}{:02x}".format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))

    couleurs_th_hex = {ct: rgba_to_hex(nuances_th[i]) for i, ct in enumerate(ct_liste)}

    COLORS = {
        "ENR":    "#31cc2e",
        "Yate":   "#2471a3",
        "Neaoua": "#85c1e9",
        "CAT":    "#2c2c2c",
    }
    for ct in ct_liste:
        COLORS[ct] = couleurs_th_hex[ct]
    
    # =========================================================================
    # Comparaison placement réel du BCC / placement optimisé
    # =========================================================================

    placement_bcc = st.session_state.get("bcc_placement")
    series_optim  = st.session_state.get("series_optim")

    if placement_bcc and series_optim and vol:
        

        heures = [t.strftime("%H:%M") for t in placement_bcc["horodatage"]]
        n = len(heures)
        x = list(range(n))

        def _couches(source, ct_liste_local):
            couches = [
                ("ENR", source["enr"], COLORS["ENR"]),
                ("Yaté", source["yate"], COLORS["Yate"]),
                ("Néaoua", source["neaoua"], COLORS["Neaoua"]),
            ]
            for ct in ct_liste_local:
                couches.append((ct, source["th_par_ct"].get(ct, [0.0] * n), couleurs_th_hex.get(ct, "#999999")))
            couches.append(("CAT", source["cat"], COLORS["CAT"]))
            return couches

        couches_bcc   = _couches(placement_bcc, ct_liste)
        couches_optim = _couches(series_optim, ct_liste)

        demande_totale_bcc   = [placement_bcc["dp"][t] + placement_bcc["sln"][t] for t in range(n)]
        demande_totale_optim = [series_optim["demande_dp"][t] + series_optim["demande_sln"][t] for t in range(n)]
        y_max = max(
            max((sum(v[t] for _, v, _ in couches_bcc) for t in range(n)), default=0),
            max((sum(v[t] for _, v, _ in couches_optim) for t in range(n)), default=0),
            max(demande_totale_bcc, default=0), max(demande_totale_optim, default=0),
        ) * 1.10

        st.markdown("**Mix complet**")
        fig, (axb, axo) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        for ax, couches, demande_totale, titre in [
            (axb, couches_bcc,   demande_totale_bcc,   "Placement BCC"),
            (axo, couches_optim, demande_totale_optim, "Placement Optimisé"),
        ]:
            bas = [0.0] * n
            for label, valeurs, couleur in couches:
                if max(valeurs, default=0) <= 1e-6:
                    continue
                ax.bar(x, valeurs, bottom=bas, color=couleur, width=0.9, label=label, align="center")
                bas = [b + v for b, v in zip(bas, valeurs)]
            ax.step(x, demande_totale, where="post", color=COULEUR_DEMANDE, linewidth=1.8, label="Demande totale")
            ax.set_title(titre, fontsize=10, fontweight="600", loc="left")
            ax.set_ylabel("MW", fontsize=9)
            ax.set_ylim(0, y_max)
            ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.6)

        axo.set_xticks(x[::max(1, n // 12)])
        axo.set_xticklabels([heures[i] for i in x[::max(1, n // 12)]], rotation=30, ha="right", fontsize=8)
        handles, labels = axb.get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.04),
                   ncol=min(len(labels), 9), fontsize=7.5)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # ── Un graphique par moyen de production : BCC réel vs Optim superposés ──
        st.markdown("**Détail par moyen de production**")
        sources_detail_all = (
            [("ENR", "enr", COLORS["ENR"]), ("Yaté", "yate", COLORS["Yate"]),
             ("Néaoua", "neaoua", COLORS["Neaoua"])]
            + [(ct, ct, couleurs_th_hex.get(ct, "#999999")) for ct in ct_liste]
            + [("CAT", "cat", COLORS["CAT"])]
        )

        def _serie(source, cle):
            if cle in ("enr", "yate", "neaoua", "cat"):
                return source[cle]
            return source["th_par_ct"].get(cle, [0.0] * n)

        # On ne garde que les moyens pour lesquels au moins un des deux
        # placements (BCC réel ou Optim) n'est pas nul sur toute la journée.
        sources_detail = [
            (label, cle, couleur) for label, cle, couleur in sources_detail_all
            if max(_serie(placement_bcc, cle), default=0) > 1e-6
            or max(_serie(series_optim, cle), default=0) > 1e-6
        ]

        ncols = 4
        nrows = -(-len(sources_detail) // ncols)  # ceil
        fig2, axes = plt.subplots(nrows, ncols, figsize=(16, 2.6 * nrows), sharex=True)
        axes = axes.flatten() if nrows * ncols > 1 else [axes]
        xt_idx = x[::max(1, n // 6)]
        for i, (label, cle, couleur) in enumerate(sources_detail):
            ax = axes[i]
            serie_bcc   = _serie(placement_bcc, cle)
            serie_optim = _serie(series_optim, cle)
            ax.plot(x, serie_bcc,   color=couleur, linewidth=1.6, label="BCC réel")
            ax.plot(x, serie_optim, color=couleur, linewidth=1.6, linestyle="--", label="Optim")
            ax.set_title(label, fontsize=8.5, fontweight="600")
            ax.set_xticks(xt_idx)
            ax.set_xticklabels([heures[j] for j in xt_idx], rotation=45, ha="right", fontsize=6)
            ax.tick_params(axis="y", labelsize=6)
            ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.6)
        for j in range(len(sources_detail), len(axes)):
            axes[j].axis("off")
        handles2, labels2 = axes[0].get_legend_handles_labels()
        fig2.legend(handles2, labels2, loc="upper center", bbox_to_anchor=(0.5, 1.02),
                    ncol=2, fontsize=8, labelcolor="black")
        plt.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)

        # Tableau d'écarts de volumes (MWh) par source — mêmes moyens que les
        # graphiques ci-dessus (les deux placements nuls exclus) et même code
        # couleur.
        def _mwh(serie):
            return sum(serie) * PAS_H_ui

        couleur_par_source = {label: couleur for label, _, couleur in sources_detail}

        lignes_cmp = [
            (label, _mwh(_serie(placement_bcc, cle)), _mwh(_serie(series_optim, cle)))
            for label, cle, _ in sources_detail
        ]
        df_cmp = pd.DataFrame(lignes_cmp, columns=["Source", "BCC réel (MWh)", "Optimisation (MWh)"])

        # Ligne TOTAL = total de ce qui a été réellement produit
        total_bcc   = df_cmp["BCC réel (MWh)"].sum()
        total_optim = df_cmp["Optimisation (MWh)"].sum()
        df_cmp = pd.concat(
            [df_cmp, pd.DataFrame([{
                "Source": "TOTAL",
                "BCC réel (MWh)": total_bcc,
                "Optimisation (MWh)": total_optim,
            }])],
            ignore_index=True,
        )
        df_cmp["Écart (MWh)"] = df_cmp["Optimisation (MWh)"] - df_cmp["BCC réel (MWh)"]

        def _luminance(hex_color):
            h = hex_color.lstrip("#")
            r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
            return 0.299 * r + 0.587 * g + 0.114 * b

        def _colorier_cmp(row):
            if row["Source"] == "TOTAL":
                return ["font-weight:600;"] * len(row)
            bg = couleur_par_source.get(row["Source"], "#ffffff")
            fg = "color:white;" if _luminance(bg) < 140 else "color:#1a2332;"
            styles = [""] * len(row)
            styles[list(row.index).index("Source")] = f"background-color:{bg};{fg}"
            return styles

        st.dataframe(
            df_cmp.style.apply(_colorier_cmp, axis=1).format(
                {"BCC réel (MWh)": "{:,.1f}", "Optimisation (MWh)": "{:,.1f}", "Écart (MWh)": "{:+,.1f}"}),
            use_container_width=True, hide_index=True,
        )
    elif import_bcc_actif and not placement_bcc:
        st.info("Import BCC actif mais données invalides : la comparaison n'est pas disponible pour ce lancement.")

    # =========================================================================
    # Graphique du mix de production optimisé (journée entière)
    # =========================================================================

    if os.path.exists("mix_production.png"):
        st.markdown("**Détail du placement Optimisé**")

        from PIL import Image
        img = Image.open("mix_production.png")
        w, h = img.size
        # Rognage : on retire le bandeau supérieur (titre/légende) et toute la
        # moitié inférieure de la figure (panneau devenu inutile sans batterie).
        # Pourcentages ajustables si le cadrage ne tombe pas juste.
        HAUT_A_RETIRER = 0.08   # part de la hauteur totale retirée en haut
        BAS_CONSERVE   = 0.50   # part de la hauteur (après le bandeau) conservée
        y_top = int(h * HAUT_A_RETIRER)
        y_bot = y_top + int((h - y_top) * BAS_CONSERVE)
        img_rogne = img.crop((0, y_top, w, y_bot))
        st.image(img_rogne, use_container_width=True)

st.markdown("---")
CHEMIN_RESULTATS_XLSX = os.path.join(PROJECT_ROOT, "resultats_optimisation.xlsx")
_pied_col = st.columns([1, 1, 1])[1]
with _pied_col:
    if os.path.exists(CHEMIN_RESULTATS_XLSX):
        with open(CHEMIN_RESULTATS_XLSX, "rb") as _f:
            st.download_button(
                label="📄 Télécharger resultats_optimisation.xlsx",
                data=_f.read(),
                file_name="resultats_optimisation.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.caption(f"⚠ Fichier introuvable : {CHEMIN_RESULTATS_XLSX}")