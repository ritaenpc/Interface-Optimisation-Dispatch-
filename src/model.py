import pulp


def creer_modele_et_variables(nb_pas, centrales, cat, yate, neaoua, prod_enr, batt):
    periodes = range(nb_pas)
    m = pulp.LpProblem("Placement_Optimal_Moyens_Production", pulp.LpMinimize)

    prod_th_dp = {
        (ct, r, t): pulp.LpVariable(f"p_th_dp_{ct}_r{r}_t{t}", lowBound=0, upBound=centrales[ct]["p_max_groupe"])
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes
    }
    prod_th_sln = {
        (ct, r, t): pulp.LpVariable(f"p_th_sln_{ct}_r{r}_t{t}", lowBound=0, upBound=centrales[ct]["p_max_groupe"])
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes
    }
    u_th = {
        (ct, r, t): pulp.LpVariable(f"u_th_{ct}_r{r}_t{t}", cat="Binary")
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes
    }
    v_th = {
        (ct, r, t): pulp.LpVariable(f"v_th_{ct}_r{r}_t{t}", cat="Binary")
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes
    }

    prod_cat_dp  = {t: pulp.LpVariable(f"p_cat_dp_t{t}",  lowBound=0, upBound=cat["p_max_liste"][t]) for t in periodes}
    prod_cat_sln = {t: pulp.LpVariable(f"p_cat_sln_t{t}", lowBound=0, upBound=cat["p_max_liste"][t]) for t in periodes}

    prod_yate = {
        (r, t): pulp.LpVariable(f"p_yate_r{r}_t{t}", lowBound=0, upBound=yate["p_max_groupe"])
        for r in range(yate["nb_groupes"]) for t in periodes
    }
    prod_yate_dp = {
        t: pulp.LpVariable(f"p_yate_dp_t{t}", lowBound=0, upBound=yate["nb_groupes"]*yate["p_max_groupe"]-yate["puissance_souscrite_sln_nuit"])
        for t in periodes
    }
    prod_yate_sln_sous = {
        t: pulp.LpVariable(f"p_yate_sln_sous_t{t}", lowBound=0, upBound=yate["puissance_souscrite_sln_jour"])
        for t in periodes
    }
    prod_yate_sln_sup = {
        t: pulp.LpVariable(f"p_yate_sln_sup_t{t}", lowBound=0, upBound=yate["nb_groupes"]*yate["p_max_groupe"]-yate["puissance_souscrite_sln_nuit"])
        for t in periodes
    }
    delta_sln_sup = {t: pulp.LpVariable(f"delta_sln_sup_t{t}", cat="Binary") for t in periodes}

    u_yate = {
        (r, t): pulp.LpVariable(f"u_yate_r{r}_t{t}", cat="Binary")
        for r in range(yate["nb_groupes"]) for t in periodes
    }
    v_yate = {
        (r, t): pulp.LpVariable(f"v_yate_r{r}_t{t}", cat="Binary")
        for r in range(yate["nb_groupes"]) for t in periodes
    }

    prod_neaoua_dp = {
        (r, t): pulp.LpVariable(f"p_neaoua_dp_r{r}_t{t}", lowBound=0, upBound=neaoua["p_max_groupe"])
        for r in range(neaoua["nb_groupes"]) for t in periodes
    }
    prod_neaoua_sln = {
        (r, t): pulp.LpVariable(f"p_neaoua_sln_r{r}_t{t}", lowBound=0, upBound=neaoua["p_max_groupe"])
        for r in range(neaoua["nb_groupes"]) for t in periodes
    }
    u_neaoua = {
        (r, t): pulp.LpVariable(f"u_neaoua_r{r}_t{t}", cat="Binary")
        for r in range(neaoua["nb_groupes"]) for t in periodes
    }
    v_neaoua = {
        (r, t): pulp.LpVariable(f"v_neaoua_r{r}_t{t}", cat="Binary")
        for r in range(neaoua["nb_groupes"]) for t in periodes
    }

    enr_u_dp  = {t: pulp.LpVariable(f"enr_u_dp_t{t}",  lowBound=0, upBound=prod_enr[t]) for t in periodes}
    enr_u_sln = {t: pulp.LpVariable(f"enr_u_sln_t{t}", lowBound=0, upBound=prod_enr[t]) for t in periodes}

    # Variable de bridage explicite : ENR disponible non injectée et non stockée
    enr_bridee = {t: pulp.LpVariable(f"enr_bridee_t{t}", lowBound=0, upBound=prod_enr[t]) for t in periodes}

    p_charge_enr = {t: pulp.LpVariable(f"p_charge_enr_t{t}", lowBound=0, upBound=batt["p_max"]) for t in periodes}
    p_charge_th = {
        (ct, r, t): pulp.LpVariable(f"p_charge_th_{ct}_r{r}_t{t}", lowBound=0, upBound=centrales[ct]["p_max_groupe"])
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in periodes
    }
    p_charge_cat = {t: pulp.LpVariable(f"p_charge_cat_t{t}", lowBound=0, upBound=cat["p_max_liste"][t]) for t in periodes}
    p_charge_yate = {
        (r, t): pulp.LpVariable(f"p_charge_yate_r{r}_t{t}", lowBound=0, upBound=yate["p_max_groupe"])
        for r in range(yate["nb_groupes"]) for t in periodes
    }
    p_charge_neaoua = {
        (r, t): pulp.LpVariable(f"p_charge_neaoua_r{r}_t{t}", lowBound=0, upBound=neaoua["p_max_groupe"])
        for r in range(neaoua["nb_groupes"]) for t in periodes
    }

    p_charge   = {t: pulp.LpVariable(f"p_charge_t{t}",   lowBound=0, upBound=batt["p_max"]) for t in periodes}
    p_decharge = {t: pulp.LpVariable(f"p_decharge_t{t}", lowBound=0, upBound=batt["p_max"]) for t in periodes}
    u_charge   = {t: pulp.LpVariable(f"u_charge_t{t}",   cat="Binary") for t in periodes}
    u_decharge = {t: pulp.LpVariable(f"u_decharge_t{t}", cat="Binary") for t in periodes}
    stock_batt = {t: pulp.LpVariable(f"stock_batt_t{t}", lowBound=0, upBound=batt["e_max"]) for t in periodes}
    prod_bat_dp  = {t: pulp.LpVariable(f"prod_bat_dp_t{t}",  lowBound=0, upBound=batt["p_max"]) for t in periodes}
    prod_bat_sln = {t: pulp.LpVariable(f"prod_bat_sln_t{t}", lowBound=0, upBound=batt["p_max"]) for t in periodes}
    delta_decharge = {t: pulp.LpVariable(f"delta_decharge_t{t}", lowBound=0) for t in periodes}
    delta_charge   = {t: pulp.LpVariable(f"delta_charge_t{t}",   lowBound=0) for t in periodes}

    return (
        m,
        prod_th_dp, prod_th_sln, u_th, v_th,
        prod_cat_dp, prod_cat_sln,
        prod_yate, prod_yate_dp, prod_yate_sln_sous, prod_yate_sln_sup, delta_sln_sup,
        u_yate, v_yate,
        prod_neaoua_dp, prod_neaoua_sln, u_neaoua, v_neaoua,
        enr_u_dp, enr_u_sln, enr_bridee,
        p_charge_enr, p_charge_th, p_charge_cat, p_charge_yate, p_charge_neaoua,
        p_charge, p_decharge, u_charge, u_decharge, stock_batt,
        prod_bat_dp, prod_bat_sln,
        delta_decharge, delta_charge,
    )


