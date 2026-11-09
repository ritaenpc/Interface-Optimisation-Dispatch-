import numpy as np

def hhmm_to_h(s):
    hh, mm = s.split(":")
    return int(hh) + int(mm) / 60

def construire_pas_indispo(params, nb_pas, pas_h):
    indispos = params.get("indispos", {})
    result = {}
    for r in range(params["nb_groupes"]):
        plage = indispos.get(r)
        if plage is not None:
            # Normaliser en liste de tuples (h_debut, h_fin)
            # Ancien format : (h_debut, h_fin)
            # Nouveau format : [(h_debut, h_fin), (h_debut, h_fin), ...]
            if isinstance(plage, tuple):
                plages = [plage]
            else:
                plages = plage

            plages_h = []
            for h_debut, h_fin in plages:
                if isinstance(h_debut, str):
                    h_debut = hhmm_to_h(h_debut)
                if isinstance(h_fin, str):
                    h_fin = hhmm_to_h(h_fin)
                plages_h.append((h_debut, h_fin))

            result[r] = [
                t for t in range(nb_pas)
                if any(h_debut <= t * pas_h < h_fin for (h_debut, h_fin) in plages_h)
            ]
        else:
            result[r] = []
    return result

def construire_p_max_cat(cat, nb_pas, pas_h):
    nb_groupes_total = cat["nb_groupes"]
    p_max_groupe     = cat["p_max_groupe"]
    indispos         = [(hhmm_to_h(a), hhmm_to_h(b)) for (a, b) in cat.get("indispos", [])]

    p_max_t = []
    for t in range(nb_pas):
        h = t * pas_h
        nb_indispo = sum(1 for (h_debut, h_fin) in indispos if h_debut <= h < h_fin)
        nb_dispo = max(0, nb_groupes_total - nb_indispo)
        p_max_t.append(nb_dispo * p_max_groupe)

    return p_max_t


