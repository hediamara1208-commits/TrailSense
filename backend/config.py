"""Paramètres globaux. Un seul endroit pour les régler pendant la démo."""

# Zone surveillée : boîte autour du Québec / sud de l'Ontario (à ajuster)
BBOX = {"lamin": 44.0, "lamax": 50.0, "lomin": -80.0, "lomax": -64.0}

# Niveaux de pression GFS disponibles sur Open-Meteo autour de l'altitude de croisière
PRESSURE_LEVELS_HPA = [300, 275, 250, 225, 200]

# On n'analyse que les avions en croisière (FL290-FL410, zone RVSM)
MIN_FLIGHT_LEVEL = 290
MAX_FLIGHT_LEVEL = 410

# Décalage proposé : 2 000 ft = 20 FL, garde la parité est/ouest
LEVEL_STEP = 20

# Cache météo : taille de cellule (degrés) et durée de validité (secondes)
WEATHER_CELL_DEG = 0.5
WEATHER_TTL_S = 3600

# Seuil d'autonomie par défaut (curseur dans l'interface)
DEFAULT_THRESHOLD = 0.8

# Nombre max d'avis rédigés par le LLM par cycle
MAX_LLM_ADVISORIES = 3

# Intervalle de rafraîchissement en mode live (secondes, OpenSky anonyme = 10 s mini)
REFRESH_S = 30
