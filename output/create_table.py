import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import os

# =============================================================================
# Helpers de style
# =============================================================================

def _apply(cell, fill_color=None, bold=False, italic=False,
           align="left", size=9, color="000000"):
    cell.font = Font(bold=bold, italic=italic, name="Arial", size=size, color=color)
    if fill_color:
        cell.fill = PatternFill("solid", start_color=fill_color)
    cell.alignment = Alignment(horizontal=align, vertical="center")


def _num(cell):
    cell.number_format = "#,##0.00"


def _num_int(cell):
    cell.number_format = "#,##0"


# =============================================================================
# Feuille Productions
# =============================================================================

def _feuille_productions(ws, nb_pas, pas_h, centrales, yate, neaoua,
                          prod_th_dp_val, prod_th_sln_val,
                          prod_cat_dp_val, prod_cat_sln_val,
                          prod_yate_val,
                          prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
                          prod_neaoua_dp_val, prod_neaoua_sln_val,
                          enr_u_dp_val, enr_u_sln_val, enr_bridee_val,
                          demande_dp, demande_sln, prod_enr,
                          stock_batt_val, p_charge_val, p_decharge_val, batt,
                          p_charge_enr_val, p_charge_th_val,
                          p_charge_cat_val, p_charge_yate_val, p_charge_neaoua_val):

    ws.title = "Productions (MW)"
    periodes = range(nb_pas)

    # ── Couleurs exactement alignées sur visualisation.py ────────────────────
    C_ENR     = "31CC2E"
    C_BAT_H   = "A8F0A8"
    C_YATE    = "2471A3"
    C_NEA     = "85C1E9"
    C_CAT     = "2C2C2C"
    C_ECR     = "D41313"
    C_DEM     = "4A235A"
    D_ENR     = "5AD657"   # palir(ENR)
    D_YATE    = "4F8DB5"   # palir(YATE)
    D_NEA     = "9DCDED"   # palir(NEAOUA)
    D_CAT     = "565656"   # palir(CAT)
    D_ECR     = "DC4242"   # palir(BRIDAGE)
    D_BAT     = "B9F3B9"   # palir(BAT)
    D_CHG     = "D6EAF8"   # bleu très clair charge→batt

    th_col = _couleurs_th(centrales)   # {ct: (hex_fonce, hex_pale)}

    STYLE = {
        None   : (C_DEM,   "EBF5FB"),
        "dem"  : (C_DEM,   "EBF5FB"),
        "cat"  : (C_CAT,   D_CAT),
        "catc" : (C_CAT,   D_CHG),
        "yate" : (C_YATE,  D_YATE),
        "yatec": (C_YATE,  D_CHG),
        "nea"  : (C_NEA,   D_NEA),
        "neac" : (C_NEA,   D_CHG),
        "enr"  : (C_ENR,   D_ENR),
        "enrc" : (C_ENR,   D_CHG),
        "ecr"  : (C_ECR,   D_ECR),
        "bat"  : (C_BAT_H, D_BAT),
    }

    # ── Définition des colonnes ───────────────────────────────────────────────
    cols = [("Heure", None, "[hh:mm]")]
    cols += [
        ("Demande totale", "dem", "[MW]"),
        ("Demande DP",     "dem", "[MW]"),
        ("Demande SLN",    "dem", "[MW]"),
    ]
    for ct in centrales:
        cols += [
            (f"{ct} – prod. totale",  "th",  "[MW]"),
            (f"{ct} – prod. directe", "th",  "[MW]"),
            (f"{ct} – DP",            "th",  "[MW]"),
            (f"{ct} – SLN",           "th",  "[MW]"),
            (f"{ct} – charge batt.",  "thc", "[MW]"),
        ]
    cols += [
        ("CAT – prod. totale",  "cat",  "[MW]"),
        ("CAT – prod. directe", "cat",  "[MW]"),
        ("CAT – DP",            "cat",  "[MW]"),
        ("CAT – SLN",           "cat",  "[MW]"),
        ("CAT – charge batt.",  "catc", "[MW]"),
    ]
    cols += [
        ("Yaté – prod. totale",  "yate",  "[MW]"),
        ("Yaté – prod. directe", "yate",  "[MW]"),
        ("Yaté – DP",            "yate",  "[MW]"),
        ("Yaté – SLN sous",      "yate",  "[MW]"),
        ("Yaté – SLN sup",       "yate",  "[MW]"),
        ("Yaté – charge batt.",  "yatec", "[MW]"),
    ]
    cols += [
        ("Néaoua – prod. totale",  "nea",  "[MW]"),
        ("Néaoua – prod. directe", "nea",  "[MW]"),
        ("Néaoua – DP",            "nea",  "[MW]"),
        ("Néaoua – SLN",           "nea",  "[MW]"),
        ("Néaoua – charge batt.",  "neac", "[MW]"),
    ]
    cols += [
        ("ENR dispo",             "enr",  "[MW]"),
        ("ENR – prod. totale",    "enr",  "[MW]"),
        ("ENR – prod. directe",   "enr",  "[MW]"),
        ("ENR – DP",              "enr",  "[MW]"),
        ("ENR – SLN",             "enr",  "[MW]"),
        ("ENR – charge batt.",    "enrc", "[MW]"),
        ("ENR écrêtée",           "ecr",  "[MW]"),
    ]
    cols += [
        ("Batterie – Stock",    "bat", "[MWh]"),
        ("Batterie – Charge",   "bat", "[MW]"),
        ("Batterie – Décharge", "bat", "[MW]"),
    ]

    # Mapping colonne (1-based) → (hex_header, hex_data) pour les thermiques
    col_th_style = {}
    for j, (lbl, grp, _) in enumerate(cols, 1):
        if grp in ("th", "thc"):
            ct_match = next((ct for ct in centrales if lbl.startswith(ct)), None)
            if ct_match:
                h, hp = th_col[ct_match]
                col_th_style[j] = (h, D_CHG if grp == "thc" else hp)

    nb_cols = len(cols)

    # ── En-têtes ──────────────────────────────────────────────────────────────
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=nb_cols)
    c = ws.cell(row=1, column=1, value="Résultats d'optimisation – Productions par source (MW)")
    _apply(c, bold=True, fill_color="1F4E79", align="center", size=11, color="FFFFFF")

    for j, (label, groupe, _) in enumerate(cols, start=1):
        c = ws.cell(row=2, column=j, value=label)
        if j in col_th_style:
            ch = col_th_style[j][0]
        else:
            ch, _ = STYLE.get(groupe, ("1F4E79", "FFFFFF"))
        _apply(c, bold=True, fill_color=ch, align="center", size=9, color="FFFFFF")

    for j, (_, _, unite) in enumerate(cols, start=1):
        c = ws.cell(row=3, column=j, value=unite)
        _apply(c, italic=True, align="center", size=8)

    # ── Index spéciaux ────────────────────────────────────────────────────────
    idx_ecr       = next(j for j, (l, g, _) in enumerate(cols, 1) if l == "ENR écrêtée")
    idx_bat_start = next(j for j, (l, g, _) in enumerate(cols, 1) if l == "Batterie – Stock")
    charge_col_indices = {j for j, (l, g, _) in enumerate(cols, 1) if g in ("thc", "catc", "yatec", "neac", "enrc")}

    # ── Données ───────────────────────────────────────────────────────────────
    from datetime import time as dt_time

    for t in periodes:
        data_row = t + 4
        minutes_tot = int(round(t * pas_h * 60)) % (24 * 60)
        heure_val = dt_time(minutes_tot // 60, minutes_tot % 60)

        # Charge batterie par source
        ch_enr    = p_charge_enr_val[t]
        ch_cat    = p_charge_cat_val[t]
        ch_yate   = sum(p_charge_yate_val[r, t]  for r in range(yate["nb_groupes"]))
        ch_neaoua = sum(p_charge_neaoua_val[r, t] for r in range(neaoua["nb_groupes"]))
        ch_th     = {ct: sum(p_charge_th_val[ct, r, t] for r in range(centrales[ct]["nb_groupes"]))
                     for ct in centrales}
        ch_total  = ch_enr + ch_cat + ch_yate + ch_neaoua + sum(ch_th.values())

        # ENR : bridage issu directement de la variable explicite du modèle
        enr_inj = enr_u_dp_val[t] + enr_u_sln_val[t]
        ecretee = enr_bridee_val[t]

        valeurs = [heure_val]
        valeurs += [demande_dp[t] + demande_sln[t], demande_dp[t], demande_sln[t]]

        for ct in centrales:
            nb_r = centrales[ct]["nb_groupes"]
            dp   = sum(prod_th_dp_val[ct, r, t]  for r in range(nb_r))
            sln  = sum(prod_th_sln_val[ct, r, t] for r in range(nb_r))
            inj  = dp + sln                       # prod. directe (réseau)
            tot  = inj + ch_th[ct]                # prod. totale (réseau + charge batt)
            valeurs += [tot, inj, dp, sln, ch_th[ct]]

        cat_dp  = prod_cat_dp_val[t]
        cat_sln = prod_cat_sln_val[t]
        cat_inj = cat_dp + cat_sln
        cat_tot = cat_inj + ch_cat
        valeurs += [cat_tot, cat_inj, cat_dp, cat_sln, ch_cat]

        yate_dp  = prod_yate_dp_val[t]
        yate_sln = prod_yate_sln_sous_val[t] + prod_yate_sln_sup_val[t]
        yate_inj = yate_dp + yate_sln
        yate_tot = yate_inj + ch_yate
        valeurs += [
            yate_tot, yate_inj,
            yate_dp,
            prod_yate_sln_sous_val[t],
            prod_yate_sln_sup_val[t],
            ch_yate,
        ]

        nb_r_n   = neaoua["nb_groupes"]
        nea_dp   = sum(prod_neaoua_dp_val[r, t]  for r in range(nb_r_n))
        nea_sln  = sum(prod_neaoua_sln_val[r, t] for r in range(nb_r_n))
        nea_inj  = nea_dp + nea_sln
        nea_tot  = nea_inj + ch_neaoua
        valeurs += [nea_tot, nea_inj, nea_dp, nea_sln, ch_neaoua]

        enr_tot = enr_inj + ch_enr   # prod. totale ENR utilisée
        valeurs += [
            prod_enr[t],    # ENR dispo
            enr_tot,        # prod. totale (injectée + stockée)
            enr_inj,        # prod. directe (injectée réseau)
            enr_u_dp_val[t],
            enr_u_sln_val[t],
            ch_enr,
            ecretee,
        ]

        valeurs += [
            stock_batt_val[t],
            ch_total,
            p_decharge_val[t],
        ]

        for j, val in enumerate(valeurs, start=1):
            c = ws.cell(row=data_row, column=j, value=val)
            groupe = cols[j - 1][1]
            if j == 1:
                c.number_format = "hh:mm"
                _apply(c, align="center")
            elif j == idx_ecr:
                _num(c); _apply(c, fill_color=D_ECR)
            elif j >= idx_bat_start:
                _num(c); _apply(c, fill_color=D_BAT)
            elif j in charge_col_indices:
                _num(c); _apply(c, fill_color=D_CHG)
            elif j in col_th_style:
                _num(c); _apply(c, fill_color=col_th_style[j][1])
            else:
                _, dc = STYLE.get(groupe, ("1F4E79", "F2F3F4"))
                _num(c); _apply(c, fill_color=dc)

    # ── Ligne TOTAL (MWh) ─────────────────────────────────────────────────────
    total_row = nb_pas + 4
    ws.cell(row=total_row, column=1, value="TOTAL (MWh)")
    _apply(ws.cell(row=total_row, column=1), bold=True, fill_color="D6E4F0", align="center", size=9)

    for j in range(2, nb_cols + 1):
        cl    = get_column_letter(j)
        lbl   = cols[j - 1][0]
        grp   = cols[j - 1][1]
        _, dc = STYLE.get(grp, ("1F4E79", "FFFFFF"))
        if lbl == "Batterie – Stock":
            c = ws.cell(row=total_row, column=j, value="—")
            _apply(c, bold=True, fill_color=D_BAT)
        else:
            c = ws.cell(row=total_row, column=j,
                        value=f"=SUM({cl}4:{cl}{total_row - 1})*{pas_h}")
            c.number_format = "#,##0.00"
            if j == idx_ecr:
                _apply(c, bold=True, fill_color=D_ECR)
            elif j >= idx_bat_start:
                _apply(c, bold=True, fill_color=D_BAT)
            elif j in charge_col_indices:
                _apply(c, bold=True, fill_color=D_CHG)
            elif j in col_th_style:
                _apply(c, bold=True, fill_color=col_th_style[j][1])
            else:
                _, dc = STYLE.get(grp, ("1F4E79", "F2F3F4"))
                _apply(c, bold=True, fill_color=dc)

    ws.column_dimensions["A"].width = 10
    for j in range(2, nb_cols + 1):
        ws.column_dimensions[get_column_letter(j)].width = 16
    ws.freeze_panes = "B4"


# =============================================================================
# Feuille Coûts
# =============================================================================

def _feuille_couts(ws, couts):
    ws.title = "Coûts (F)"

    sections = {
        "COÛT ENL": [
            ("__DETAIL_TH__",                     None,                    None,               None,                    None),
            ("__DETAIL_DEMARRAGE_TH__",            None,                    None,               None,                    None),
            ("Coût opportunité Yaté",              "cout_yate_opp",         "mwh_yate",        None,                    "tarif_yate_opp"),
            ("Coût démarrage Yaté",                "cout_yate_demarrage",   None,               "nb_demarrage_yate",    "tarif_demarrage_yate"),
            ("Coût opportunité Néaoua",            "cout_neaoua_opp",       "mwh_neaoua",      None,                    "tarif_neaoua_opp"),
            ("Coût démarrage Néaoua",              "cout_neaoua_demarrage", None,               "nb_demarrage_neaoua",  "tarif_demarrage_neaoua"),
            ("Achat CAT (DP)",                     "cout_achat_enl_cat",    "mwh_cat_dp",      None,                    "tarif_cat_enl"),
            ("Coût bridage ENR",                   "cout_bridage",          "mwh_ecretee",     None,                    "tarif_bridage"),
            ("Coût usure batterie",                "cout_batterie",         "mwh_bat_cycle",   None,                    "tarif_cycle"),
            ("Coût lissage batterie",              "cout_lissage",          None,               None,                    "tarif_lissage"),
        ],
        "COÛT SLN": [
            ("Coût marginal CAT (DP + SLN)",       "cout_cat_marginal",     "mwh_cat_tot",     None,                    "tarif_cat_marginal"),
            ("Achat thermique SLN",                "cout_achat_sln_th",     "mwh_th_sln",      None,                    "tarif_th_sln"),
            ("Achat Yaté SLN – souscription",      "cout_achat_sln_yate_sous", "mwh_yate_sln_sous", None,              "tarif_yate_sln"),
            ("Achat Yaté SLN – hors souscription", "cout_achat_sln_yate_sup",  "mwh_yate_sln_sup",  None,             "tarif_yate_sln_hs"),
            ("Achat Néaoua SLN",                   "cout_achat_sln_neaoua", "mwh_neaoua_sln",  None,                    "tarif_neaoua_sln"),
            ("Achat ENR SLN",                      "cout_achat_sln_enr",    "mwh_enr_sln",     None,                    "tarif_enr_sln"),
        ],
        "INDICATEURS": [
            ("Coût variable total du mix",   "cout_variable_mix",     "mwh_injecte_mix", None,                    None),
            ("Coût réel pour Enercal",           "cout_enl_reel",         "mwh_dp",          None,                    None),
        ],
    }
    couleurs_section = {"COÛT ENL": "1F4E79", "COÛT SLN": "145A32", "INDICATEURS": "6E2FA0"}

    ws.merge_cells("A1:E1")
    c = ws.cell(row=1, column=1, value="Détail des coûts d'optimisation")
    _apply(c, bold=True, fill_color="1F4E79", align="center", size=11, color="FFFFFF")

    for j, label in enumerate(["Composante", "Coût (F)", "Énergie (MWh)", "Nb démarrages", "Tarif (F/MWh)"], start=1):
        c = ws.cell(row=2, column=j, value=label)
        _apply(c, bold=True, fill_color="2E4057", align="center", size=9, color="FFFFFF")

    current_row = 3
    total_rows  = {}

    for section, items in sections.items():
        ws.merge_cells(start_row=current_row, start_column=1,
                       end_row=current_row, end_column=5)
        c = ws.cell(row=current_row, column=1, value=section)
        _apply(c, bold=True, fill_color=couleurs_section[section], align="left", size=10, color="FFFFFF")
        current_row += 1
        section_start = current_row

        for label, key_cout, key_mwh, key_nb_dem, key_tarif in items:
            # Détail prop. thermique par centrale
            if label == "__DETAIL_TH__":
                par_ct = couts.get("cout_th_prop_par_ct", {})
                mwh_ct = couts.get("mwh_th_par_ct", {})
                for ct in par_ct:
                    ws.cell(row=current_row, column=1, value=f"Coût prop. thermique {ct}")
                    _apply(ws.cell(row=current_row, column=1), size=9)
                    c_cout = ws.cell(row=current_row, column=2, value=par_ct[ct])
                    _num_int(c_cout)
                    c_mwh = ws.cell(row=current_row, column=3, value=mwh_ct.get(ct))
                    _num(c_mwh)
                    ws.cell(row=current_row, column=4, value="—")
                    _apply(ws.cell(row=current_row, column=4), align="center", size=9)
                    tarif_ct = couts.get("tarif_prop_par_ct", {}).get(ct)
                    c_tar = ws.cell(row=current_row, column=5,
                                    value=tarif_ct if tarif_ct is not None else "—")
                    if tarif_ct is not None:
                        _num_int(c_tar)
                    else:
                        _apply(c_tar, align="center", size=9)
                    current_row += 1
                continue

            # Détail démarrages thermiques par centrale
            if label == "__DETAIL_DEMARRAGE_TH__":
                par_ct   = couts.get("cout_th_demarrage_par_ct", {})
                nb_ct    = couts.get("nb_demarrage_par_ct", {})
                tarif_ct = couts.get("tarif_demarrage_par_ct", {})
                for ct in par_ct:
                    ws.cell(row=current_row, column=1, value=f"Coût démarrage {ct}")
                    _apply(ws.cell(row=current_row, column=1), size=9)
                    c_cout = ws.cell(row=current_row, column=2, value=par_ct[ct])
                    _num_int(c_cout)
                    ws.cell(row=current_row, column=3, value="—")
                    _apply(ws.cell(row=current_row, column=3), align="center", size=9)
                    c_nb = ws.cell(row=current_row, column=4, value=nb_ct.get(ct))
                    _num(c_nb)
                    c_tar = ws.cell(row=current_row, column=5,
                                    value=tarif_ct.get(ct, "—"))
                    if tarif_ct.get(ct) is not None:
                        _num_int(c_tar)
                    else:
                        _apply(c_tar, align="center", size=9)
                    current_row += 1
                continue

            ws.cell(row=current_row, column=1, value=label)
            _apply(ws.cell(row=current_row, column=1), size=9)

            c_cout = ws.cell(row=current_row, column=2, value=couts.get(key_cout, 0))
            _num_int(c_cout)

            # Col C : énergie (vide si ligne démarrage)
            c_mwh = ws.cell(row=current_row, column=3,
                            value=couts.get(key_mwh) if key_mwh else "—")
            if key_mwh and couts.get(key_mwh) is not None:
                _num(c_mwh)
            else:
                _apply(c_mwh, align="center", size=9)

            # Col D : nb démarrages (vide si ligne énergie)
            c_nb = ws.cell(row=current_row, column=4,
                           value=couts.get(key_nb_dem) if key_nb_dem else "—")
            if key_nb_dem and couts.get(key_nb_dem) is not None:
                _num(c_nb)
            else:
                _apply(c_nb, align="center", size=9)

            # Col E : tarif
            c_tar = ws.cell(row=current_row, column=5,
                            value=couts.get(key_tarif) if key_tarif else "—")
            if key_tarif and couts.get(key_tarif) is not None:
                _num_int(c_tar)
            else:
                _apply(c_tar, align="center", size=9)

            current_row += 1

        section_end = current_row - 1

        if section != "INDICATEURS":
            for col, label_tot in [(1, f"Sous-total {section}"), (2, None), (3, None), (4, None), (5, None)]:
                c = ws.cell(row=current_row, column=col)
                if col == 1:
                    c.value = label_tot
                elif col == 2:
                    c.value = f"=SUM(B{section_start}:B{section_end})"
                    _num_int(c)
                _apply(c, bold=True, fill_color="D5D8DC", size=9)
            total_rows[section] = current_row
            current_row += 2
        else:
            current_row += 1

    r_enl = total_rows["COÛT ENL"]
    r_sln = total_rows["COÛT SLN"]
    grand_row = current_row

    for col in range(1, 6):
        c = ws.cell(row=grand_row, column=col)
        if col == 1:
            c.value = "VALEUR FONCTION OBJ. (Coût ENL + SLN)"
        elif col == 2:
            c.value = f"=B{r_enl}+B{r_sln}"
            _num_int(c)
        _apply(c, bold=True, fill_color="1F4E79", size=10, color="FFFFFF")

    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 18
    ws.freeze_panes = "A3"


def _couleurs_th(centrales):
    """Retourne (hex_couleur, hex_pale) pour chaque centrale thermique,
    en reproduisant exactement la colormap Oranges de visualisation.py."""
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    def _to_hex(rgba):
        r, g, b, _ = rgba
        return "{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))

    def _palir(rgba, blend=0.20):
        r, g, b, a = rgba
        return (r + (1 - r) * blend, g + (1 - g) * blend, b + (1 - b) * blend, a)

    nb_ct       = len(centrales)
    orange_cmap = plt.colormaps["Oranges"]
    nuances     = [orange_cmap(0.35 + 0.55 * i / max(nb_ct - 1, 1)) for i in range(nb_ct)]
    return {ct: (_to_hex(nuances[i]), _to_hex(_palir(nuances[i])))
            for i, ct in enumerate(centrales)}


def _feuille_mix_mwh(ws, centrales, volumes):
    ws.title = "Mix énergétique (MWh)"

    # ── Couleurs exactement alignées sur visualisation.py ─────────────────────
    C_ENR     = "31CC2E"
    C_CHG_ENR = "5AD657"
    C_BAT     = "A8F0A8"
    C_YATE    = "2471A3"
    C_CHG_YAT = "4F8DB5"
    C_NEA     = "85C1E9"
    C_CHG_NEA = "9DCDED"
    C_CAT     = "2C2C2C"
    C_CHG_CAT = "565656"
    C_BRIDAGE = "D41313"
    C_TOTAL   = "17202A"
    C_HEADER  = "2E4057"

    th_colors = _couleurs_th(centrales)   # {ct: (hex_fonce, hex_pale)}

    # 5 colonnes : Source | Injection réseau | Stocké → batt. | Total produit | Écrêté (ENR only)
    NB_COLS = 5
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NB_COLS)
    c = ws.cell(row=1, column=1, value="Mix énergétique journalier — Énergie par source (MWh)")
    _apply(c, bold=True, fill_color="1F4E79", align="center", size=11, color="FFFFFF")

    headers = [
        "Source",
        "Injection réseau (MWh)",
        "Stocké → batterie (MWh)",
        "Total produit (MWh)",
        "Écrêté (MWh)",
    ]
    for j, label in enumerate(headers, start=1):
        c = ws.cell(row=2, column=j, value=label)
        fill = C_BRIDAGE if j == 5 else C_HEADER
        _apply(c, bold=True, fill_color=fill, align="center", size=9, color="FFFFFF")

    current_row = 3

    def _ligne(label, inj, stk, tot, ecr=None,
               c_src=None, c_inj=None, c_stk=None, c_tot=None):
        nonlocal current_row
        fills = [c_src, c_inj, c_stk, c_tot, "FADBD8" if ecr is not None else None]
        vals  = [label, inj,   stk,   tot,   ecr]
        for j, (val, fill) in enumerate(zip(vals, fills), start=1):
            cell = ws.cell(row=current_row, column=j, value=val)
            _apply(cell, bold=True, fill_color=fill, size=9, color="FFFFFF" if fill else "000000")
            if j > 1 and val is not None:
                _num(cell)
        current_row += 1

    def _vide():
        nonlocal current_row
        current_row += 1

    # ── ENR ──────────────────────────────────────────────────────────────────
    _ligne("ENR",
           inj=volumes["mwh_enr_direct"],
           stk=volumes["mwh_enr_charge"],
           tot=volumes["mwh_enr_direct"] + volumes["mwh_enr_charge"],
           ecr=volumes["mwh_ecretee"],
           c_src=C_ENR, c_inj=C_ENR, c_stk=C_CHG_ENR, c_tot=C_ENR)
    _vide()

    # ── Yaté ─────────────────────────────────────────────────────────────────
    _ligne("Yaté",
           inj=volumes["mwh_yate_inj"],
           stk=volumes["mwh_yate_charge"],
           tot=volumes["mwh_yate"],
           c_src=C_YATE, c_inj=C_YATE, c_stk=C_CHG_YAT, c_tot=C_YATE)
    _vide()

    # ── Néaoua ───────────────────────────────────────────────────────────────
    _ligne("Néaoua",
           inj=volumes["mwh_neaoua_inj"],
           stk=volumes["mwh_neaoua_charge"],
           tot=volumes["mwh_neaoua"],
           c_src=C_NEA, c_inj=C_NEA, c_stk=C_CHG_NEA, c_tot=C_NEA)
    _vide()

    # ── Thermiques (une ligne par centrale) ───────────────────────────────────
    for ct in centrales:
        ch, ch_pale = th_colors[ct]
        _ligne(ct,
               inj=volumes[f"mwh_th_{ct}_inj"],
               stk=volumes[f"mwh_th_{ct}_charge"],
               tot=volumes[f"mwh_th_{ct}"],
               c_src=ch, c_inj=ch, c_stk=ch_pale, c_tot=ch)
    _vide()

    # ── CAT ──────────────────────────────────────────────────────────────────
    _ligne("CAT",
           inj=volumes["mwh_cat_inj"],
           stk=volumes["mwh_cat_charge"],
           tot=volumes["mwh_cat_tot"],
           c_src=C_CAT, c_inj=C_CAT, c_stk=C_CHG_CAT, c_tot=C_CAT)
    _vide()

    # ── Batterie → réseau (décharge toutes sources) ───────────────────────────
    _ligne("Batterie → réseau (décharge)",
           inj=volumes["mwh_bat_reseau"],
           stk=0,
           tot=volumes["mwh_bat_reseau"],
           c_src=C_BAT, c_inj=C_BAT, c_stk=None, c_tot=C_BAT)
    _vide()

    # ── TOTAL GÉNÉRAL ─────────────────────────────────────────────────────────
    mwh_tot_inj = (volumes["mwh_enr_direct"] + volumes["mwh_bat_reseau"]
                   + volumes["mwh_yate_inj"] + volumes["mwh_neaoua_inj"]
                   + sum(volumes[f"mwh_th_{ct}_inj"] for ct in centrales)
                   + volumes["mwh_cat_inj"])
    mwh_tot_stk = (volumes["mwh_enr_charge"] + volumes["mwh_yate_charge"]
                   + volumes["mwh_neaoua_charge"]
                   + sum(volumes[f"mwh_th_{ct}_charge"] for ct in centrales)
                   + volumes["mwh_cat_charge"])
    for j, val in enumerate(
        ["TOTAL", round(mwh_tot_inj, 2), round(mwh_tot_stk, 2),
         round(volumes["mwh_total"], 2), None],
        start=1,
    ):
        cell = ws.cell(row=current_row, column=j, value=val)
        _apply(cell, bold=True, fill_color=C_TOTAL, size=11, color="FFFFFF")
        if j > 1 and val is not None:
            _num(cell)

    ws.column_dimensions["A"].width = 36
    for j in range(2, NB_COLS + 1):
        ws.column_dimensions[get_column_letter(j)].width = 24
    ws.freeze_panes = "A3"


