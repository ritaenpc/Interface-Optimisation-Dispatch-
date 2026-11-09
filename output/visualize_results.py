"""
Visualisation des résultats du placement de production.

Toutes les fonctions partagent la même charte graphique, calquée sur
`visualiser_production_batterie` (graphique de référence) :
  - mêmes couleurs par moyen de production ;
  - même axe du temps : barres centrées sur t·pas_h, étiquette « Temps [h] »,
    graduations identiques ;
  - mêmes libellés et même ordre de légende (fontsize, position) ;
  - mêmes tailles de titres, même style de grille, même taille de figure ;
  - même convention de signe : production / décharge batterie en positif,
    charge batterie et écrêtement en négatif.
"""
import os

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import MultipleLocator
import numpy as np


# =============================================================================
# Charte graphique commune
# =============================================================================
COULEUR_ENR       = "#31cc2e"
COULEUR_BAT       = "#c769f0"
COULEUR_YATE      = "#2471a3"
COULEUR_NEAOUA    = "#85c1e9"
COULEUR_CAT       = "#2c2c2c"
COULEUR_BRIDAGE   = "#d41313"
COULEUR_DEMANDE   = "red"
COULEUR_REFERENCE = "black"   # courbes de référence : ENR dispo, capacité max…

LABEL_ENR       = "ENR"
LABEL_DECHARGE  = "Décharge batterie"
LABEL_CHARGE    = "Charge batterie"
LABEL_YATE      = "Yaté"
LABEL_NEAOUA    = "Néaoua"
LABEL_CAT       = "CAT"
LABEL_DEMANDE   = "Demande totale"
LABEL_ENR_DISPO = "ENR dispo"
LABEL_BRIDAGE   = "Écrêtement ENR"
LABEL_DEMANDE_DP  = "Demande DP+PRNC"
LABEL_DEMANDE_SLN = "Demande SLN"
STYLE_DEMANDE_DP  = dict(color="red", linestyle="--", linewidth=1.3)
STYLE_DEMANDE_SLN = dict(color="red", linestyle=":", linewidth=1.6)

LARGEUR_FIGURE  = 16
HAUTEUR_FIGURE  = 10
TAILLE_TITRE    = 11
TAILLE_SUPTITRE = 13
TAILLE_LEGENDE  = 7
FRACTION_BARRE  = 0.8
ALPHA_BRIDAGE   = 0.85
DPI             = 150
SEUIL_ACTIF     = 1e-9
STYLE_GRILLE    = dict(linestyle=":", linewidth=0.5, alpha=0.7)


# =============================================================================
# Fonctions utilitaires de style
# =============================================================================
def couleurs_thermiques(centrales):
    """Nuances d'orange pour les centrales thermiques (même règle partout)."""
    nb_ct = len(centrales)
    cmap = plt.colormaps["Oranges"]
    return {ct: cmap(0.30 + 0.70 * i / max(1, nb_ct - 1))
            for i, ct in enumerate(centrales)}


def palir(couleur, blend=0.20):
    """Éclaircit une couleur (utilisée pour la charge batterie par source)."""
    r, g, b, a = mcolors.to_rgba(couleur)
    return (r + (1 - r) * blend, g + (1 - g) * blend, b + (1 - b) * blend, a)


def _abscisses(nb_pas, pas_h):
    return np.arange(nb_pas) * pas_h


def _pas_graduation(duree_h):
    for pas in (0.25, 0.5, 1, 2, 3, 4, 6, 12, 24, 48, 168):
        if duree_h / pas <= 12:
            return pas
    return duree_h / 12


def configurer_axe_temps(ax, nb_pas, pas_h, afficher_label=True):
    """Axe du temps commun : barres centrées sur t·pas_h, mêmes graduations."""
    ax.set_xlim(-pas_h / 2, (nb_pas - 0.5) * pas_h)
    ax.xaxis.set_major_locator(MultipleLocator(_pas_graduation(nb_pas * pas_h)))
    if afficher_label:
        ax.set_xlabel("Temps [h]")


