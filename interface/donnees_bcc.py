"""
Lecture et rééchantillonnage des fichiers DATA-YYYYMMDD.csv (export brut du BCC,
1 valeur par minute, 1 colonne par équipement).

Module partagé, indépendant de tout script en particulier : utilisé par
interface_for_dispatch.py (import automatique des données ENR/demande + placement
réel du BCC pour comparaison), et peut aussi être utilisé par generer_bcc.py ou
tout autre outil d'analyse — sans dépendance entre ces scripts eux-mêmes.
"""

import re
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd


# ─── Date à partir du nom du fichier (ex : DATA-20260720.csv) ────────────────

def extraire_date_nom_fichier(nom_fichier: str):
    """Cherche un motif AAAAMMJJ dans le nom du fichier et renvoie la date réelle
    des données qu'il contient, ou None si aucun motif de ce type n'est trouvé.

    Le fichier DATA-AAAAMMJJ.csv contient en réalité les données du jour
    PRÉCÉDENT (de J-1 00:01 à J 00:00) : on retranche donc 1 jour à la date
    trouvée dans le nom du fichier."""
    nom = Path(nom_fichier).stem
    m = re.search(r'(\d{8})', nom)
    if not m:
        return None
    try:
        date_nom_fichier = datetime.strptime(m.group(1), '%Y%m%d').date()
    except ValueError:
        return None
    return date_nom_fichier - timedelta(days=1)


# ─── Définition des groupes de colonnes ───────────────────────────────────────

IGNORE_COLS = [
    'THERM PRNC UN1', 'THERM PRNC UN2',
    'THERM STG1', 'THERM STG2', 'THERM CTG1', 'THERM CTG2',
    'HYD THU', 'HYD WE PAALO', 'BIOGAZ',
    'THERM EEC',
    'EEC1', 'EEC2', 'T1', 'T2', 'U3',
]

CAT_COLS = [f'THERM CAT G{i}' for i in range(1, 12)]
PRONY_COLS = ['THERM PRONY G1', 'THERM PRONY G2']
NEPOUI_COLS = [f'THERM NEPOUI G{i}' for i in range(1, 5)]
TAC_COLS = ['THERM TAC1', 'THERM TAC2']
SINGLE_THERM_COLS = ['THERM CTSP']

YATE_COLS = [f'HYD YATE G{i}' for i in range(1, 5)]
NEAOUA_COLS = ['HYD NEAOUA G1', 'HYD NEAOUA G2']

ENR_COLS = [
    'EOLE YATE', 'EOLE KAFEATE', 'EOLE EEC', 'BEST', 'SOL EEC', 'SOL CASSIS',
    'SOL HELYOS BAY', 'SOL HELIO BOULOUPARIS 1', 'SOL HELIO BOULOUPARIS 2',
    'SOL HELIO TEMALA', 'SOL HELIO POPIDERY', 'SOL HELIO TAMOA',
    'SOL HELIOS MOINDOU', 'SOL FOCOLA', 'SOL OUATOM', 'SOL HELIO BAKIA',
    'SOL HELIO PIIN PATCH', 'SOL MOINDOU POWER', 'SOL OUACO', 'SOL KOTA BORE',
    'SOL HELIO MOINDAH', 'SOL HELIO KOUMAC', 'SOL HELIO PLAINE DES GAIACS',
    'SOL HELIO TONTOUTA', 'SOL KWITA WIJE', 'SOL TIABET', 'SOL KOUMAC POWER',
    'SOL HELIO POAVIDAPHTIA',
]

SLN_COLS = ['FD9', 'FD10', 'FD11', 'FM']
PRNC_COLS = ['GNI1', 'GNI2']

DP_COL = 'DP 150'

# Correspondance colonne(s) CSV BCC -> centrale de instances.py.
CSV_COLS_PAR_CENTRALE = {
    "Prony1":  ["THERM PRONY G1"],
    "Prony2":  ["THERM PRONY G2"],
    "Népoui1": ["THERM NEPOUI G1"],
    "Népoui2": ["THERM NEPOUI G2"],
    "Népoui3": ["THERM NEPOUI G3"],
    "Népoui4": ["THERM NEPOUI G4"],
    "TAC1":    ["THERM TAC1"],
    "TAC2":    ["THERM TAC2"],
    "CTSP":    ["THERM CTSP"],
}

# Couleurs utilisées pour les graphiques BCC (mix électrique, comparaison…)
COULEUR_ENR     = "#31cc2e"
COULEUR_YATE    = "#2471a3"
COULEUR_NEAOUA  = "#85c1e9"
COULEUR_CAT     = "#2c2c2c"
COULEUR_DEMANDE = "red"


# ─── Lecture + nettoyage + moyenne au pas choisi ──────────────────────────────

def charger_et_moyenner(chemin_csv: str, pas: str = '10min') -> pd.DataFrame:
    """Lit un CSV BCC brut (1 valeur/minute) et le rééchantillonne au pas donné
    (ex : '10min', '30min', '1h'), en moyenne, avec horodatage de fin de bloc."""
    chemin = Path(chemin_csv)
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin_csv}")

    df = pd.read_csv(chemin)
    df = df.drop(columns=[c for c in IGNORE_COLS if c in df.columns], errors='ignore')

    df['Horodatage'] = pd.to_datetime(df['Horodatage'], dayfirst=True, errors='coerce')

    cols_num = [c for c in df.columns if c != 'Horodatage']
    for c in cols_num:
        df[c] = pd.to_numeric(df[c], errors='coerce')  # 'null' -> NaN

    df = df.dropna(subset=['Horodatage']).sort_values('Horodatage')
    df = df.set_index('Horodatage')

    # label='right', closed='right' : chaque bloc est étiqueté par son horodatage
    # de fin, comme les données sources (relevé de 00:01 = fin de la 1ère minute,
    # relevé de J+1 00:00 = fin de la dernière minute du jour J).
    df_out = df.resample(pas, label='right', closed='right').mean(numeric_only=True)
    df_out = df_out.reset_index()

    return df_out


def filtrer_jour(df: pd.DataFrame, jour) -> pd.DataFrame:
    """Restreint df à la journée BCC de `jour` (de J 00:01 à J+1 00:00 inclus)."""
    debut = pd.Timestamp(jour)
    fin = debut + pd.Timedelta(days=1)
    return df[(df['Horodatage'] > debut) & (df['Horodatage'] <= fin)].reset_index(drop=True)


def sommer_colonnes(df: pd.DataFrame, cols) -> pd.Series:
    """Somme les colonnes présentes dans df parmi `cols`, NaN traités comme 0."""
    present = [c for c in cols if c in df.columns]
    return df[present].fillna(0).sum(axis=1) if present else pd.Series(0.0, index=df.index)