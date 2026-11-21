"""Global settings. One place to tune everything during the demo."""

# Monitored area: Quebec, Gulf of St. Lawrence, Newfoundland, Labrador (transatlantic corridor).
# Widened east then north on 2026-11-21: Quebec alone was too dry on the first night;
# ice-supersaturated layers were mostly around 50-52°N.
# ~288 square degrees = 3 OpenSky credits per call: ~860 credits/day at one call every 5 min.
BBOX = {"lamin": 44.0, "lamax": 56.0, "lomin": -76.0, "lomax": -52.0}

# GFS pressure levels on Open-Meteo around cruise altitude (all verified to exist).
# 350 hPa (≈ FL265) brackets FL290-300; 175 (≈ FL420) and 150 cover FL390-410 and climbs.
PRESSURE_LEVELS_HPA = [350, 300, 275, 250, 225, 200, 175, 150]

# GFS humidity convention at these temperatures: "water" or "ice".
# Confirmed "ice" (capped at 100 %): on the overnight recording, values pile up at 80-100 % and never
# exceed 100. Exactly 100 % at -49.5 °C would mean ~155 % over ice if it were over water (unphysical).
# With "ice", physics does NOT convert water -> ice again.
RH_CONVENTION = "ice"

# Only cruising aircraft are analysed (FL290-FL410, RVSM airspace)
MIN_FLIGHT_LEVEL = 290
MAX_FLIGHT_LEVEL = 410
# Climbing/descending aircraft excluded: |vertical_rate| > 2.5 m/s (~500 ft/min) = not in cruise
MAX_VERTICAL_RATE_MS = 2.5

# Proposed shift: 2,000 ft = 20 FL, keeps the east/west (odd/even) level parity
LEVEL_STEP = 20

# Weather cache: cell size (degrees) and time to live (seconds)
WEATHER_CELL_DEG = 0.5
WEATHER_TTL_S = 3600

# Default autonomy threshold (slider in the UI)
DEFAULT_THRESHOLD = 0.8

# Advisory writing cascade: template -> local Granite -> Cloud LLM
MAX_CLOUD_LLM_ADVISORIES = 2      # only the most important ones
MAX_GRANITE_ADVISORIES = 5     # routine advisories, written locally
USE_GRANITE = True             # False if Ollama/Granite does not work: go straight to template/Cloud LLM
OLLAMA_URL = "http://localhost:11434"
GRANITE_MODEL = "granite4:micro"   # check the exact name with `ollama list` after `ollama pull`
CLOUD_LLM_MODEL = "cloud_llm-haiku-5-5"  # small model, enough to write a short advisory

# Live mode refresh interval (seconds; anonymous OpenSky = 10 s minimum)
REFRESH_S = 30

# Night recording: one aircraft snapshot every RECORD_S (free OpenSky account required).
RECORD_S = 300
# Weather recorded on a fixed grid covering the whole BBOX (not just the aircraft cells),
# so every replayed aircraft has a profile. 1° -> 13 × 25 = 325 points = 4 grouped calls.
# Open-Meteo free tier = 10,000 calls/day, weighted by points and variables (24 vars ≈ ×2.4)
# -> ~780 "calls" per grid: one grid every 3 h ≈ 6,300/day. GFS only updates every 6 h anyway.
RECORD_WEATHER_INTERVAL_S = 10800
RECORD_GRID_DEG = 1.0

# All-LLM benchmark: capped to keep the cost down
BENCHMARK_MAX_FLIGHTS = 20

# Plan B: if Jev is unavailable (API down, early access blocked), switch to the hard-coded rule
USE_JEV = True


# ---------- Physics (Dawud): every tunable assumption, documented in docs/hypotheses.md ----------
# Persistence: RHi >= threshold. GFS caps at 100 % and underestimates supersaturation -> 95 % (tuning choice).
RHI_THRESHOLD = 95.0
# Overall propulsive efficiency for the Schmidt-Appleman criterion (modern engines ~0.3-0.4)
SAC_ETA = 0.35
# Flight levels allowed for a ±2,000 ft option
OPTION_MIN_FL = 280
OPTION_MAX_FL = 430
# Fallback length of an ice-supersaturated region when no weather grid is available
# (Gierens & Spichtinger 2000: ~150 km on average along flight tracks)
ISSR_TYPICAL_KM = 150.0
# Generic cruise fuel flow (aircraft type unknown in OpenSky): mix of narrow-body and wide-body
CRUISE_FUEL_FLOW_KG_H = 3000.0
# Extra fuel burn off the optimal level during the deviation (published trials: ~2 %)
FUEL_PENALTY_PCT = {"climb": 1.5, "descend": 2.0}
# Warming of a persistent contrail, in kg CO2e (100-year horizon) per km of contrail.
# MOST UNCERTAIN ESTIMATE OF THE PROJECT, shown with a ÷3 to ×3 range. Derived from Borella et al. (ACP 2024):
# mean energy forcing ~9.6e10 J per flown km (contrail-forming flights), efficacy 0.37,
# CO2 AGWP100 ≈ 1.48e9 J/kg -> ~24 kg CO2e/km on average, day and night. See docs/hypotheses.md.
# Night weighs more: the contrail traps heat without reflecting sunlight.
CONTRAIL_CO2E_KG_PER_KM = {"night": 50.0, "day": 15.0}
CONTRAIL_UNCERTAINTY_FACTOR = 3.0