def appliquer_grille(ax, axe="y"):
    ax.grid(axis=axe, **STYLE_GRILLE)


def legende_ordonnee(ax, labels_voulus, loc="upper right"):
    """Affiche la légende dans l'ordre demandé, uniquement pour les labels tracés."""
    handles, labels = ax.get_legend_handles_labels()
    handles_map = dict(zip(labels, handles))
    retenus = [l for l in labels_voulus if l in handles_map]
    if retenus:
        ax.legend([handles_map[l] for l in retenus], retenus,
                  loc=loc, fontsize=TAILLE_LEGENDE)


def _actif(valeurs):
    return np.any(np.asarray(valeurs) > SEUIL_ACTIF)


def _sauvegarder(fig, chemin_sortie, suptitre, rect=None):
    fig.suptitle(suptitre, fontsize=TAILLE_SUPTITRE, fontweight="bold")
    # Les figures construites avec add_gridspec(hspace/wspace) gèrent déjà
    # leurs espacements : tight_layout n'est appliqué qu'aux autres.
    if not getattr(fig, "_gridspec_manuel", False):
        fig.tight_layout(rect=rect)
    if os.path.exists(chemin_sortie):
        os.remove(chemin_sortie)
    fig.savefig(chemin_sortie, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def _figure_trois_panneaux():
    fig = plt.figure(figsize=(LARGEUR_FIGURE, HAUTEUR_FIGURE))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.4, wspace=0.3)
    fig._gridspec_manuel = True
    return (fig, fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]),
            fig.add_subplot(gs[1, :]))


# =============================================================================
# Agrégation des résultats
# =============================================================================
def _serie(val, periodes):
    return np.array([val[t] for t in periodes], dtype=float)


def _somme_groupes(val, nb_groupes, periodes, *prefixe):
    """Somme sur les groupes r de val[(*prefixe, r, t)], pour chaque t."""
    return np.array([sum(val[(*prefixe, r, t)] for r in range(nb_groupes))
                     for t in periodes], dtype=float)


def _agreger_production(periodes, centrales, yate, neaoua, *,
                        prod_th_dp_val, prod_th_sln_val,
                        prod_cat_dp_val, prod_cat_sln_val,
                        prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
                        prod_neaoua_dp_val, prod_neaoua_sln_val,
                        enr_u_dp_val, enr_u_sln_val,
                        prod_bat_dp_val, prod_bat_sln_val,
                        p_charge_enr_val, p_charge_yate_val, p_charge_neaoua_val,
                        p_charge_th_val, p_charge_cat_val,
                        **_autres):
    """
    Renvoie trois « mix » (dict enr / bat / yate / neaoua / th{ct} / cat) :
      - dp     : production servant la demande DP+PRNC ;
      - sln    : production servant la demande SLN ;
      - charge : production servant à charger la batterie (bat = 0).
    """
    nb_yate, nb_neaoua = yate["nb_groupes"], neaoua["nb_groupes"]

    def th(val):
        return {ct: _somme_groupes(val, centrales[ct]["nb_groupes"], periodes, ct)
                for ct in centrales}

    dp = dict(
        enr=_serie(enr_u_dp_val, periodes),
        bat=_serie(prod_bat_dp_val, periodes),
        yate=_serie(prod_yate_dp_val, periodes),
        neaoua=_somme_groupes(prod_neaoua_dp_val, nb_neaoua, periodes),
        th=th(prod_th_dp_val),
        cat=_serie(prod_cat_dp_val, periodes),
    )
    sln = dict(
        enr=_serie(enr_u_sln_val, periodes),
        bat=_serie(prod_bat_sln_val, periodes),
        yate=_serie(prod_yate_sln_sous_val, periodes) + _serie(prod_yate_sln_sup_val, periodes),
        neaoua=_somme_groupes(prod_neaoua_sln_val, nb_neaoua, periodes),
        th=th(prod_th_sln_val),
        cat=_serie(prod_cat_sln_val, periodes),
    )
    charge = dict(
        enr=_serie(p_charge_enr_val, periodes),
        bat=np.zeros(len(periodes)),
        yate=_somme_groupes(p_charge_yate_val, nb_yate, periodes),
        neaoua=_somme_groupes(p_charge_neaoua_val, nb_neaoua, periodes),
        th=th(p_charge_th_val),
        cat=_serie(p_charge_cat_val, periodes),
    )
    return dp, sln, charge


