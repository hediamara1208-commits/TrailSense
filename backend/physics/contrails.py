"""[DAWUD] Le cœur scientifique : ce contrail va-t-il se former, et va-t-il durer ?

Deux conditions (toutes les deux nécessaires pour un contrail persistant) :
1. Critère de Schmidt-Appleman (SAC) : le mélange gaz d'échappement + air ambiant
   devient saturé par rapport à l'eau. Pente de la droite de mélange (Pa/K) :
       G = EI_H2O * cp * p / (eps * Q * (1 - eta))
   EI_H2O = 1,23 kg/kg (kérosène), cp = 1004 J/kg/K, eps = 0,622, Q = 43,2e6 J/kg, eta ≈ 0,35.
   Température seuil (air sec) T_LM, approximation de Schumann (1996), éq. 31 :
       T_LM [°C] = -46,46 + 9,43 ln(G - 0,053) + 0,720 ln²(G - 0,053)
   Le contrail se forme si T < T_LM ET e_amb >= e_sat_eau(T_LM) - G (T_LM - T)
   (la droite de mélange croise la courbe de saturation de l'eau).
   Référence : Schumann (1996), "On conditions for contrail formation from aircraft exhausts".
2. Persistance : l'air ambiant est sursaturé par rapport à la glace (RHi >= config.RHI_THRESHOLD).

Pressions de saturation : formules de Sonntag (1994), T en K, résultat en hPa.
Niveau de vol -> pression : atmosphère standard ISA (un FL est une altitude-pression).

Limite à dire au jury : les modèles météo captent mal ces zones sursaturées,
donc on affiche des probabilités, pas des certitudes.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from backend import config
from backend.models import Aircraft, LevelRisk, RiskAssessment, WeatherProfile
from backend.physics import fuel

EI_H2O = 1.23
CP = 1004.0
EPS = 0.622
Q_FUEL = 43.2e6


# ---------- Thermodynamique ----------

def e_sat_water_hpa(temperature_c: float) -> float:
    """Pression de vapeur saturante par rapport à l'eau liquide (Sonntag 1994)."""
    t = temperature_c + 273.15
    return math.exp(-6096.9385 / t + 16.635794 - 2.711193e-2 * t
                    + 1.673952e-5 * t ** 2 + 2.433502 * math.log(t))


def e_sat_ice_hpa(temperature_c: float) -> float:
    """Pression de vapeur saturante par rapport à la glace (Sonntag 1994)."""
    t = temperature_c + 273.15
    return math.exp(-6024.5282 / t + 24.7219 + 1.0613868e-2 * t
                    - 1.3198825e-5 * t ** 2 - 0.49382577 * math.log(t))


def rh_ice(rh_pct: float, temperature_c: float) -> float:
    """Humidité relative par rapport à la glace, selon config.RH_CONVENTION.

    - "ice"   : rh_pct est déjà par rapport à la glace -> tel quel (pas de double conversion).
    - "water" : RHi = RHw * e_sat_eau(T) / e_sat_glace(T).
    """
    if config.RH_CONVENTION == "ice":
        return rh_pct
    return rh_pct * e_sat_water_hpa(temperature_c) / e_sat_ice_hpa(temperature_c)


def vapour_pressure_hpa(rh_pct: float, temperature_c: float) -> float:
    """Pression partielle de vapeur ambiante, quelle que soit la convention."""
    if config.RH_CONVENTION == "ice":
        return rh_pct / 100.0 * e_sat_ice_hpa(temperature_c)
    return rh_pct / 100.0 * e_sat_water_hpa(temperature_c)


def mixing_slope_pa_per_k(pressure_hpa: float, eta: float) -> float:
    return EI_H2O * CP * (pressure_hpa * 100.0) / (EPS * Q_FUEL * (1.0 - eta))


def sac_threshold_c(pressure_hpa: float, eta: float | None = None) -> float:
    """T_LM : au-dessus, aucun contrail ne peut se former, même en air saturé."""
    g = mixing_slope_pa_per_k(pressure_hpa, config.SAC_ETA if eta is None else eta)
    x = math.log(g - 0.053)
    return -46.46 + 9.43 * x + 0.720 * x * x


