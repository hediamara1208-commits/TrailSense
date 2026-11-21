"""[DAWUD] Tests de la physique : ce qu'on doit pouvoir défendre devant le jury.

Lancer : python -m pytest -q
"""
import pytest

from backend import config
from backend.models import Aircraft, LevelWeather, WeatherProfile
from backend.physics import contrails as c
from backend.physics import fuel

NIGHT_TS = 1795234233  # vendredi ~23 h 15 à Montréal
DAY_TS = NIGHT_TS + 13 * 3600  # samedi ~12 h 15


def profile(rh_by_p: dict[int, float]) -> WeatherProfile:
    """Profil réaliste (températures du premier enregistrement, Gaspésie) avec RH choisies."""
    temps = {350: -39.0, 300: -49.5, 275: -53.5, 250: -58.5, 225: -62.5, 200: -61.0, 175: -57.5, 150: -55.5}
    return WeatherProfile(lat=49.0, lon=-64.0, valid_time=NIGHT_TS, levels=[
        LevelWeather(pressure_hpa=p, altitude_ft=0, temperature_c=t, rh_pct=rh_by_p.get(p, 30.0))
        for p, t in temps.items()])


def plane(fl: int, ts: int = NIGHT_TS) -> Aircraft:
    return Aircraft("abc123", "TEST1", 49.0, -64.0, fl * 100, fl, 75.0, 500.0, ts)


@pytest.fixture(autouse=True)
def ice_convention(monkeypatch):
    monkeypatch.setattr(config, "RH_CONVENTION", "ice")


def test_ice_saturates_before_water():
    assert c.e_sat_ice_hpa(-50) < c.e_sat_water_hpa(-50)


def test_water_convention_converts(monkeypatch):
    monkeypatch.setattr(config, "RH_CONVENTION", "water")
    assert c.rh_ice(60, -50) > 90  # 60 % /eau à -50 °C ≈ 98 % /glace


def test_isa_flight_levels():
    assert c.fl_to_pressure_hpa(350) == pytest.approx(238.4, abs=0.5)
    assert c.fl_to_pressure_hpa(390) == pytest.approx(196.8, abs=0.5)


def test_sac_threshold_order_of_magnitude():
    # Schumann (1996) : T_LM ≈ -40 °C vers 250 hPa pour eta ~0,35
    assert -45 < c.sac_threshold_c(250) < -38


def test_sac_cold_humid_forms():
    assert c.sac_satisfied(-60, 250, 90)


def test_sac_warm_never_forms():
    assert not c.sac_satisfied(-30, 250, 100)


def test_day_night():
    assert c.is_night(45.5, -73.6, NIGHT_TS)
    assert not c.is_night(45.5, -73.6, DAY_TS)


def test_assess_flags_persistent_and_finds_dry_option():
    # Couche saturée autour de 275-250 hPa (FL320-340), sèche au-dessus
    prof = profile({275: 100, 250: 100, 225: 40})
    a = c.assess(plane(330), prof)
    assert a.flagged and a.current.persistent
    assert a.climb is not None and not a.climb.persistent
    assert a.net_benefit_co2e_kg["climb"] > 0
    assert a.fuel_penalty_kg["climb"] > 0


def test_assess_dry_not_flagged():
    a = c.assess(plane(330), profile({}))
    assert not a.flagged and a.net_benefit_co2e_kg == {}


def test_option_also_persistent_avoids_nothing():
    prof = profile({300: 100, 275: 100, 250: 100, 225: 100, 200: 100})
    a = c.assess(plane(350), prof)
    assert a.warming_avoided_co2e_kg["climb"] == 0
    assert a.net_benefit_co2e_kg["climb"] < 0  # on brûlerait du carburant pour rien


def test_night_weighs_more_than_day():
    assert fuel.warming_avoided_co2e_kg(18, 500, True) > fuel.warming_avoided_co2e_kg(18, 500, False)


def test_out_of_profile_returns_none():
    assert c.level_risk(profile({}), 500) is None


def test_along_track_measures_issr_length():
    wet = profile({275: 100, 250: 100, 225: 40})
    dry = profile({})
    # zone sursaturée sur les 100 premiers km vers l'est, puis sec
    def profile_at(lat, lon):
        return wet if lon < -64.0 + 100 / (111.2 * 0.656) else dry
    a = c.assess(Aircraft("x", "X", 49.0, -64.0, 33000, 330, 90.0, 500.0, NIGHT_TS), wet, profile_at=profile_at)
    assert a.flagged
    assert 75 <= a.minutes_in_issr / 60 * 500 * 1.852 <= 130  # ~100 km, à un pas de 25 km près
    assert a.warming_avoided_co2e_kg["climb"] > 0


def test_assess_cycle_on_replay_dict():
    from dataclasses import asdict
    from backend.physics.cycle import assess_cycle
    prof = profile({275: 100, 250: 100, 225: 40})
    data = {"timestamp": NIGHT_TS, "aircraft": [asdict(plane(330)), asdict(plane(500))],
            "weather": [asdict(prof)]}
    aircraft, assessments, stats = assess_cycle(data)
    assert len(aircraft) == 2 and len(assessments) == 1  # FL500 hors profil -> écarté
    assert stats["flagged_by_physics"] == 1
