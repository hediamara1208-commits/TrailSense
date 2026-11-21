"""Paramètres globaux. Un seul endroit pour les régler pendant la démo."""

# Zone surveillée : élargie à l'est le 21/11 (aucun vol signalé sur le Québec seul la 1re nuit).
# ~224 degrés carrés = 3 crédits OpenSky par appel (au lieu de 2) : ~860 crédits/jour à 1 appel / 5 min.
BBOX = {"lamin": 44.0, "lamax": 52.0, "lomin": -80.0, "lomax": -52.0}  # Québec + golfe du Saint-Laurent + Terre-Neuve (entrée de l'Atlantique Nord, plus humide)

# Niveaux de pression GFS disponibles sur Open-Meteo autour de l'altitude de croisière
# 350 hPa (≈ FL265) pour que FL290-300 soient encadrés. 200 hPa ≈ FL385 : on ajoute 175 (≈ FL420) et 150 pour couvrir FL390-410 et la montée.
# À vérifier par un appel test sur Open-Meteo GFS (la doc liste 300, 275, 250, 225, 200, 175, 150).
PRESSURE_LEVELS_HPA = [350, 300, 275, 250, 225, 200, 175, 150]

# Convention de l'humidité GFS à ces températures : "water" ou "ice". À fixer après vérification
# (D3). Si "ice", physics ne refait PAS la conversion eau -> glace.
RH_CONVENTION = "ice"  # provisoire : RH = 100 % pile à -49,5 °C (si /eau -> ~155 % /glace, irréaliste)

# On n'analyse que les avions en croisière (FL290-FL410, zone RVSM)
MIN_FLIGHT_LEVEL = 290
MAX_FLIGHT_LEVEL = 410
# Avions en montée/descente exclus : |vertical_rate| > 2,5 m/s (~500 ft/min) = pas en croisière
MAX_VERTICAL_RATE_MS = 2.5

# Décalage proposé : 2 000 ft = 20 FL, garde la parité est/ouest
LEVEL_STEP = 20

# Cache météo : taille de cellule (degrés) et durée de validité (secondes)
WEATHER_CELL_DEG = 0.5
WEATHER_TTL_S = 3600

# Seuil d'autonomie par défaut (curseur dans l'interface)
DEFAULT_THRESHOLD = 0.8

# Cascade de rédaction des avis : gabarit -> Granite local -> Cloud LLM
MAX_CLOUD_LLM_ADVISORIES = 2      # seulement les plus importants
MAX_GRANITE_ADVISORIES = 5     # avis courants, rédigés en local
USE_GRANITE = True             # False si Ollama/Granite ne marche pas : on passe directement à gabarit/Cloud LLM
OLLAMA_URL = "http://localhost:11434"
GRANITE_MODEL = "granite4:micro"   # nom exact à vérifier avec `ollama list` après `ollama pull`
CLOUD_LLM_MODEL = "cloud_llm-haiku-5-5"  # petit modèle, assez pour rédiger un avis court

# Intervalle de rafraîchissement en mode live (secondes, OpenSky anonyme = 10 s mini)
REFRESH_S = 30

# Enregistrement de nuit : la boîte fait ~96 degrés carrés = 2 crédits OpenSky par appel.
# En anonyme, un appel toutes les 30 s épuise les crédits en ~1 h 40.
# -> créer un compte OpenSky gratuit, et une capture toutes les 2 à 5 min.
RECORD_S = 300
# Météo : une fois par heure suffit (GFS n'est mis à jour que toutes les 6 h)
RECORD_WEATHER_INTERVAL_S = 7200
# Météo enregistrée sur une grille fixe couvrant toute la BBOX (pas seulement les cellules des avions),
# pour que chaque avion rejoué ait un profil. 1° -> 9 × 29 = 261 points = 3 appels groupés.
# Open-Meteo gratuit = 10 000 appels/jour, pondérés par nb de points et de variables (24 var. ≈ ×2,4)
# -> ~630 « appels » par grille : une grille toutes les 2 h (RECORD_WEATHER_INTERVAL_S) ≈ 7 500/jour.
RECORD_GRID_DEG = 1.0

# Benchmark tout-LLM : limité pour ne pas exploser le coût
BENCHMARK_MAX_FLIGHTS = 20

# Plan B : si Jev est indisponible (API en panne, accès anticipé bloqué), on bascule sur la règle codée
USE_JEV = True


# ---------- Physique (Dawud) : toutes les hypothèses réglables, documentées dans docs/hypotheses.md ----------
# Persistance : RHi >= seuil. GFS plafonne à 100 % et sous-estime la sursaturation -> 95 % (choix de réglage).
RHI_THRESHOLD = 95.0
# Rendement propulsif global pour le critère de Schmidt-Appleman (moteurs modernes ~0,3-0,4)
SAC_ETA = 0.35
# Niveaux de vol envisageables pour une option ±2 000 ft
OPTION_MIN_FL = 280
OPTION_MAX_FL = 430
# Longueur typique d'une zone sursaturée traversée (Gierens & Spichtinger 2000 : ~150 km en moyenne)
ISSR_TYPICAL_KM = 150.0
# Consommation de croisière générique (type d'avion inconnu dans OpenSky) : mélange monocouloirs / gros porteurs
CRUISE_FUEL_FLOW_KG_H = 3000.0
# Surconsommation hors niveau optimal pendant la déviation (ordre de grandeur des essais publiés : ~2 %)
FUEL_PENALTY_PCT = {"climb": 1.5, "descend": 2.0}
# Réchauffement d'un contrail persistant, en kg CO2e (horizon 100 ans) par km de contrail.
# ESTIMATION LA PLUS INCERTAINE DU PROJET : ordre de grandeur, fourchette x0,3 à x3 affichée.
# La nuit compte plus : le contrail piège la chaleur sans réfléchir le soleil.
CONTRAIL_CO2E_KG_PER_KM = {"night": 100.0, "day": 40.0}
CONTRAIL_UNCERTAINTY_FACTOR = 3.0