# =============================================================================
# Contraintes
# =============================================================================

def ajouter_contrainte_bornes_groupe_th(nb_pas, m, prod_th_dp, prod_th_sln, p_charge_th, u_th, centrales):
    for ct in centrales:
        for r in range(centrales[ct]["nb_groupes"]):
            for t in range(nb_pas):
                prod_tot = prod_th_dp[ct, r, t] + prod_th_sln[ct, r, t] + p_charge_th[ct, r, t]
                m += (prod_tot >= centrales[ct]["min_technique_groupe"] * u_th[ct, r, t], f"Min_tech_groupe_{ct}_r{r}_t{t}")
                m += (prod_tot <= centrales[ct]["p_max_groupe"]          * u_th[ct, r, t], f"P_max_groupe_{ct}_r{r}_t{t}")
    return m


# def ajouter_contrainte_bornes_cat(nb_pas, m, prod_cat_dp, prod_cat_sln, p_charge_cat, cat):
#     for t in range(nb_pas):
#         m += (prod_cat_dp[t] + prod_cat_sln[t] + p_charge_cat[t] <= cat["p_max_liste"][t], f"P_max_cat_t{t}")
#     return m

def ajouter_contrainte_bornes_cat(nb_pas, m, prod_cat_dp, prod_cat_sln, p_charge_cat,
                                   u_th, u_yate, u_neaoua,
                                   centrales, yate, neaoua, cat,
                                   e_cin_min_reseau):
    for t in range(nb_pas):
        prod_cat_totale = prod_cat_dp[t] + prod_cat_sln[t] + p_charge_cat[t]

        # Energie cinétique totale apportée par les groupes actifs (hors CAT)
        e_cin_totale = (
            pulp.lpSum(
                centrales[ct]["e_cin_groupe"] * u_th[ct, r, t]
                for ct in centrales for r in range(centrales[ct]["nb_groupes"])
            )
            + pulp.lpSum(
                yate["e_cin_groupe"] * u_yate[r, t]
                for r in range(yate["nb_groupes"])
            )
            + pulp.lpSum(
                neaoua["e_cin_groupe"] * u_neaoua[r, t]
                for r in range(neaoua["nb_groupes"])
            )
        )
        
        # Borne max (inchangée)
        m += (prod_cat_totale <= cat["p_max_liste"][t], f"P_max_cat_t{t}")

        # Borne min dynamique liée à l'énergie cinétique
        borne_min_cat = ((e_cin_min_reseau - e_cin_totale) / cat["e_cin_groupe"]) * 14
        m += (prod_cat_totale >= borne_min_cat, f"Min_ecin_cat_t{t}")
        m += (prod_cat_totale >= cat["min_technique_ct"], f"Min54_ecin_cat_t{t}")

    return m


# def ajouter_contrainte_min_cat(nb_pas, m, prod_cat_dp, prod_cat_sln, p_charge_cat):
#     for t in range(nb_pas):
#         m += (prod_cat_dp[t] + prod_cat_sln[t] + p_charge_cat[t] >= 54.0, f"Min_cat_t{t}")
#     return m


def ajouter_contrainte_bornes_groupe_yate(nb_pas, m, prod_yate, u_yate, yate):
    for r in range(yate["nb_groupes"]):
        for t in range(nb_pas):
            m += (prod_yate[r, t] >= yate["min_technique_groupe"] * u_yate[r, t], f"Min_tech_groupe_yate_r{r}_t{t}")
            m += (prod_yate[r, t] <= yate["p_max_groupe"]          * u_yate[r, t], f"P_max_groupe_yate_r{r}_t{t}")
    return m