def _somme_mix(*mixes):
    res = {cle: sum(m[cle] for m in mixes) for cle in ("enr", "bat", "yate", "neaoua", "cat")}
    res["th"] = {ct: sum(m["th"][ct] for m in mixes) for ct in mixes[0]["th"]}
    return res


def _mix_nul(nb_pas, centrales):
    z = np.zeros(nb_pas)
    return dict(enr=z, bat=z, yate=z, neaoua=z, cat=z, th={ct: z for ct in centrales})


# =============================================================================
# Tracé commun d'un panneau de mix de production
# =============================================================================
def _tracer_mix(ax, nb_pas, pas_h, centrales, couleurs_th, mix, demande, titre,
                enr_dispo=None, negatifs=(), demandes_detail=(), afficher_legende=False):
    """
    Empile la production (ENR en bas → CAT en haut), trace la demande (et
    éventuellement l'ENR disponible), puis empile en négatif les séries de
    `negatifs` = [(label, valeurs, couleur, alpha), ...].
    """
    x = _abscisses(nb_pas, pas_h)
    largeur = pas_h * FRACTION_BARRE

    series = [(LABEL_ENR,      mix["enr"],    COULEUR_ENR),
              (LABEL_DECHARGE, mix["bat"],    COULEUR_BAT),
              (LABEL_YATE,     mix["yate"],   COULEUR_YATE),
              (LABEL_NEAOUA,   mix["neaoua"], COULEUR_NEAOUA)]
    series += [(ct, mix["th"][ct], couleurs_th[ct]) for ct in centrales]
    series.append((LABEL_CAT, mix["cat"], COULEUR_CAT))

    bas = np.zeros(nb_pas)
    for label, val, couleur in series:
        ax.bar(x, val, width=largeur, bottom=bas, color=couleur, label=label)
        bas = bas + val

    demande = np.asarray(demande, dtype=float)
    ax.step(x, demande, where="mid", color=COULEUR_DEMANDE, linewidth=1.5, label=LABEL_DEMANDE)
    y_max = max(bas.max(), demande.max())

    labels_detail = []
    for label, val, style in demandes_detail:
        val = np.asarray(val, dtype=float)
        ax.step(x, val, where="mid", label=label, **style)
        y_max = max(y_max, val.max())
        labels_detail.append(label)

    if enr_dispo is not None:
        enr_dispo = np.asarray(enr_dispo, dtype=float)
        ax.step(x, enr_dispo, where="mid", color=COULEUR_REFERENCE, linewidth=1.2,
                label=LABEL_ENR_DISPO)
        y_max = max(y_max, enr_dispo.max())

    bas_neg = np.zeros(nb_pas)
    labels_neg = []
    for label, val, couleur, alpha in negatifs:
        val = np.asarray(val, dtype=float)
        if _actif(val):
            ax.bar(x, -val, width=largeur, bottom=-bas_neg, color=couleur, alpha=alpha,
                   label=label)
            labels_neg.append(label)
        bas_neg = bas_neg + val
    y_min = -1.2 * bas_neg.max() if bas_neg.max() > 0 else 0.0

    ax.set_ylim(y_min, max(y_max, 1e-6) * 1.10)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_title(titre, fontsize=TAILLE_TITRE)
    ax.set_ylabel("Production [MW]")
    configurer_axe_temps(ax, nb_pas, pas_h)
    appliquer_grille(ax)

    if afficher_legende:
        # Courbes, puis ordre inverse de l'empilement (CAT en haut → ENR en bas),
        # puis séries négatives (charge batterie, écrêtement)
        ordre = [(LABEL_DEMANDE, True)]
        ordre += [(l, True) for l in labels_detail]
        ordre += [(LABEL_ENR_DISPO, enr_dispo is not None)]
        ordre += [(label, _actif(val)) for label, val, _ in reversed(series)]
        legende_ordonnee(ax, [l for l, a in ordre if a] + labels_neg)

