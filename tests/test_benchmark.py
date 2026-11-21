"""[HEDI] Benchmark plumbing with the models mocked (no network, no Ollama)."""
import json
from dataclasses import asdict

import pytest

from backend import config
from backend.agent import pipeline
from backend.benchmark import all_llm
from backend.models import Aircraft
from backend.sources import recorder
from tests.test_pipeline import NIGHT_TS, humid_profile


@pytest.fixture
def one_cycle(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, "REPLAY_DIR", tmp_path)
    monkeypatch.setattr(all_llm, "OUT", tmp_path / "latest.json")
    monkeypatch.setattr(config, "RH_CONVENTION", "ice")
    monkeypatch.setattr(config, "USE_GRANITE", False)
    monkeypatch.setattr(pipeline.jev, "decide", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no Jev")))
    weather = [asdict(humid_profile(la, lo)) for la in range(46, 54) for lo in range(-70, -58)]
    planes = [Aircraft("aaa111", "WET350", 49.0, -64.0, 35000, 350, 75.0, 470.0, NIGHT_TS),
              Aircraft("bbb222", "DRY410", 50.0, -62.0, 41000, 410, 255.0, 470.0, NIGHT_TS)]
    (tmp_path / f"{NIGHT_TS}.json").write_text(json.dumps(
        {"timestamp": NIGHT_TS, "aircraft": [asdict(a) for a in planes], "weather": weather}))
    calls = []

    def fake_llm(system, user):
        calls.append(json.loads(user)["aircraft"]["callsign"])
        persistent = "WET" in calls[-1]
        return ({"persistent_contrail": persistent, "action": "climb_2000" if persistent else "maintain",
                 "advisory": "..."}, {"input_tokens": 500, "output_tokens": 60, "ms": 3000.0, "wh": 0.02})
    monkeypatch.setattr(all_llm, "granite_json", fake_llm)
    return calls


def test_benchmark_compares_both_agents(one_cycle):
    r = all_llm.run_benchmark(20)
    assert one_cycle == ["WET350", "DRY410"]                  # the all-LLM agent sees every aircraft
    assert r["all_llm"]["model_calls"] == 2 and r["contrailwatch"]["model_calls"] == 0
    assert r["quality"]["contrails_found_by_all_llm"] == "1/1"
    assert r["quality"]["same_action_on_flagged"] == "1/1"
    assert all_llm.OUT.exists()