def ajouter_contrainte_bornes_groupe_neaoua(nb_pas, m, prod_neaoua_dp, prod_neaoua_sln, p_charge_neaoua, u_neaoua, neaoua):
    for r in range(neaoua["nb_groupes"]):
        for t in range(nb_pas):
            prod_tot = prod_neaoua_dp[r, t] + prod_neaoua_sln[r, t] + p_charge_neaoua[r, t]
            m += (prod_tot >= neaoua["min_technique_groupe"] * u_neaoua[r, t], f"Min_tech_groupe_neaoua_r{r}_t{t}")
            m += (prod_tot <= neaoua["p_max_groupe"]          * u_neaoua[r, t], f"P_max_groupe_neaoua_r{r}_t{t}")
    return m



def ajouter_contrainte_groupes_toujours_actifs(nb_pas, pas_h, m, u_th, u_yate, centrales, yate):

    pas_indispo_yate = yate["indispos_liste"]

    
    prony_ct = [ct for ct in centrales if ct.startswith("Prony")]
    pas_indispo_prony = {ct: centrales[ct]["indispos_liste"].get(0, []) for ct in prony_ct}

    
    nepoui_ct = [ct for ct in centrales if ct.startswith("Népoui")]
    pas_indispo_nepoui = {ct: centrales[ct]["indispos_liste"].get(0, []) for ct in nepoui_ct}

    for t in range(nb_pas):

        # Prony : au moins 1 groupe actif parmi Prony1/Prony2, dès qu'au moins 1
        # est disponible
        nb_indispo_prony = sum(1 for ct in prony_ct if t in pas_indispo_prony[ct])
        min_actifs_prony = min(1, len(prony_ct) - nb_indispo_prony)
        m += (
            pulp.lpSum(u_th[ct, 0, t] for ct in prony_ct) >= min_actifs_prony,
            f"Prony_min_actif_t{t}",
        )

        # Népoui : au moins 1 groupe actif parmi les 4, dès qu'au moins 1 est disponible
        
        nb_indispo_nepoui = sum(1 for ct in nepoui_ct if t in pas_indispo_nepoui[ct])
        min_actifs_nepoui = min(1, len(nepoui_ct) - nb_indispo_nepoui)
        m += (
            pulp.lpSum(u_th[ct, 0, t] for ct in nepoui_ct) >= min_actifs_nepoui,
            f"Nepoui_min_actif_t{t}",
        )

        nb_indispo_yate = sum(1 for r in range(yate["nb_groupes"]) if t in pas_indispo_yate[r])
        min_actifs = min(3, 4 - nb_indispo_yate)
        m += (pulp.lpSum(u_yate[r, t] for r in range(yate["nb_groupes"])) >= min_actifs, f"Yate_grp_actif_t{t}")


    return m



def ajouter_contrainte_indispos(m, nb_pas, pas_h, centrales, yate, neaoua, u_th, u_yate, u_neaoua):
    for ct, params in centrales.items():
        for r, pas_liste in params["indispos_liste"].items():
            for t in pas_liste:
                m += (u_th[ct, r, t] == 0, f"Indispo_{ct}_r{r}_t{t}")

    for r, pas_liste in yate["indispos_liste"].items():
        for t in pas_liste:
            m += (u_yate[r, t] == 0, f"Indispo_yate_r{r}_t{t}")

    for r, pas_liste in neaoua["indispos_liste"].items():
        for t in pas_liste:
            m += (u_neaoua[r, t] == 0, f"Indispo_neaoua_r{r}_t{t}")

    return m

def ajouter_contrainte_lien_production_yate(nb_pas, m, prod_yate, prod_yate_dp, prod_yate_sln_sous,
                                             prod_yate_sln_sup, p_charge_yate, yate):
    for t in range(nb_pas):
        m += (
            pulp.lpSum(prod_yate[r, t] for r in range(yate["nb_groupes"]))
            == prod_yate_dp[t] + prod_yate_sln_sous[t] + prod_yate_sln_sup[t]
            + pulp.lpSum(p_charge_yate[r, t] for r in range(yate["nb_groupes"])),
            f"Lien_prod_yate_t{t}",
        )
    return m


def ajouter_contrainte_repartition_yate(nb_pas, m, prod_yate_dp, prod_yate_sln_sup, p_charge_yate, yate):
    for t in range(nb_pas):
        pas_indispo_yate = yate["indispos_liste"]
        nb_indispo_yate = sum(1 for r in range(yate["nb_groupes"]) if t in pas_indispo_yate[r])
        if 36 <= t < 108:
            puissance_allouee_dp = ((yate["nb_groupes"] - nb_indispo_yate) * yate["p_max_groupe"]) * (1 - (yate["puissance_souscrite_sln_jour"] / (yate["nb_groupes"] * yate["p_max_groupe"])))
        else:
            puissance_allouee_dp = ((yate["nb_groupes"] - nb_indispo_yate) * yate["p_max_groupe"]) * (1 - (yate["puissance_souscrite_sln_nuit"] / (yate["nb_groupes"] * yate["p_max_groupe"])))
        m += (prod_yate_sln_sup[t] <= puissance_allouee_dp - prod_yate_dp[t] - pulp.lpSum(p_charge_yate[r, t] for r in range(yate["nb_groupes"])), f"Surplus_sln_yate_t{t}")
        m += (prod_yate_sln_sup[t] <= puissance_allouee_dp * yate["vente_hs_SLN"])
    return m


