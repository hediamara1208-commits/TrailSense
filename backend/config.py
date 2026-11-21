"""Paramètres globaux. Un seul endroit pour les régler pendant la démo."""

# Zone surveillée : boîte autour du Québec / sud de l'Ontario (à ajuster)
BBOX = {"lamin": 44.0, "lamax": 50.0, "lomin": -80.0, "lomax": -64.0}

# Niveaux de pression GFS disponibles sur Open-Meteo autour de l'altitude de croisière
# 200 hPa ≈ FL385 : on ajoute 175 (≈ FL420) et 150 pour couvrir FL390-410 et la montée.
# À vérifier par un appel test sur Open-Meteo GFS (la doc liste 300, 275, 250, 225, 200, 175, 150).
PRESSURE_LEVELS_HPA = [300, 275, 250, 225, 200, 175, 150]

# Convention de l'humidité GFS à ces températures : "water" ou "ice". À fixer après vérification
# (D3). Si "ice", physics ne refait PAS la conversion eau -> glace.
RH_CONVENTION = "unknown"

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
RECORD_WEATHER_INTERVAL_S = 3600
# Météo enregistrée sur une grille fixe couvrant toute la BBOX (pas seulement les cellules des avions),
# pour que chaque avion rejoué ait un profil. 1° -> 7 × 17 = 119 points ≈ 2 appels groupés par heure.
# (Open-Meteo gratuit = 10 000 appels/jour, pondérés par nb de points et de variables : ~6 000/jour ici.)
RECORD_GRID_DEG = 1.0

# Benchmark tout-LLM : limité pour ne pas exploser le coût
BENCHMARK_MAX_FLIGHTS = 20

# Plan B : si Jev est indisponible (API en panne, accès anticipé bloqué), on bascule sur la règle codée
USE_JEV = True