# =============================================================================
# Graphiques
# =============================================================================
def visualiser_production(
    nb_pas: int,
    pas_h: float,
    centrales: dict,
    yate: dict,
    neaoua: dict,
    prod_th_dp_val: dict,
    prod_th_sln_val: dict,
    prod_cat_dp_val: dict,
    prod_cat_sln_val: dict,
    prod_yate_dp_val: dict,
    prod_yate_sln_sous_val: dict,
    prod_yate_sln_sup_val: dict,
    prod_neaoua_dp_val: dict,
    prod_neaoua_sln_val: dict,
    enr_u_dp_val: dict,
    enr_u_sln_val: dict,
    enr_bridee_val: dict,          # variable de bridage explicite du modèle
    prod_bat_dp_val: dict,
    prod_bat_sln_val: dict,
    p_charge_val: dict,
    prod_enr: list,
    demande_dp: list,
    demande_sln: list,
    p_charge_enr_val: dict,
    p_charge_yate_val: dict,       # {(r, t): valeur}
    p_charge_neaoua_val: dict,     # {(r, t): valeur}
    p_charge_th_val: dict,         # {(ct, r, t): valeur}
    p_charge_cat_val: dict,
    chemin_sortie="mix_production.png"
):
    """
    Placement « net » : chaque moyen n'affiche que la part servant la demande ;
    la charge batterie est décomposée par source, en négatif.
    """
    periodes = range(nb_pas)
    dp, sln, charge = _agreger_production(
        periodes, centrales, yate, neaoua,
        prod_th_dp_val=prod_th_dp_val, prod_th_sln_val=prod_th_sln_val,
        prod_cat_dp_val=prod_cat_dp_val, prod_cat_sln_val=prod_cat_sln_val,
        prod_yate_dp_val=prod_yate_dp_val, prod_yate_sln_sous_val=prod_yate_sln_sous_val,
        prod_yate_sln_sup_val=prod_yate_sln_sup_val,
        prod_neaoua_dp_val=prod_neaoua_dp_val, prod_neaoua_sln_val=prod_neaoua_sln_val,
        enr_u_dp_val=enr_u_dp_val, enr_u_sln_val=enr_u_sln_val,
        prod_bat_dp_val=prod_bat_dp_val, prod_bat_sln_val=prod_bat_sln_val,
        p_charge_enr_val=p_charge_enr_val, p_charge_yate_val=p_charge_yate_val,
        p_charge_neaoua_val=p_charge_neaoua_val, p_charge_th_val=p_charge_th_val,
        p_charge_cat_val=p_charge_cat_val,
    )
    mix_total = _somme_mix(dp, sln)
    demande_tot = np.asarray(demande_dp, dtype=float) + np.asarray(demande_sln, dtype=float)
    bridage = _serie(enr_bridee_val, periodes)
    couleurs_th = couleurs_thermiques(centrales)

    # Charge batterie décomposée par source (couleur de la source, éclaircie)
    negatifs = [("Charge batt. ← ENR",    charge["enr"],    palir(COULEUR_ENR),    1.0),
                ("Charge batt. ← Yaté",   charge["yate"],   palir(COULEUR_YATE),   1.0),
                ("Charge batt. ← Néaoua", charge["neaoua"], palir(COULEUR_NEAOUA), 1.0)]
    negatifs += [(f"Charge batt. ← {ct}", charge["th"][ct], palir(couleurs_th[ct]), 1.0)
                 for ct in centrales]
    negatifs += [("Charge batt. ← CAT", charge["cat"], palir(COULEUR_CAT), 1.0),
                 (LABEL_BRIDAGE, bridage, COULEUR_BRIDAGE, ALPHA_BRIDAGE)]

    fig, ax_dp, ax_sln, ax_total = _figure_trois_panneaux()
    commun = dict(nb_pas=nb_pas, pas_h=pas_h, centrales=centrales, couleurs_th=couleurs_th)
    _tracer_mix(ax_dp,  mix=dp,  demande=demande_dp,  titre="Placement DP+PRNC", **commun)
    _tracer_mix(ax_sln, mix=sln, demande=demande_sln, titre="Placement SLN",     **commun)
    _tracer_mix(ax_total, mix=mix_total, demande=demande_tot, titre="Placement total",
                enr_dispo=prod_enr, negatifs=negatifs, afficher_legende=True, **commun)
    _sauvegarder(fig, chemin_sortie, "Placement optimal")