def ajouter_contrainte_seuil_sln_sup(nb_pas, m, prod_yate_sln_sous, prod_yate_sln_sup, delta_sln_sup, yate):
    for t in range(nb_pas):
        pas_indispo_yate = yate["indispos_liste"]
        nb_indispo_yate = sum(1 for r in range(yate["nb_groupes"]) if t in pas_indispo_yate[r])
        if 36 <= t < 108:
            p_sous = ((yate["nb_groupes"] - nb_indispo_yate) * yate["p_max_groupe"]) * (yate["puissance_souscrite_sln_jour"] / (yate["nb_groupes"] * yate["p_max_groupe"]))
            M = ((yate["nb_groupes"] - nb_indispo_yate) * yate["p_max_groupe"]) * (1 - (yate["puissance_souscrite_sln_jour"] / (yate["nb_groupes"] * yate["p_max_groupe"])))
        else:
            p_sous = ((yate["nb_groupes"] - nb_indispo_yate) * yate["p_max_groupe"]) * (yate["puissance_souscrite_sln_nuit"] / (yate["nb_groupes"] * yate["p_max_groupe"]))
            M = ((yate["nb_groupes"] - nb_indispo_yate) * yate["p_max_groupe"]) * (1 - (yate["puissance_souscrite_sln_nuit"] / (yate["nb_groupes"] * yate["p_max_groupe"])))
        m += (prod_yate_sln_sous[t] >= p_sous - M * (1 - delta_sln_sup[t]), f"Seuil_sln_sous_t{t}")
        m += (prod_yate_sln_sup[t]  <= M * delta_sln_sup[t],                 f"Seuil_sln_sup_t{t}")
    return m


def ajouter_contrainte_demarrage(nb_pas, m, u_th, u_yate, u_neaoua, v_th, v_yate, v_neaoua,
                                  centrales, yate, neaoua):
    for ct in centrales:
        for r in range(centrales[ct]["nb_groupes"]):
            for t in range(nb_pas):
                u_prec = centrales[ct]["u_init"][r] if t == 0 else u_th[ct, r, t - 1]
                m += (v_th[ct, r, t] >= u_th[ct, r, t] - u_prec, f"Demarrage_th_{ct}_r{r}_t{t}")
    for r in range(yate["nb_groupes"]):
        for t in range(nb_pas):
            u_prec = yate["u_init"][r] if t == 0 else u_yate[r, t - 1]
            m += (v_yate[r, t] >= u_yate[r, t] - u_prec, f"Demarrage_yate_r{r}_t{t}")
    for r in range(neaoua["nb_groupes"]):
        for t in range(nb_pas):
            u_prec = neaoua["u_init"][r] if t == 0 else u_neaoua[r, t - 1]
            m += (v_neaoua[r, t] >= u_neaoua[r, t] - u_prec, f"Demarrage_neaoua_r{r}_t{t}")
    return m


def ajouter_contrainte_bilan_enr(nb_pas, m, enr_u_dp, enr_u_sln, p_charge_enr, enr_bridee, prod_enr):
    """Bilan ENR en égalité stricte : chaque MWh est injecté DP, injecté SLN, stocké ou bridé."""
    for t in range(nb_pas):
        m += (
            enr_u_dp[t] + enr_u_sln[t] + p_charge_enr[t] + enr_bridee[t] == prod_enr[t],
            f"Bilan_enr_t{t}",
        )
    return m


def ajouter_contrainte_lien_charge_batterie(nb_pas, m, p_charge, p_charge_enr, p_charge_th,
                                             p_charge_cat, p_charge_yate, p_charge_neaoua,
                                             centrales, yate, neaoua):
    for t in range(nb_pas):
        m += (
            p_charge[t]
            == p_charge_enr[t]
            + pulp.lpSum(p_charge_th[ct, r, t] for ct in centrales for r in range(centrales[ct]["nb_groupes"]))
            + p_charge_cat[t]
            + pulp.lpSum(p_charge_yate[r, t] for r in range(yate["nb_groupes"]))
            + pulp.lpSum(p_charge_neaoua[r, t] for r in range(neaoua["nb_groupes"])),
            f"Lien_charge_batt_t{t}",
        )
    return m


def ajouter_contrainte_enr_priorite_dp(nb_pas, pas_h, m, enr_u_dp, prod_enr,
                                        demande_dp, centrales, yate):

    prony_ct = [ct for ct in centrales if ct.startswith("Prony")]
    pas_indispo_prony = {ct: centrales[ct]["indispos_liste"].get(0, []) for ct in prony_ct}
    mt_prony = centrales[prony_ct[0]]["min_technique_groupe"]

    nepoui_ct = [ct for ct in centrales if ct.startswith("Népoui")]
    pas_indispo_nepoui = {ct: centrales[ct]["indispos_liste"].get(0, []) for ct in nepoui_ct}
    mt_nepoui = centrales[nepoui_ct[0]]["min_technique_groupe"]

    pas_indispo_yate = yate["indispos_liste"]

    for t in range(nb_pas):
        min_tech_t = 0.0

        nb_indispo_prony = sum(1 for ct in prony_ct if t in pas_indispo_prony[ct])
        nb_actifs_prony  = max(0, 1 - (len(prony_ct) - (len(prony_ct) - nb_indispo_prony)))
        nb_actifs_prony  = max(0, min(1, len(prony_ct) - nb_indispo_prony))
        min_tech_t      += nb_actifs_prony * mt_prony

        nb_indispo_nepoui = sum(1 for ct in nepoui_ct if t in pas_indispo_nepoui[ct])
        nb_actifs_nepoui  = max(0, min(1, len(nepoui_ct) - nb_indispo_nepoui))
        min_tech_t       += nb_actifs_nepoui * mt_nepoui

        nb_indispo_yate = sum(1 for r in range(yate["nb_groupes"]) if t in pas_indispo_yate[r])
        nb_actifs_yate  = max(0, 3 - nb_indispo_yate)
        min_tech_t     += nb_actifs_yate * yate["min_technique_groupe"]

        seuil = min(prod_enr[t], max(0.0, demande_dp[t] - min_tech_t))
        m += (enr_u_dp[t] >= seuil, f"ENR_priorite_dp_t{t}")

    return m