def sac_satisfied(temperature_c: float, pressure_hpa: float, rh_pct: float,
                  eta: float | None = None) -> bool:
    """True si le critère de Schmidt-Appleman est rempli (le contrail se forme)."""
    eta = config.SAC_ETA if eta is None else eta
    t_lm = sac_threshold_c(pressure_hpa, eta)
    if temperature_c >= t_lm:
        return False
    g_hpa = mixing_slope_pa_per_k(pressure_hpa, eta) / 100.0
    e_amb = vapour_pressure_hpa(rh_pct, temperature_c)
    return e_amb >= e_sat_water_hpa(t_lm) - g_hpa * (t_lm - temperature_c)


# ---------- Interpolation verticale ----------

def fl_to_pressure_hpa(flight_level: int) -> float:
    """Atmosphère standard ISA : niveau de vol (altitude-pression) -> pression."""
    h_ft = flight_level * 100.0
    if h_ft <= 36089.0:
        return 1013.25 * (1.0 - 6.8755856e-6 * h_ft) ** 5.2558797
    return 226.3206 * math.exp(-(h_ft - 36089.0) / 20805.8)


def interpolate(profile: WeatherProfile, pressure_hpa: float) -> tuple[float, float] | None:
    """(T, RH) interpolés linéairement en ln(p). None si hors du profil (pas d'extrapolation)."""
    levels = sorted(profile.levels, key=lambda lv: lv.pressure_hpa, reverse=True)  # du bas vers le haut
    for lo, hi in zip(levels, levels[1:]):
        if hi.pressure_hpa <= pressure_hpa <= lo.pressure_hpa:
            w = (math.log(lo.pressure_hpa) - math.log(pressure_hpa)) / \
                (math.log(lo.pressure_hpa) - math.log(hi.pressure_hpa))
            return (lo.temperature_c + w * (hi.temperature_c - lo.temperature_c),
                    lo.rh_pct + w * (hi.rh_pct - lo.rh_pct))
    return None


def level_risk(profile: WeatherProfile, flight_level: int) -> LevelRisk | None:
    """Risque de contrail au niveau demandé. None si le niveau sort du profil météo."""
    p = fl_to_pressure_hpa(flight_level)
    tr = interpolate(profile, p)
    if tr is None:
        return None
    t, rh = tr
    rhi = rh_ice(rh, t)
    sac = sac_satisfied(t, p, rh)
    return LevelRisk(flight_level=flight_level, temperature_c=round(t, 1), rh_ice_pct=round(rhi, 1),
                     sac_satisfied=sac, persistent=sac and rhi >= config.RHI_THRESHOLD)


# ---------- Jour / nuit ----------

def solar_elevation_deg(lat: float, lon: float, timestamp: int) -> float:
    """Élévation du soleil (approximation à ~1°, suffisante pour jour/nuit)."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    n = dt.timetuple().tm_yday
    decl = math.radians(23.44) * math.sin(math.radians(360.0 / 365.0 * (n - 81)))
    b = math.radians(360.0 / 365.0 * (n - 81))
    eot_min = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    solar_time_h = dt.hour + dt.minute / 60.0 + lon / 15.0 + eot_min / 60.0
    hour_angle = math.radians(15.0 * (solar_time_h - 12.0))
    phi = math.radians(lat)
    sin_el = math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(hour_angle)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_el))))


def is_night(lat: float, lon: float, timestamp: int) -> bool:
    """Soleil sous l'horizon : le contrail ne fait que piéger la chaleur."""
    return solar_elevation_deg(lat, lon, timestamp) < 0.0


# ---------- Évaluation complète ----------

def _option(profile: WeatherProfile, fl: int) -> LevelRisk | None:
    if not (config.OPTION_MIN_FL <= fl <= config.OPTION_MAX_FL):
        return None
    return level_risk(profile, fl)


TRACK_STEP_KM = 25.0
TRACK_MAX_KM = 800.0
KM_PER_DEG_LAT = 111.2