def visualiser_production_batterie(
    nb_pas: int,
    pas_h: float,
    centrales: dict,
    yate: dict,
    neaoua: dict,
    prod_th_dp_val: dict,
    prod_th_sln_val: dict,
    prod_cat_dp_val: dict,
    prod_cat_sln_val: dict,
    prod_yate_dp_val: dict,
    prod_yate_sln_sous_val: dict,
    prod_yate_sln_sup_val: dict,
    prod_neaoua_dp_val: dict,
    prod_neaoua_sln_val: dict,
    enr_u_dp_val: dict,
    enr_u_sln_val: dict,
    enr_bridee_val: dict,          # variable de bridage explicite du modèle
    prod_bat_dp_val: dict,
    prod_bat_sln_val: dict,
    p_charge_val: dict,
    prod_enr: list,
    demande_dp: list,
    demande_sln: list,
    p_charge_enr_val: dict,
    p_charge_yate_val: dict,       # {(r, t): valeur}
    p_charge_neaoua_val: dict,     # {(r, t): valeur}
    p_charge_th_val: dict,         # {(ct, r, t): valeur}
    p_charge_cat_val: dict,
    chemin_sortie="mix_production_batterie.png"
):
    """
    Graphique de référence. La puissance qu'une source utilise pour charger
    la batterie est réintégrée dans la barre de cette source
    (ex : Prony affiché = prony_dp + prony_sln + prony_batt). La charge
    totale de la batterie et l'écrêtement ENR sont affichés en négatif.
    """
    periodes = range(nb_pas)
    dp, sln, charge = _agreger_production(
        periodes, centrales, yate, neaoua,
        prod_th_dp_val=prod_th_dp_val, prod_th_sln_val=prod_th_sln_val,
        prod_cat_dp_val=prod_cat_dp_val, prod_cat_sln_val=prod_cat_sln_val,
        prod_yate_dp_val=prod_yate_dp_val, prod_yate_sln_sous_val=prod_yate_sln_sous_val,
        prod_yate_sln_sup_val=prod_yate_sln_sup_val,
        prod_neaoua_dp_val=prod_neaoua_dp_val, prod_neaoua_sln_val=prod_neaoua_sln_val,
        enr_u_dp_val=enr_u_dp_val, enr_u_sln_val=enr_u_sln_val,
        prod_bat_dp_val=prod_bat_dp_val, prod_bat_sln_val=prod_bat_sln_val,
        p_charge_enr_val=p_charge_enr_val, p_charge_yate_val=p_charge_yate_val,
        p_charge_neaoua_val=p_charge_neaoua_val, p_charge_th_val=p_charge_th_val,
        p_charge_cat_val=p_charge_cat_val,
    )
    # Répartition de la charge batterie entre les panneaux DP et SLN :
    #   DP  : charge venant de tous les moyens sauf la CAT ;
    #   SLN : charge venant de la CAT.
    charge_hors_cat = {**charge, "cat": np.zeros(nb_pas)}
    charge_cat      = {**_mix_nul(nb_pas, centrales), "cat": charge["cat"]}
    mix_dp    = _somme_mix(dp, charge_hors_cat)
    mix_sln   = _somme_mix(sln, charge_cat)
    mix_total = _somme_mix(dp, sln, charge)

    demande_tot   = np.asarray(demande_dp, dtype=float) + np.asarray(demande_sln, dtype=float)
    bridage       = _serie(enr_bridee_val, periodes)
    charge_totale = _serie(p_charge_val, periodes)
    couleurs_th   = couleurs_thermiques(centrales)

    negatifs = [(LABEL_CHARGE,  charge_totale, COULEUR_BAT,     1.0),
                (LABEL_BRIDAGE, bridage,       COULEUR_BRIDAGE, ALPHA_BRIDAGE)]

    demandes_detail = [(LABEL_DEMANDE_DP,  demande_dp,  STYLE_DEMANDE_DP),
                       (LABEL_DEMANDE_SLN, demande_sln, STYLE_DEMANDE_SLN)]

    fig, ax_dp, ax_sln, ax_total = _figure_trois_panneaux()
    commun = dict(nb_pas=nb_pas, pas_h=pas_h, centrales=centrales, couleurs_th=couleurs_th)
    _tracer_mix(ax_dp,  mix=mix_dp,  demande=demande_dp,  titre="Mix DP+PRNC", **commun)
    _tracer_mix(ax_sln, mix=mix_sln, demande=demande_sln, titre="Mix SLN",     **commun)
    _tracer_mix(ax_total, mix=mix_total, demande=demande_tot, titre="Mix total",
                enr_dispo=prod_enr, negatifs=negatifs, afficher_legende=True, **commun)
    _sauvegarder(fig, chemin_sortie, "Mix optimal")


