"""[HEDI] Pipeline tests on a synthetic recording (no network): physics -> decisions -> advisories."""
import json
from dataclasses import asdict

import pytest

from backend import config
from backend.agent import pipeline
from backend.models import Action, Aircraft, LevelWeather, Route, WeatherProfile
from backend.sources import recorder

NIGHT_TS = 1795234233  # Friday ~11:15 pm in Montreal
TEMPS = {350: -39.0, 300: -49.5, 275: -53.5, 250: -58.5, 225: -62.5, 200: -61.0, 175: -57.5, 150: -55.5}


def humid_profile(lat, lon, wet_hpa=(250, 225)):
    """Ice-supersaturated layer around FL340-360, dry above and below."""
    return WeatherProfile(lat, lon, NIGHT_TS, [
        LevelWeather(p, 0, t, 125.0 if p in wet_hpa else 30.0) for p, t in TEMPS.items()])


@pytest.fixture
def replay(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, "REPLAY_DIR", tmp_path)
    monkeypatch.setattr(config, "RH_CONVENTION", "ice")
    monkeypatch.setattr(config, "USE_JEV", True)
    monkeypatch.setattr(config, "USE_GRANITE", False)  # never call the local model in tests

    def jev_down(*args, **kwargs):  # never spend real Jev credits in tests
        raise RuntimeError("Jev unavailable in tests")
    monkeypatch.setattr(pipeline.jev, "decide", jev_down)  # -> must fall back cleanly
    pipeline._cache.clear()
    weather = [asdict(humid_profile(lat, lon)) for lat in range(46, 54) for lon in range(-70, -58)]
    planes = [
        Aircraft("aaa111", "WET350", 49.0, -64.0, 35000, 350, 75.0, 470.0, NIGHT_TS),  # in the wet layer
        Aircraft("bbb222", "DRY410", 50.0, -62.0, 41000, 410, 255.0, 470.0, NIGHT_TS),  # above it
    ]
    (tmp_path / f"{NIGHT_TS}.json").write_text(json.dumps(
        {"timestamp": NIGHT_TS, "aircraft": [asdict(a) for a in planes], "weather": weather}))
    return tmp_path


def test_cycle_end_to_end(replay):
    snap = pipeline.run_cycle("replay", 0.8, 0)
    assert snap.receipt.aircraft_scanned == 2
    assert snap.receipt.jev_calls == 0          # Jev down: fallback rule, free
    flagged = {a.icao24 for a in snap.assessments if a.flagged}
    assert {d.icao24 for d in snap.decisions} == flagged
    assert len(snap.advisories) == len(snap.decisions)
    for d in snap.decisions:
        assert d.decided_by in {"rule", "physics"}
        assert (d.route == Route.AUTO) == (d.confidence >= 0.8)


def test_threshold_reroutes_without_recomputing(replay):
    first = pipeline.run_cycle("replay", 0.99, 0)
    again = pipeline.run_cycle("replay", 0.1, 0)
    assert again.receipt is first.receipt       # same cached cycle
    assert all(d.route == Route.AUTO for d in again.decisions)


def test_no_benefit_means_maintain_without_jev(replay):
    from backend.agent import fallback
    snap = pipeline.run_cycle("replay", 0.8, 0)
    for a in snap.assessments:
        if a.flagged and not any(v > 0 for v in a.net_benefit_co2e_kg.values()):
            d = next(d for d in snap.decisions if d.icao24 == a.icao24)
            assert d.action == Action.MAINTAIN and d.decided_by == "physics"
    assert fallback.best_option is not None