def _step(lat: float, lon: float, heading_deg: float, km: float) -> tuple[float, float]:
    """Point à `km` le long du cap (approximation locale plane, suffisante sur 25 km)."""
    h = math.radians(heading_deg)
    dlat = km * math.cos(h) / KM_PER_DEG_LAT
    dlon = km * math.sin(h) / (KM_PER_DEG_LAT * max(math.cos(math.radians(lat)), 0.1))
    return lat + dlat, lon + dlon


def issr_along_track(aircraft: Aircraft, profile_at, levels: dict[str, int]) -> dict[str, float]:
    """Suit le cap de l'avion dans la grille météo tant que son niveau actuel est sursaturé.

    profile_at(lat, lon) -> WeatherProfile | None (None = hors des données : on s'arrête).
    levels = {"current": FL, "climb": FL+20, "descend": FL-20}.
    Renvoie les km de contrail persistant au niveau actuel ("current"), et pour chaque option
    les km où le niveau actuel est sursaturé MAIS pas le niveau visé (contrail réellement évité).
    """
    km = {name: 0.0 for name in levels}
    lat, lon, d = aircraft.lat, aircraft.lon, 0.0
    while d < TRACK_MAX_KM:
        prof = profile_at(lat, lon)
        if prof is None:
            break
        cur = level_risk(prof, levels["current"])
        if cur is None or not cur.persistent:
            break
        km["current"] += TRACK_STEP_KM
        for name, fl in levels.items():
            if name == "current":
                continue
            opt = level_risk(prof, fl)
            if opt is not None and not opt.persistent:
                km[name] += TRACK_STEP_KM
        lat, lon = _step(lat, lon, aircraft.heading_deg, TRACK_STEP_KM)
        d += TRACK_STEP_KM
    return km


def assess(aircraft: Aircraft, profile: WeatherProfile, profile_at=None) -> RiskAssessment | None:
    """Risque au niveau actuel, à +20 FL et à -20 FL, et le bilan chiffré de chaque option.

    flagged = current.persistent. Jev ne calcule rien : il choisit à partir de ces chiffres.
    None si le niveau actuel sort du profil météo.

    profile_at(lat, lon) (optionnel) : accès à la grille météo. Si fourni, on mesure la
    longueur réelle de la zone sursaturée le long du cap (issr_along_track) ; sinon on prend
    la longueur typique config.ISSR_TYPICAL_KM.
    """
    current = level_risk(profile, aircraft.flight_level)
    if current is None:
        return None
    climb = _option(profile, aircraft.flight_level + config.LEVEL_STEP)
    descend = _option(profile, aircraft.flight_level - config.LEVEL_STEP)
    night = is_night(aircraft.lat, aircraft.lon, aircraft.timestamp)
    options = {"climb": climb, "descend": descend}

    minutes = 0.0
    fuel_pen, avoided, net = {}, {}, {}
    if current.persistent:
        kmh = max(aircraft.speed_kt, 1.0) * fuel.KT_TO_KMH
        if profile_at is not None:
            levels = {"current": aircraft.flight_level}
            levels.update({n: o.flight_level for n, o in options.items() if o is not None})
            km = issr_along_track(aircraft, profile_at, levels)
            issr_km = max(km["current"], TRACK_STEP_KM)
            avoided_km = {n: km.get(n, 0.0) for n in options}
        else:
            issr_km = config.ISSR_TYPICAL_KM
            avoided_km = {n: (0.0 if o is None or o.persistent else issr_km) for n, o in options.items()}
        minutes = issr_km / kmh * 60.0
        factor = config.CONTRAIL_CO2E_KG_PER_KM["night" if night else "day"]
        for name, opt in options.items():
            if opt is None:
                continue
            # On reste au niveau dévié tant que l'avion traverse la zone sursaturée.
            fuel_pen[name] = round(fuel.fuel_penalty_kg(None, minutes, name), 1)
            avoided[name] = round(avoided_km[name] * factor, 0)
            net[name] = round(fuel.net_benefit_co2e_kg(avoided[name], fuel_pen[name]), 0)

    return RiskAssessment(
        icao24=aircraft.icao24, current=current, climb=climb, descend=descend,
        is_night=night, flagged=current.persistent, minutes_in_issr=round(minutes, 1),
        fuel_penalty_kg=fuel_pen, warming_avoided_co2e_kg=avoided, net_benefit_co2e_kg=net,
    )