def visualiser_activation_ct(
    nb_pas: int,
    pas_h: float,
    centrales: dict,
    yate: dict,
    neaoua: dict,
    u_th_val: dict,
    u_yate_val: dict,
    u_neaoua_val: dict,
    chemin_sortie="activation_groupes.png"
):
    periodes = range(nb_pas)

    matrices = {
        ct: np.array([[u_th_val[ct, r, t] for t in periodes]
                      for r in range(centrales[ct]["nb_groupes"])])
        for ct in centrales
    }
    matrices[LABEL_YATE]   = np.array([[u_yate_val[r, t]   for t in periodes]
                                       for r in range(yate["nb_groupes"])])
    matrices[LABEL_NEAOUA] = np.array([[u_neaoua_val[r, t] for t in periodes]
                                       for r in range(neaoua["nb_groupes"])])

    couleurs = couleurs_thermiques(centrales)
    couleurs[LABEL_YATE]   = COULEUR_YATE
    couleurs[LABEL_NEAOUA] = COULEUR_NEAOUA

    noms = list(matrices)
    nb   = len(noms)
    fig, axes = plt.subplots(nb, 1, figsize=(LARGEUR_FIGURE, max(8, nb * 1.6 + 1.5)),
                             sharex=True, squeeze=False)
    axes = axes[:, 0]

    for i, (ax, nom) in enumerate(zip(axes, noms)):
        mat  = matrices[nom]
        nb_r = mat.shape[0]
        cmap_bin = mcolors.LinearSegmentedColormap.from_list(
            f"cmap_{nom}", ["white", couleurs[nom]])
        # Même convention que les barres : la période t est centrée sur t·pas_h
        ax.imshow(mat, aspect="auto", cmap=cmap_bin, vmin=0, vmax=1,
                  extent=[-pas_h / 2, (nb_pas - 0.5) * pas_h, nb_r - 0.5, -0.5],
                  interpolation="none")
        for r in range(1, nb_r):
            ax.axhline(r - 0.5, color="gray", linewidth=0.5, linestyle=":")
        ax.set_yticks(range(nb_r))
        ax.set_yticklabels([f"G{r}" for r in range(nb_r)], fontsize=8)
        ax.set_title(f"Activation — {nom}", fontsize=TAILLE_TITRE, pad=3)
        ax.set_ylabel("Groupes")
        configurer_axe_temps(ax, nb_pas, pas_h, afficher_label=(i == nb - 1))
        appliquer_grille(ax, axe="x")
        # Taux d'activation affiché à droite de chaque ligne
        for r, taux in enumerate(mat.mean(axis=1)):
            ax.text(1.005, r, f"{taux:.0%}", transform=ax.get_yaxis_transform(),
                    va="center", ha="left", fontsize=8, color=couleurs[nom])

    _sauvegarder(fig, chemin_sortie, "État d'activation des groupes par centrale",
                 rect=[0, 0, 0.95, 0.97])