def ajouter_contrainte_equilibre_dp(nb_pas, m, prod_th_dp, prod_cat_dp, prod_yate_dp,
                                     prod_neaoua_dp, enr_u_dp, prod_bat_dp, centrales, neaoua, demande_dp):
    for t in range(nb_pas):
        m += (
            pulp.lpSum(prod_th_dp[ct, r, t] for ct in centrales for r in range(centrales[ct]["nb_groupes"]))
            + prod_cat_dp[t] + prod_yate_dp[t]
            + pulp.lpSum(prod_neaoua_dp[r, t] for r in range(neaoua["nb_groupes"]))
            + enr_u_dp[t] + prod_bat_dp[t]
            == demande_dp[t],
            f"Equilibre_dp_t{t}",
        )
    return m


def ajouter_contrainte_equilibre_sln(nb_pas, m, prod_th_sln, prod_cat_sln, prod_yate_sln_sous,
                                      prod_yate_sln_sup, prod_neaoua_sln, enr_u_sln, prod_bat_sln,
                                      centrales, neaoua, demande_sln):
    for t in range(nb_pas):
        m += (
            pulp.lpSum(prod_th_sln[ct, r, t] for ct in centrales for r in range(centrales[ct]["nb_groupes"]))
            + prod_cat_sln[t] + prod_yate_sln_sous[t] + prod_yate_sln_sup[t]
            + pulp.lpSum(prod_neaoua_sln[r, t] for r in range(neaoua["nb_groupes"]))
            + enr_u_sln[t] + prod_bat_sln[t]
            == demande_sln[t],
            f"Equilibre_sln_t{t}",
        )
    return m


def ajouter_contrainte_limite_transfo_doniambo(nb_pas, m, prod_th_sln, prod_yate_sln_sous,
                                               prod_yate_sln_sup, prod_neaoua_sln, enr_u_sln,
                                               prod_bat_sln, centrales, neaoua):
    for t in range(nb_pas):
        m += (
            pulp.lpSum(prod_th_sln[ct, r, t] for ct in centrales for r in range(centrales[ct]["nb_groupes"]))
            + prod_yate_sln_sous[t] + prod_yate_sln_sup[t]
            + pulp.lpSum(prod_neaoua_sln[r, t] for r in range(neaoua["nb_groupes"]))
            + enr_u_sln[t] + prod_bat_sln[t]
            <= 70,
            f"Max_injection_SLN_t{t}",
        )
    return m


def ajouter_contrainte_batterie_bornes(nb_pas, m, p_charge, p_decharge, u_charge, u_decharge, batt):
    for t in range(nb_pas):
        m += (p_charge[t]   <= batt["p_max"] * u_charge[t],   f"Borne_charge_t{t}")
        m += (p_decharge[t] <= batt["p_max"] * u_decharge[t], f"Borne_decharge_t{t}")
        m += (p_charge[t]   >= batt["p_min"] * u_charge[t],   f"P_min_charge_t{t}")
        m += (p_decharge[t] >= batt["p_min"] * u_decharge[t], f"P_min_decharge_t{t}")
    return m


def ajouter_contrainte_batterie_exclusion(nb_pas, m, u_charge, u_decharge):
    for t in range(nb_pas):
        m += (u_charge[t] + u_decharge[t] <= 1, f"Exclusion_charge_decharge_t{t}")
    return m


def ajouter_contrainte_batterie_stock(nb_pas, m, pas_h, p_charge, p_decharge, stock_batt, batt):
    rho             = batt["rho"]
    stock_batt_init = batt["stock_init"]
    for t in range(nb_pas):
        stock_prec = stock_batt_init if t == 0 else stock_batt[t - 1]
        m += (
            stock_batt[t] == stock_prec + (rho * p_charge[t] - p_decharge[t]) * pas_h,
            f"Bilan_stock_batt_t{t}",
        )
    return m


def ajouter_contrainte_batterie_repartition(nb_pas, m, p_decharge, prod_bat_dp, prod_bat_sln, batt):
    rho = batt["rho"]
    for t in range(nb_pas):
        m += (rho * p_decharge[t] == prod_bat_dp[t] + prod_bat_sln[t], f"Repartition_bat_t{t}")
    return m


def ajouter_contrainte_batterie_soc_min(nb_pas, m, stock_batt, batt):
    for t in range(nb_pas):
        m += (stock_batt[t] >= batt["e_min"], f"SOC_min_t{t}")
    return m


def ajouter_contrainte_batterie_soc_final(nb_pas, m, stock_batt, batt):
    m += (stock_batt[nb_pas - 1] >= batt["stock_fin_min"], "SOC_final_min")
    return m


def ajouter_contrainte_batterie_rampe(nb_pas, m, p_charge, p_decharge, batt):
    rampe           = batt["rampe_max"]
    p_charge_init   = batt["p_charge_init"]
    p_decharge_init = batt["p_decharge_init"]
    for t in range(nb_pas):
        pc_prec = p_charge_init   if t == 0 else p_charge[t - 1]
        pd_prec = p_decharge_init if t == 0 else p_decharge[t - 1]
        m += (p_charge[t]   - pc_prec <=  rampe, f"Rampe_charge_mont_t{t}")
        m += (pc_prec - p_charge[t]   <=  rampe, f"Rampe_charge_desc_t{t}")
        m += (p_decharge[t] - pd_prec <=  rampe, f"Rampe_decharge_mont_t{t}")
        m += (pd_prec - p_decharge[t] <=  rampe, f"Rampe_decharge_desc_t{t}")
    return m