# =============================================================================
# Fonction principale
# =============================================================================

def exporter_resultats_excel(
    nb_pas, pas_h,
    centrales, cat, yate, neaoua,
    prod_th_dp_val, prod_th_sln_val,
    prod_cat_dp_val, prod_cat_sln_val,
    prod_yate_val,
    prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
    prod_neaoua_dp_val, prod_neaoua_sln_val,
    v_th_val, v_yate_val, v_neaoua_val,
    enr_u_dp_val, enr_u_sln_val, enr_bridee_val,
    prod_enr, cout_br, prix_achat_sln_enr,
    demande_dp, demande_sln,
    stock_batt_val, p_charge_val, p_decharge_val,
    batt,
    p_charge_enr_val, p_charge_th_val,
    p_charge_cat_val, p_charge_yate_val, p_charge_neaoua_val,
    prod_bat_dp_val, prod_bat_sln_val,
    delta_charge_val, delta_decharge_val,
    chemin_sortie="resultats_optimisation.xlsx",
):
    periodes = range(nb_pas)

    # ── Calcul des volumes énergétiques (MWh) ────────────────────────────────
    # MWh produits = DP + SLN + part vers batterie (calé sur la fonction objectif)
    mwh_th       = sum((prod_th_dp_val[ct,r,t] + prod_th_sln_val[ct,r,t]
                        + p_charge_th_val[ct,r,t]) * pas_h
                       for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
    mwh_th_sln   = sum(prod_th_sln_val[ct,r,t] * pas_h
                       for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
    mwh_yate     = sum(prod_yate_val[r,t] * pas_h
                       for r in range(yate["nb_groupes"]) for t in periodes)  # prod_yate inclut déjà p_charge_yate
    mwh_yate_sln_sous = sum(prod_yate_sln_sous_val[t] * pas_h for t in periodes)
    mwh_yate_sln_sup  = sum(prod_yate_sln_sup_val[t]  * pas_h for t in periodes)
    mwh_neaoua   = sum((prod_neaoua_dp_val[r,t] + prod_neaoua_sln_val[r,t]
                        + p_charge_neaoua_val[r,t]) * pas_h
                       for r in range(neaoua["nb_groupes"]) for t in periodes)
    mwh_neaoua_sln = sum(prod_neaoua_sln_val[r,t] * pas_h
                         for r in range(neaoua["nb_groupes"]) for t in periodes)
    mwh_cat_dp   = sum((prod_cat_dp_val[t] + p_charge_cat_val[t]) * pas_h for t in periodes)
    mwh_cat_tot  = sum((prod_cat_dp_val[t] + prod_cat_sln_val[t]) * pas_h for t in periodes)  # p_charge_cat hors cout_cat_marginal
    mwh_enr_sln  = sum(enr_u_sln_val[t]   * pas_h for t in periodes)
    mwh_ecretee  = sum(enr_bridee_val[t] * pas_h for t in periodes)
    mwh_bat_dech   = sum(p_decharge_val[t] * pas_h for t in periodes)
    mwh_bat_charge = sum(p_charge_val[t]  * pas_h for t in periodes)
    mwh_bat_cycle  = mwh_bat_dech + mwh_bat_charge

    # ── Calcul des coûts ──────────────────────────────────────────────────────
    cout_th_prop = sum(
        centrales[ct]["cout_prop"] * (prod_th_dp_val[ct,r,t] + prod_th_sln_val[ct,r,t]
                                       + p_charge_th_val[ct,r,t]) * pas_h
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
    cout_th_prop_par_ct = {
        ct: sum(centrales[ct]["cout_prop"] * (prod_th_dp_val[ct,r,t] + prod_th_sln_val[ct,r,t]
                                               + p_charge_th_val[ct,r,t]) * pas_h
                for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
        for ct in centrales}
    mwh_th_par_ct = {
        ct: sum((prod_th_dp_val[ct,r,t] + prod_th_sln_val[ct,r,t]
                 + p_charge_th_val[ct,r,t]) * pas_h
                for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
        for ct in centrales}
    tarif_prop_par_ct = {ct: centrales[ct]["cout_prop"] for ct in centrales}
    cout_th_demarrage = sum(
        centrales[ct]["cout_demarrage"] * v_th_val[ct,r,t]
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
    cout_th_demarrage_par_ct = {
        ct: sum(centrales[ct]["cout_demarrage"] * v_th_val[ct,r,t]
                for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
        for ct in centrales}
    nb_demarrage_par_ct = {
        ct: round(sum(v_th_val[ct,r,t]
                for r in range(centrales[ct]["nb_groupes"]) for t in periodes), 1)
        for ct in centrales}
    cout_yate_opp = sum(
        yate["cout_opp"] * prod_yate_val[r,t] * pas_h
        for r in range(yate["nb_groupes"]) for t in periodes)
    cout_yate_demarrage = sum(
        yate["cout_demarrage"] * v_yate_val[r,t]
        for r in range(yate["nb_groupes"]) for t in periodes)
    nb_demarrage_yate = round(sum(
        v_yate_val[r,t] for r in range(yate["nb_groupes"]) for t in periodes), 1)
    cout_neaoua_opp = sum(
        neaoua["cout_opp"] * (prod_neaoua_dp_val[r,t] + prod_neaoua_sln_val[r,t]
                               + p_charge_neaoua_val[r,t]) * pas_h
        for r in range(neaoua["nb_groupes"]) for t in periodes)
    cout_neaoua_demarrage = sum(
        neaoua["cout_demarrage"] * v_neaoua_val[r,t]
        for r in range(neaoua["nb_groupes"]) for t in periodes)
    nb_demarrage_neaoua = round(sum(
        v_neaoua_val[r,t] for r in range(neaoua["nb_groupes"]) for t in periodes), 1)
    cout_achat_enl_cat = sum(cat["prix_achat_enl"] * (prod_cat_dp_val[t] + p_charge_cat_val[t]) * pas_h for t in periodes)
    cout_bridage = sum(cout_br * enr_bridee_val[t] * pas_h for t in periodes)
    cout_batterie = sum(batt["cout_cycle"] * (p_decharge_val[t] + p_charge_val[t]) * pas_h for t in periodes)
    cout_lissage = sum(
        batt["cout_lissage"] * (delta_charge_val[t] + delta_decharge_val[t])
        for t in periodes)
    cout_enl = (cout_th_prop + cout_th_demarrage + cout_yate_opp + cout_yate_demarrage
                + cout_neaoua_opp + cout_neaoua_demarrage + cout_achat_enl_cat
                + cout_bridage + cout_batterie + cout_lissage)

    cout_cat_marginal     = sum(cat["cout_prop"] * (prod_cat_dp_val[t] + prod_cat_sln_val[t]) * pas_h for t in periodes)
    cout_achat_sln_th     = sum(centrales[ct]["prix_achat_sln"] * prod_th_sln_val[ct,r,t] * pas_h
                                for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
    cout_achat_sln_yate_sous = sum(yate["prix_achat_sln_yate"]    * prod_yate_sln_sous_val[t] * pas_h for t in periodes)
    cout_achat_sln_yate_sup  = sum(yate["prix_achat_sln_yate_hs"] * prod_yate_sln_sup_val[t]  * pas_h for t in periodes)
    cout_achat_sln_neaoua = sum(neaoua["prix_achat_sln"] * prod_neaoua_sln_val[r,t] * pas_h
                                for r in range(neaoua["nb_groupes"]) for t in periodes)
    cout_achat_sln_enr    = sum(prix_achat_sln_enr * (enr_u_sln_val[t] + prod_bat_sln_val[t]) * pas_h for t in periodes)
    cout_sln = (cout_cat_marginal + cout_achat_sln_th + cout_achat_sln_yate_sous
                + cout_achat_sln_yate_sup + cout_achat_sln_neaoua + cout_achat_sln_enr)

    def _tarif(cout, mwh):
        return round(cout / mwh, 0) if mwh and mwh > 0 else None

    tarif_th_moy = _tarif(cout_th_prop, mwh_th)

    cout_variable_mix = cout_th_prop + cout_yate_opp + cout_neaoua_opp + cout_cat_marginal
    mwh_injecte_mix = (
        mwh_th + mwh_yate + mwh_neaoua
        + sum((prod_cat_dp_val[t] + prod_cat_sln_val[t]) * pas_h for t in periodes)
        + sum((enr_u_dp_val[t] + enr_u_sln_val[t]) * pas_h for t in periodes)
        + sum(p_decharge_val[t] * batt["rho"] * pas_h for t in periodes)
    )

    cout_th_prop_dp = sum(
        centrales[ct]["cout_prop"] * prod_th_dp_val[ct, r, t] * pas_h
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
    cout_yate_opp_dp = sum(
        yate["cout_opp"] * prod_yate_dp_val[t] * pas_h for t in periodes)
    cout_neaoua_opp_dp = sum(
        neaoua["cout_opp"] * prod_neaoua_dp_val[r, t] * pas_h
        for r in range(neaoua["nb_groupes"]) for t in periodes)
    cout_achat_enl_cat_dp = sum(
        cat["prix_achat_enl"] * prod_cat_dp_val[t] * pas_h for t in periodes)
    cout_enl_reel = (cout_th_prop_dp + cout_yate_opp_dp
                     + cout_neaoua_opp_dp + cout_achat_enl_cat_dp + cout_bridage)

    mwh_dp = (
        sum(prod_th_dp_val[ct, r, t] * pas_h
            for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
        + sum(prod_yate_dp_val[t] * pas_h for t in periodes)
        + sum(prod_neaoua_dp_val[r, t] * pas_h
              for r in range(neaoua["nb_groupes"]) for t in periodes)
        + sum(prod_cat_dp_val[t] * pas_h for t in periodes)
        + sum(enr_u_dp_val[t] * pas_h for t in periodes)
        + sum(p_decharge_val[t] * batt["rho"] * pas_h for t in periodes)
    )

    couts = {
        "cout_th_prop"            : cout_th_prop,
        "cout_th_prop_par_ct"     : cout_th_prop_par_ct,
        "mwh_th_par_ct"           : mwh_th_par_ct,
        "tarif_prop_par_ct"       : tarif_prop_par_ct,
        "tarif_prop_par_ct"       : {ct: centrales[ct]["cout_prop"] for ct in centrales},
        "cout_th_demarrage"       : cout_th_demarrage,
        "cout_th_demarrage_par_ct": cout_th_demarrage_par_ct,
        "nb_demarrage_par_ct"     : nb_demarrage_par_ct,
        "tarif_demarrage_par_ct"  : {ct: centrales[ct]["cout_demarrage"] for ct in centrales},
        "cout_yate_opp"           : cout_yate_opp,
        "cout_yate_demarrage"     : cout_yate_demarrage,
        "nb_demarrage_yate"       : nb_demarrage_yate,
        "tarif_demarrage_yate"    : yate["cout_demarrage"],
        "cout_neaoua_opp"         : cout_neaoua_opp,
        "cout_neaoua_demarrage"   : cout_neaoua_demarrage,
        "nb_demarrage_neaoua"     : nb_demarrage_neaoua,
        "tarif_demarrage_neaoua"  : neaoua["cout_demarrage"],
        "cout_achat_enl_cat"      : cout_achat_enl_cat,
        "cout_bridage"            : cout_bridage,
        "cout_batterie"           : cout_batterie,
        "cout_lissage"            : cout_lissage,
        "cout_enl"                : cout_enl,
        "cout_variable_mix"       : cout_variable_mix,
        "mwh_injecte_mix"         : round(mwh_injecte_mix, 2),
        "cout_enl_reel"           : cout_enl_reel,
        "mwh_dp"                  : round(mwh_dp, 2),
        "cout_cat_marginal"       : cout_cat_marginal,
        "cout_achat_sln_th"       : cout_achat_sln_th,
        "cout_achat_sln_yate_sous": cout_achat_sln_yate_sous,
        "cout_achat_sln_yate_sup" : cout_achat_sln_yate_sup,
        "cout_achat_sln_neaoua"   : cout_achat_sln_neaoua,
        "cout_achat_sln_enr"      : cout_achat_sln_enr,
        "cout_sln"                : cout_sln,
        "cout_total"              : cout_enl + cout_sln,
        "mwh_th"                  : round(mwh_th, 2),
        "mwh_th_sln"              : round(mwh_th_sln, 2),
        "mwh_yate"                : round(mwh_yate, 2),
        "mwh_yate_sln_sous"       : round(mwh_yate_sln_sous, 2),
        "mwh_yate_sln_sup"        : round(mwh_yate_sln_sup, 2),
        "mwh_neaoua"              : round(mwh_neaoua, 2),
        "mwh_neaoua_sln"          : round(mwh_neaoua_sln, 2),
        "mwh_cat_dp"              : round(mwh_cat_dp, 2),
        "mwh_cat_tot"             : round(mwh_cat_tot, 2),
        "mwh_enr_sln"             : round(mwh_enr_sln, 2),
        "mwh_ecretee"             : round(mwh_ecretee, 2),
        "mwh_bat_dech"            : round(mwh_bat_dech, 2),
        "mwh_bat_cycle"           : round(mwh_bat_cycle, 2),
        "tarif_th_prop"           : tarif_th_moy,
        "tarif_yate_opp"          : yate["cout_opp"],
        "tarif_neaoua_opp"        : neaoua["cout_opp"],
        "tarif_cat_enl"           : cat["prix_achat_enl"],
        "tarif_cat_marginal"      : cat["cout_prop"],
        "tarif_bridage"           : cout_br,
        "tarif_cycle"             : batt["cout_cycle"],
        "tarif_lissage"           : batt["cout_lissage"],
        "tarif_th_sln"            : _tarif(cout_achat_sln_th, mwh_th_sln),
        "tarif_yate_sln"          : yate["prix_achat_sln_yate"],
        "tarif_yate_sln_hs"       : yate["prix_achat_sln_yate_hs"],
        "tarif_neaoua_sln"        : neaoua["prix_achat_sln"],
        "tarif_enr_sln"           : prix_achat_sln_enr,
    }

    # ── Volumes par centrale thermique (injection + charge batt) ─────────────
    mwh_th_par_ct_inj = {
        ct: sum((prod_th_dp_val[ct,r,t] + prod_th_sln_val[ct,r,t]) * pas_h
                for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
        for ct in centrales
    }
    mwh_th_par_ct_charge = {
        ct: sum(p_charge_th_val[ct,r,t] * pas_h
                for r in range(centrales[ct]["nb_groupes"]) for t in periodes)
        for ct in centrales
    }

    mwh_enr_direct      = sum((enr_u_dp_val[t] + enr_u_sln_val[t]) * pas_h for t in periodes)
    mwh_enr_charge      = sum(p_charge_enr_val[t] * pas_h for t in periodes)
    mwh_bat_dech_reseau = sum(p_decharge_val[t] * batt["rho"] * pas_h for t in periodes)

    mwh_yate_inj    = sum((prod_yate_dp_val[t] + prod_yate_sln_sous_val[t] + prod_yate_sln_sup_val[t]) * pas_h
                          for t in periodes)
    mwh_yate_charge = sum(
        sum(p_charge_yate_val[r,t] for r in range(yate["nb_groupes"])) * pas_h
        for t in periodes)

    mwh_neaoua_inj    = sum((sum(prod_neaoua_dp_val[r,t] + prod_neaoua_sln_val[r,t]
                                 for r in range(neaoua["nb_groupes"]))) * pas_h for t in periodes)
    mwh_neaoua_charge = sum(
        sum(p_charge_neaoua_val[r,t] for r in range(neaoua["nb_groupes"])) * pas_h
        for t in periodes)

    mwh_cat_inj    = sum((prod_cat_dp_val[t] + prod_cat_sln_val[t]) * pas_h for t in periodes)
    mwh_cat_charge = sum(p_charge_cat_val[t] * pas_h for t in periodes)

    mwh_total = (mwh_enr_direct + mwh_bat_dech_reseau
                 + mwh_yate_inj + mwh_neaoua_inj
                 + sum(mwh_th_par_ct_inj.values())
                 + mwh_cat_inj)

    volumes = {
        # ENR
        "mwh_enr_direct"  : round(mwh_enr_direct, 2),
        "mwh_enr_charge"  : round(mwh_enr_charge, 2),
        "mwh_enr_bat"     : round(mwh_bat_dech_reseau, 2),   # rétro-compat
        "mwh_bat_reseau"  : round(mwh_bat_dech_reseau, 2),
        "mwh_enr_total"   : round(mwh_enr_direct + mwh_bat_dech_reseau, 2),
        "mwh_ecretee"     : round(mwh_ecretee, 2),
        # Yaté
        "mwh_yate"        : round(mwh_yate_inj + mwh_yate_charge, 2),
        "mwh_yate_inj"    : round(mwh_yate_inj, 2),
        "mwh_yate_charge" : round(mwh_yate_charge, 2),
        # Néaoua
        "mwh_neaoua"      : round(mwh_neaoua_inj + mwh_neaoua_charge, 2),
        "mwh_neaoua_inj"  : round(mwh_neaoua_inj, 2),
        "mwh_neaoua_charge": round(mwh_neaoua_charge, 2),
        # Thermiques agrégés
        "mwh_th"          : round(mwh_th, 2),
        # CAT
        "mwh_cat_tot"     : round(mwh_cat_inj + mwh_cat_charge, 2),
        "mwh_cat_inj"     : round(mwh_cat_inj, 2),
        "mwh_cat_charge"  : round(mwh_cat_charge, 2),
        # Total
        "mwh_total"       : round(mwh_total, 2),
    }
    for ct in centrales:
        volumes[f"mwh_th_{ct}"]        = round(mwh_th_par_ct_inj[ct] + mwh_th_par_ct_charge[ct], 2)
        volumes[f"mwh_th_{ct}_inj"]    = round(mwh_th_par_ct_inj[ct], 2)
        volumes[f"mwh_th_{ct}_charge"] = round(mwh_th_par_ct_charge[ct], 2)

    # ── Écriture du classeur ──────────────────────────────────────────────────
    wb = openpyxl.Workbook()

    ws_prod = wb.active
    _feuille_productions(
        ws_prod, nb_pas, pas_h, centrales, yate, neaoua,
        prod_th_dp_val, prod_th_sln_val,
        prod_cat_dp_val, prod_cat_sln_val,
        prod_yate_val,
        prod_yate_dp_val, prod_yate_sln_sous_val, prod_yate_sln_sup_val,
        prod_neaoua_dp_val, prod_neaoua_sln_val,
        enr_u_dp_val, enr_u_sln_val, enr_bridee_val,
        demande_dp, demande_sln, prod_enr,
        stock_batt_val, p_charge_val, p_decharge_val, batt,
        p_charge_enr_val, p_charge_th_val,
        p_charge_cat_val, p_charge_yate_val, p_charge_neaoua_val,
    )

    ws_couts = wb.create_sheet()
    _feuille_couts(ws_couts, couts)

    ws_mix = wb.create_sheet()
    _feuille_mix_mwh(ws_mix, centrales, volumes)

    if os.path.exists(chemin_sortie):
        os.remove(chemin_sortie)

    wb.save(chemin_sortie)