def visualiser_batterie(nb_pas, pas_h, stock_batt_val, p_charge_val, p_decharge_val,
                        batt, chemin_sortie="batterie.png"):
    """
    Même convention de signe que le mix de production :
    décharge en positif, charge en négatif.
    """
    periodes  = range(nb_pas)
    x         = _abscisses(nb_pas, pas_h)
    largeur   = pas_h * FRACTION_BARRE
    stock     = np.array([batt["stock_init"]] + [stock_batt_val[t] for t in periodes], dtype=float)
    charges   = _serie(p_charge_val, periodes)
    decharges = _serie(p_decharge_val, periodes)
    # Stock aux frontières des périodes (période t = [t-½, t+½]·pas_h)
    x_stock   = (np.arange(nb_pas + 1) - 0.5) * pas_h

    fig = plt.figure(figsize=(LARGEUR_FIGURE, HAUTEUR_FIGURE))
    gs  = fig.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.4)
    fig._gridspec_manuel = True
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    # --- État de charge ---
    ax1.fill_between(x_stock, stock, step="post", color=COULEUR_BAT, alpha=0.18)
    ax1.step(x_stock, stock, where="post", color=COULEUR_BAT, linewidth=1.5,
             label="État de charge")
    ax1.axhline(batt["e_max"], color=COULEUR_REFERENCE, linestyle="--", linewidth=1.2,
                label=f"Capacité max ({batt['e_max']:.0f} MWh)")
    ax1.axhline(0, color="black", linewidth=0.5)
    ax1.set_ylim(-0.05 * batt["e_max"], batt["e_max"] * 1.25)
    ax1.set_ylabel("Stock [MWh]")
    ax1.set_title("État de charge de la batterie", fontsize=TAILLE_TITRE)
    configurer_axe_temps(ax1, nb_pas, pas_h)
    appliquer_grille(ax1)
    legende_ordonnee(ax1, ["État de charge", f"Capacité max ({batt['e_max']:.0f} MWh)"])

    # --- Puissances ---
    ax2.bar(x, decharges, width=largeur, color=COULEUR_BAT, label=LABEL_DECHARGE)
    ax2.bar(x, -charges,  width=largeur, color=COULEUR_BAT, label=LABEL_CHARGE)
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_ylim(-batt["p_max"] * 1.2, batt["p_max"] * 1.2)
    ax2.set_ylabel("Puissance [MW]")
    ax2.set_title("Décharge (+) / Charge (−) de la batterie", fontsize=TAILLE_TITRE)
    configurer_axe_temps(ax2, nb_pas, pas_h)
    appliquer_grille(ax2)

    _sauvegarder(fig, chemin_sortie, "Fonctionnement de la batterie")