def ajouter_contrainte_lissage_batterie(nb_pas, m, p_charge, p_decharge,
                                         delta_charge, delta_decharge, batt):
    p_charge_init   = batt["p_charge_init"]
    p_decharge_init = batt["p_decharge_init"]
    for t in range(nb_pas):
        pc_prec = p_charge_init   if t == 0 else p_charge[t - 1]
        pd_prec = p_decharge_init if t == 0 else p_decharge[t - 1]
        m += (delta_charge[t]   >= p_charge[t]   - pc_prec, f"Lissage_charge_pos_t{t}")
        m += (delta_charge[t]   >= pc_prec - p_charge[t],   f"Lissage_charge_neg_t{t}")
        m += (delta_decharge[t] >= p_decharge[t] - pd_prec, f"Lissage_decharge_pos_t{t}")
        m += (delta_decharge[t] >= pd_prec - p_decharge[t], f"Lissage_decharge_desc_t{t}")
    return m


def ajouter_contrainte_cycles_batterie(nb_pas, pas_h, m, p_charge, p_decharge, batt):
    puissance_theorique_par_cycle = batt["e_max"] * 2
    m += (
        pas_h * pulp.lpSum(p_charge[t] + p_decharge[t] for t in range(nb_pas))
        <= batt["nb_cycles_max"] * puissance_theorique_par_cycle,
        "Limite_cycles_batterie",
    )
    return m


# =============================================================================
# Fonction objectif
# =============================================================================

def ajouter_fonction_objectif(nb_pas, pas_h, m,
                               prod_th_dp, prod_th_sln,
                               prod_cat_dp, prod_cat_sln,
                               prod_yate, prod_yate_dp, prod_yate_sln_sous, prod_yate_sln_sup,
                               prod_neaoua_dp, prod_neaoua_sln,
                               v_th, v_yate, v_neaoua,
                               enr_u_dp, enr_u_sln, enr_bridee,
                               p_charge_enr, p_charge_th, p_charge_cat, p_charge_yate, p_charge_neaoua,
                               p_charge, p_decharge, prod_bat_sln,
                               delta_charge, delta_decharge,
                               cout_br, prix_achat_sln_enr,
                               centrales, cat, yate, neaoua, batt):

    cout_th_prop = pulp.lpSum(
        centrales[ct]["cout_prop"] * (prod_th_dp[ct, r, t] + prod_th_sln[ct, r, t] + p_charge_th[ct, r, t]) * pas_h
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)
    )
    cout_th_demarrage = pulp.lpSum(
        centrales[ct]["cout_demarrage"] * v_th[ct, r, t]
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)
    )
    cout_yate_opp = pulp.lpSum(
        yate["cout_opp"] * (prod_yate[r, t]) * pas_h
        for r in range(yate["nb_groupes"]) for t in range(nb_pas)
    )
    cout_yate_demarrage = pulp.lpSum(
        yate["cout_demarrage"] * v_yate[r, t]
        for r in range(yate["nb_groupes"]) for t in range(nb_pas)
    )
    cout_neaoua_opp = pulp.lpSum(
        neaoua["cout_opp"] * (prod_neaoua_dp[r, t] + prod_neaoua_sln[r, t] + p_charge_neaoua[r, t]) * pas_h
        for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)
    )
    cout_neaoua_demarrage = pulp.lpSum(
        neaoua["cout_demarrage"] * v_neaoua[r, t]
        for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)
    )


    cout_achat_enl_cat = pulp.lpSum(
        cat["prix_achat_enl"] * (prod_cat_dp[t] + p_charge_cat[t]) * pas_h for t in range(nb_pas)
    )
    # Bridage : pénalise directement la variable enr_bridee (toujours >= 0)
    cout_bridage = pulp.lpSum(
        cout_br * enr_bridee[t] * pas_h for t in range(nb_pas)
    )
    cout_batterie = pulp.lpSum(
        batt["cout_cycle"] * (p_decharge[t] + p_charge[t]) * pas_h for t in range(nb_pas)
    )
    cout_lissage = pulp.lpSum(
        batt["cout_lissage"] * (delta_charge[t] + delta_decharge[t]) for t in range(nb_pas)
    )
    cout_enl = (
        cout_th_prop + cout_th_demarrage
        + cout_yate_opp + cout_yate_demarrage
        + cout_neaoua_opp + cout_neaoua_demarrage
        + cout_achat_enl_cat + cout_bridage
        + cout_batterie + cout_lissage
    )

    cout_cat_marginal = pulp.lpSum(
        cat["cout_prop"] * (prod_cat_dp[t] + prod_cat_sln[t] + p_charge_cat[t]) * pas_h for t in range(nb_pas)
    )
    cout_achat_sln_th = pulp.lpSum(
        centrales[ct]["prix_achat_sln"] * prod_th_sln[ct, r, t] * pas_h
        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)
    )
    cout_achat_sln_yate_sous = pulp.lpSum(
        yate["prix_achat_sln_yate"] * prod_yate_sln_sous[t] * pas_h for t in range(nb_pas)
    )
    cout_achat_sln_yate_sup = pulp.lpSum(
        yate["prix_achat_sln_yate_hs"] * prod_yate_sln_sup[t] * pas_h for t in range(nb_pas)
    )
    cout_achat_sln_neaoua = pulp.lpSum(
        neaoua["prix_achat_sln"] * prod_neaoua_sln[r, t] * pas_h
        for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)
    )
    cout_achat_sln_enr = pulp.lpSum(
        prix_achat_sln_enr * (enr_u_sln[t] + prod_bat_sln[t]) * pas_h for t in range(nb_pas)
    )

    cout_achat_sln_batt = pulp.lpSum(
            50000 * (prod_bat_sln[t]) * pas_h for t in range(nb_pas)
        )
    
    cout_sln = (
        cout_cat_marginal + cout_achat_sln_th
        + cout_achat_sln_neaoua + cout_achat_sln_enr + cout_achat_sln_batt
        + cout_achat_sln_yate_sous + cout_achat_sln_yate_sup
    )

    m += (cout_enl + cout_sln, "Cout_total")
    return m


