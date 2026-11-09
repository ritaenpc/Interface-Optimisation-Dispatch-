import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.model import resoudre_probleme
from output.visualize_results import visualiser_production, visualiser_production_batterie, visualiser_activation_ct, visualiser_batterie
from output.create_table import exporter_resultats_excel
from output.visualize_costs import visualiser_couts



from instances import (
    NB_PAS, PAS_H,
    CENTRALES, CAT, YATE, NEAOUA, ENR, BATT,
    DEMANDE_DP, DEMANDE_SLN,
    COUT_BR, PRIX_ACHAT_SLN_ENR, E_CIN_MIN
)
 


# =============================================================================
# Résolution
# =============================================================================

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
) = resoudre_probleme(
    nb_pas             = NB_PAS,
    pas_h              = PAS_H,
    centrales          = CENTRALES,
    cat                = CAT,
    yate               = YATE,
    neaoua             = NEAOUA,
    prod_enr           = ENR,
    demande_dp         = DEMANDE_DP,
    demande_sln        = DEMANDE_SLN,
    cout_br            = COUT_BR,
    prix_achat_sln_enr = PRIX_ACHAT_SLN_ENR,
    batt               = BATT,
    e_cin_min_reseau   = E_CIN_MIN
)

print(f"Coût total : {cout_total:,.0f} F")



# =============================================================================
# Visualisation
# =============================================================================

visualiser_production(
    nb_pas                 = NB_PAS,
    pas_h                  = PAS_H,
    centrales              = CENTRALES,
    yate                   = YATE,
    neaoua                 = NEAOUA,
    prod_th_dp_val         = prod_th_dp_val,
    prod_th_sln_val        = prod_th_sln_val,
    prod_cat_dp_val        = prod_cat_dp_val,
    prod_cat_sln_val       = prod_cat_sln_val,
    prod_yate_dp_val       = prod_yate_dp_val,
    prod_yate_sln_sous_val = prod_yate_sln_sous_val,
    prod_yate_sln_sup_val  = prod_yate_sln_sup_val,
    prod_neaoua_dp_val     = prod_neaoua_dp_val,
    prod_neaoua_sln_val    = prod_neaoua_sln_val,
    enr_u_dp_val           = enr_u_dp_val,
    enr_u_sln_val          = enr_u_sln_val,
    enr_bridee_val         = enr_bridee_val,
    prod_bat_dp_val        = prod_bat_dp_val,
    prod_bat_sln_val       = prod_bat_sln_val,
    p_charge_val           = p_charge_val,
    prod_enr               = ENR,
    demande_dp             = DEMANDE_DP,
    demande_sln            = DEMANDE_SLN,
    p_charge_enr_val       = p_charge_enr_val,
    p_charge_yate_val      = p_charge_yate_val,
    p_charge_neaoua_val    = p_charge_neaoua_val,
    p_charge_th_val        = p_charge_th_val,
    p_charge_cat_val       = p_charge_cat_val,
)

visualiser_production_batterie(
    nb_pas                 = NB_PAS,
    pas_h                  = PAS_H,
    centrales              = CENTRALES,
    yate                   = YATE,
    neaoua                 = NEAOUA,
    prod_th_dp_val         = prod_th_dp_val,
    prod_th_sln_val        = prod_th_sln_val,
    prod_cat_dp_val        = prod_cat_dp_val,
    prod_cat_sln_val       = prod_cat_sln_val,
    prod_yate_dp_val       = prod_yate_dp_val,
    prod_yate_sln_sous_val = prod_yate_sln_sous_val,
    prod_yate_sln_sup_val  = prod_yate_sln_sup_val,
    prod_neaoua_dp_val     = prod_neaoua_dp_val,
    prod_neaoua_sln_val    = prod_neaoua_sln_val,
    enr_u_dp_val           = enr_u_dp_val,
    enr_u_sln_val          = enr_u_sln_val,
    enr_bridee_val         = enr_bridee_val,
    prod_bat_dp_val        = prod_bat_dp_val,
    prod_bat_sln_val       = prod_bat_sln_val,
    p_charge_val           = p_charge_val,
    prod_enr               = ENR,
    demande_dp             = DEMANDE_DP,
    demande_sln            = DEMANDE_SLN,
    p_charge_enr_val       = p_charge_enr_val,
    p_charge_yate_val      = p_charge_yate_val,
    p_charge_neaoua_val    = p_charge_neaoua_val,
    p_charge_th_val        = p_charge_th_val,
    p_charge_cat_val       = p_charge_cat_val,
    chemin_sortie          = "mix_production_batterie.png",
)

# visualiser_activation_ct(
#     nb_pas        = NB_PAS,
#     pas_h         = PAS_H,
#     centrales     = CENTRALES,
#     yate          = YATE,
#     neaoua        = NEAOUA,
#     u_th_val      = u_th_val,
#     u_yate_val    = u_yate_val,
#     u_neaoua_val  = u_neaoua_val,
# )

visualiser_batterie(
    nb_pas         = NB_PAS,
    pas_h          = PAS_H,
    stock_batt_val = stock_batt_val,
    p_charge_val   = p_charge_val,
    p_decharge_val = p_decharge_val,
    batt           = BATT,
)

# =============================================================================
# Exportation des résultats dans un fichier excel
# =============================================================================

exporter_resultats_excel(
    nb_pas                 = NB_PAS,
    pas_h                  = PAS_H,
    centrales              = CENTRALES,
    cat                    = CAT,
    yate                   = YATE,
    neaoua                 = NEAOUA,
    prod_th_dp_val         = prod_th_dp_val,
    prod_th_sln_val        = prod_th_sln_val,
    prod_cat_dp_val        = prod_cat_dp_val,
    prod_cat_sln_val       = prod_cat_sln_val,
    prod_yate_val          = prod_yate_val,
    prod_yate_dp_val       = prod_yate_dp_val,
    prod_yate_sln_sous_val = prod_yate_sln_sous_val,
    prod_yate_sln_sup_val  = prod_yate_sln_sup_val,
    prod_neaoua_dp_val     = prod_neaoua_dp_val,
    prod_neaoua_sln_val    = prod_neaoua_sln_val,
    v_th_val               = v_th_val,
    v_yate_val             = v_yate_val,
    v_neaoua_val           = v_neaoua_val,
    enr_u_dp_val           = enr_u_dp_val,
    enr_u_sln_val          = enr_u_sln_val,
    enr_bridee_val         = enr_bridee_val,
    prod_enr               = ENR,
    cout_br                = COUT_BR,
    prix_achat_sln_enr     = PRIX_ACHAT_SLN_ENR,
    demande_dp             = DEMANDE_DP,
    demande_sln            = DEMANDE_SLN,
    stock_batt_val         = stock_batt_val,
    p_charge_val           = p_charge_val,
    p_decharge_val         = p_decharge_val,
    batt                   = BATT,
    p_charge_enr_val       = p_charge_enr_val,
    p_charge_th_val        = p_charge_th_val,
    p_charge_cat_val       = p_charge_cat_val,
    p_charge_yate_val      = p_charge_yate_val,
    p_charge_neaoua_val    = p_charge_neaoua_val,
    prod_bat_dp_val        = prod_bat_dp_val,
    prod_bat_sln_val       = prod_bat_sln_val,
    delta_charge_val       = delta_charge_val,
    delta_decharge_val     = delta_decharge_val,
)