def comparer_placements(
    nb_pas: int,
    pas_h: float,
    centrales: dict,
    yate: dict,
    neaoua: dict,
    resultats_avec_batterie: dict,
    resultats_sans_batterie: dict,
    chemin_sortie: str = "comparaison_avec_sans_batterie.png",
):
    """
    Compare deux scénarios de placement (avec / sans batterie) et trace, pour
    chaque pas de temps, l'écart de puissance produite par moyen :

        écart(t) = puissance_sans_batterie(t) - puissance_avec_batterie(t)

    Chaque dictionnaire de résultats doit contenir les clés :
        prod_th_dp_val, prod_th_sln_val,
        prod_cat_dp_val, prod_cat_sln_val,
        prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
        prod_neaoua_dp_val, prod_neaoua_sln_val,
        enr_u_dp_val, enr_u_sln_val,
        prod_bat_dp_val, prod_bat_sln_val,
        p_charge_enr_val, p_charge_yate_val, p_charge_neaoua_val,
        p_charge_cat_val, p_charge_th_val

    La production comparée est la production RÉELLE de chaque moyen
    (demande DP + SLN + charge batterie), comme dans le graphique de
    référence. La batterie elle-même n'est pas représentée.
    """
    periodes = range(nb_pas)
    x = _abscisses(nb_pas, pas_h)
    largeur = pas_h * FRACTION_BARRE

    def _prod_par_moyen(res):
        mix = _somme_mix(*_agreger_production(periodes, centrales, yate, neaoua, **res))
        moyens = {LABEL_ENR: mix["enr"], LABEL_YATE: mix["yate"],
                  LABEL_NEAOUA: mix["neaoua"], LABEL_CAT: mix["cat"]}
        moyens.update(mix["th"])
        return moyens

    prod_avec = _prod_par_moyen(resultats_avec_batterie)
    prod_sans = _prod_par_moyen(resultats_sans_batterie)
    ecarts = {m: prod_sans[m] - prod_avec[m] for m in prod_avec}

    couleurs = couleurs_thermiques(centrales)
    couleurs.update({LABEL_ENR: COULEUR_ENR, LABEL_YATE: COULEUR_YATE,
                     LABEL_NEAOUA: COULEUR_NEAOUA, LABEL_CAT: COULEUR_CAT})

    # Même ordre d'empilement que le graphique de référence (sans la batterie)
    ordre_empilement = [LABEL_ENR, LABEL_YATE, LABEL_NEAOUA] + list(centrales) + [LABEL_CAT]

    fig, ax = plt.subplots(figsize=(LARGEUR_FIGURE, 8))
    bas_pos = np.zeros(nb_pas)
    bas_neg = np.zeros(nb_pas)
    for moyen in ordre_empilement:
        ecart = ecarts[moyen]
        if np.allclose(ecart, 0, atol=1e-6):
            continue  # aucun écart pour ce moyen
        partie_pos = np.clip(ecart, 0, None)
        partie_neg = np.clip(ecart, None, 0)
        ax.bar(x, partie_pos, width=largeur, bottom=bas_pos, color=couleurs[moyen], label=moyen)
        ax.bar(x, partie_neg, width=largeur, bottom=bas_neg, color=couleurs[moyen])
        bas_pos += partie_pos
        bas_neg += partie_neg

    marge = 0.10 * max(bas_pos.max(), -bas_neg.min(), 1e-6)
    ax.set_ylim(bas_neg.min() - marge, bas_pos.max() + marge)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Écart de production [MW]\n(sans batterie − avec batterie)")
    ax.set_title("Écart de production par moyen", fontsize=TAILLE_TITRE)
    configurer_axe_temps(ax, nb_pas, pas_h)
    appliquer_grille(ax)
    legende_ordonnee(ax, list(reversed(ordre_empilement)))

    _sauvegarder(fig, chemin_sortie, "Comparaison des placements avec et sans batterie")