# =============================================================================
# Résolution
# =============================================================================

def resoudre_probleme(nb_pas, pas_h, centrales, cat, yate, neaoua,
                      prod_enr, demande_dp, demande_sln,
                      cout_br, prix_achat_sln_enr, batt, e_cin_min_reseau):

    (
        m,
        prod_th_dp, prod_th_sln, u_th, v_th,
        prod_cat_dp, prod_cat_sln,
        prod_yate, prod_yate_dp, prod_yate_sln_sous, prod_yate_sln_sup, delta_sln_sup,
        u_yate, v_yate,
        prod_neaoua_dp, prod_neaoua_sln, u_neaoua, v_neaoua,
        enr_u_dp, enr_u_sln, enr_bridee,
        p_charge_enr, p_charge_th, p_charge_cat, p_charge_yate, p_charge_neaoua,
        p_charge, p_decharge, u_charge, u_decharge, stock_batt,
        prod_bat_dp, prod_bat_sln,
        delta_decharge, delta_charge,
    ) = creer_modele_et_variables(nb_pas, centrales, cat, yate, neaoua, prod_enr, batt)

    m = ajouter_contrainte_bornes_groupe_th(nb_pas, m, prod_th_dp, prod_th_sln, p_charge_th, u_th, centrales)
    # m = ajouter_contrainte_bornes_cat(nb_pas, m, prod_cat_dp, prod_cat_sln, p_charge_cat, cat)
    m = ajouter_contrainte_bornes_cat(nb_pas, m, prod_cat_dp, prod_cat_sln, p_charge_cat,
                                   u_th, u_yate, u_neaoua,
                                   centrales, yate, neaoua, cat,
                                   e_cin_min_reseau)
    # m = ajouter_contrainte_min_cat(nb_pas, m, prod_cat_dp, prod_cat_sln, p_charge_cat)
    m = ajouter_contrainte_bornes_groupe_yate(nb_pas, m, prod_yate, u_yate, yate)
    m = ajouter_contrainte_bornes_groupe_neaoua(nb_pas, m, prod_neaoua_dp, prod_neaoua_sln, p_charge_neaoua, u_neaoua, neaoua)
    m = ajouter_contrainte_groupes_toujours_actifs(nb_pas, pas_h, m, u_th, u_yate, centrales, yate)
    m = ajouter_contrainte_indispos(m, nb_pas, pas_h, centrales, yate, neaoua, u_th, u_yate, u_neaoua)
    m = ajouter_contrainte_lien_production_yate(nb_pas, m, prod_yate, prod_yate_dp, prod_yate_sln_sous,
                                                prod_yate_sln_sup, p_charge_yate, yate)
    m = ajouter_contrainte_repartition_yate(nb_pas, m, prod_yate_dp, prod_yate_sln_sup, p_charge_yate, yate)
    m = ajouter_contrainte_seuil_sln_sup(nb_pas, m, prod_yate_sln_sous, prod_yate_sln_sup, delta_sln_sup, yate)
    m = ajouter_contrainte_demarrage(nb_pas, m, u_th, u_yate, u_neaoua, v_th, v_yate, v_neaoua,
                                     centrales, yate, neaoua)
    m = ajouter_contrainte_bilan_enr(nb_pas, m, enr_u_dp, enr_u_sln, p_charge_enr, enr_bridee, prod_enr)
    m = ajouter_contrainte_lien_charge_batterie(nb_pas, m, p_charge, p_charge_enr, p_charge_th,
                                                p_charge_cat, p_charge_yate, p_charge_neaoua,
                                                centrales, yate, neaoua)
    m = ajouter_contrainte_enr_priorite_dp(nb_pas, pas_h, m, enr_u_dp, prod_enr, demande_dp, centrales, yate)
    m = ajouter_contrainte_equilibre_dp(nb_pas, m, prod_th_dp, prod_cat_dp, prod_yate_dp,
                                        prod_neaoua_dp, enr_u_dp, prod_bat_dp, centrales, neaoua, demande_dp)
    m = ajouter_contrainte_equilibre_sln(nb_pas, m, prod_th_sln, prod_cat_sln,
                                         prod_yate_sln_sous, prod_yate_sln_sup,
                                         prod_neaoua_sln, enr_u_sln, prod_bat_sln,
                                         centrales, neaoua, demande_sln)
    m = ajouter_contrainte_limite_transfo_doniambo(nb_pas, m, prod_th_sln, prod_yate_sln_sous,
                                                   prod_yate_sln_sup, prod_neaoua_sln, enr_u_sln,
                                                   prod_bat_sln, centrales, neaoua)
    m = ajouter_contrainte_batterie_bornes(nb_pas, m, p_charge, p_decharge, u_charge, u_decharge, batt)
    m = ajouter_contrainte_batterie_exclusion(nb_pas, m, u_charge, u_decharge)
    m = ajouter_contrainte_batterie_stock(nb_pas, m, pas_h, p_charge, p_decharge, stock_batt, batt)
    m = ajouter_contrainte_batterie_repartition(nb_pas, m, p_decharge, prod_bat_dp, prod_bat_sln, batt)
    m = ajouter_contrainte_batterie_soc_min(nb_pas, m, stock_batt, batt)
    m = ajouter_contrainte_batterie_soc_final(nb_pas, m, stock_batt, batt)
    m = ajouter_contrainte_batterie_rampe(nb_pas, m, p_charge, p_decharge, batt)
    m = ajouter_contrainte_lissage_batterie(nb_pas, m, p_charge, p_decharge, delta_charge, delta_decharge, batt)
    m = ajouter_contrainte_cycles_batterie(nb_pas, pas_h, m, p_charge, p_decharge, batt)

    m = ajouter_fonction_objectif(nb_pas, pas_h, m,
                                   prod_th_dp, prod_th_sln, prod_cat_dp, prod_cat_sln,
                                   prod_yate, prod_yate_dp, prod_yate_sln_sous, prod_yate_sln_sup,
                                   prod_neaoua_dp, prod_neaoua_sln,
                                   v_th, v_yate, v_neaoua,
                                   enr_u_dp, enr_u_sln, enr_bridee,
                                   p_charge_enr, p_charge_th, p_charge_cat, p_charge_yate, p_charge_neaoua,
                                   p_charge, p_decharge, prod_bat_sln,
                                   delta_charge, delta_decharge,
                                   cout_br, prix_achat_sln_enr,
                                   centrales, cat, yate, neaoua, batt)

    m.solve(pulp.PULP_CBC_CMD(msg=1, timeLimit = 200, gapRel=0.05))
    print("Statut:", pulp.LpStatus[m.status])
        
    
    prod_th_dp_val  = {(ct, r, t): pulp.value(prod_th_dp[ct, r, t])  for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)}
    prod_th_sln_val = {(ct, r, t): pulp.value(prod_th_sln[ct, r, t]) for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)}
    u_th_val        = {(ct, r, t): pulp.value(u_th[ct, r, t])        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)}
    v_th_val        = {(ct, r, t): pulp.value(v_th[ct, r, t])        for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)}

    prod_cat_dp_val  = {t: pulp.value(prod_cat_dp[t])  for t in range(nb_pas)}
    prod_cat_sln_val = {t: pulp.value(prod_cat_sln[t]) for t in range(nb_pas)}

    prod_yate_val          = {(r, t): pulp.value(prod_yate[r, t])       for r in range(yate["nb_groupes"]) for t in range(nb_pas)}
    prod_yate_dp_val       = {t:      pulp.value(prod_yate_dp[t])       for t in range(nb_pas)}
    prod_yate_sln_sous_val = {t:      pulp.value(prod_yate_sln_sous[t]) for t in range(nb_pas)}
    prod_yate_sln_sup_val  = {t:      pulp.value(prod_yate_sln_sup[t])  for t in range(nb_pas)}
    u_yate_val             = {(r, t): pulp.value(u_yate[r, t])          for r in range(yate["nb_groupes"]) for t in range(nb_pas)}
    v_yate_val             = {(r, t): pulp.value(v_yate[r, t])          for r in range(yate["nb_groupes"]) for t in range(nb_pas)}

    prod_neaoua_dp_val  = {(r, t): pulp.value(prod_neaoua_dp[r, t])  for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)}
    prod_neaoua_sln_val = {(r, t): pulp.value(prod_neaoua_sln[r, t]) for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)}
    u_neaoua_val        = {(r, t): pulp.value(u_neaoua[r, t])        for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)}
    v_neaoua_val        = {(r, t): pulp.value(v_neaoua[r, t])        for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)}

    enr_u_dp_val   = {t: pulp.value(enr_u_dp[t])   for t in range(nb_pas)}
    enr_u_sln_val  = {t: pulp.value(enr_u_sln[t])  for t in range(nb_pas)}
    enr_bridee_val = {t: pulp.value(enr_bridee[t])  for t in range(nb_pas)}

    p_charge_enr_val    = {t:          pulp.value(p_charge_enr[t])       for t in range(nb_pas)}
    p_charge_th_val     = {(ct, r, t): pulp.value(p_charge_th[ct, r, t])
                           for ct in centrales for r in range(centrales[ct]["nb_groupes"]) for t in range(nb_pas)}
    p_charge_cat_val    = {t:          pulp.value(p_charge_cat[t])       for t in range(nb_pas)}
    p_charge_yate_val   = {(r, t):     pulp.value(p_charge_yate[r, t])
                           for r in range(yate["nb_groupes"]) for t in range(nb_pas)}
    p_charge_neaoua_val = {(r, t):     pulp.value(p_charge_neaoua[r, t])
                           for r in range(neaoua["nb_groupes"]) for t in range(nb_pas)}

    p_charge_val     = {t: pulp.value(p_charge[t])     for t in range(nb_pas)}
    p_decharge_val   = {t: pulp.value(p_decharge[t])   for t in range(nb_pas)}
    u_charge_val     = {t: pulp.value(u_charge[t])     for t in range(nb_pas)}
    u_decharge_val   = {t: pulp.value(u_decharge[t])   for t in range(nb_pas)}
    stock_batt_val   = {t: pulp.value(stock_batt[t])   for t in range(nb_pas)}
    prod_bat_dp_val  = {t: pulp.value(prod_bat_dp[t])  for t in range(nb_pas)}
    prod_bat_sln_val = {t: pulp.value(prod_bat_sln[t]) for t in range(nb_pas)}

    delta_charge_val   = {t: pulp.value(delta_charge[t])   for t in range(nb_pas)}
    delta_decharge_val = {t: pulp.value(delta_decharge[t]) for t in range(nb_pas)}


    


    return (
        pulp.value(m.objective),
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
    )