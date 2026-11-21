"""[HEDI] Jev client tests without the network: state format, answer parsing, HTTP call (mocked)."""
import json

import httpx
import pytest

from backend import config
from backend.agent import jev
from backend.models import Action, LevelRisk, RiskAssessment, Route


def humid_assessment() -> RiskAssessment:
    return RiskAssessment(
        icao24="aaa111",
        current=LevelRisk(350, -60.3, 125.0, True, True),
        climb=LevelRisk(370, -62.0, 80.0, True, False),
        descend=LevelRisk(330, -56.0, 120.0, True, True),
        is_night=True, flagged=True, minutes_in_issr=12.0,
        fuel_penalty_kg={"climb": 23.3, "descend": 31.0},
        warming_avoided_co2e_kg={"climb": 900.0, "descend": 0.0},
        net_benefit_co2e_kg={"climb": 826.0, "descend": -98.0},
    )


ANSWERS = {  # format of the raw API (docs.typesafe.ai quickstart)
    "action": {"type": "choice", "choice": "climb_2000", "confidence": 0.93,
               "probabilities": {"climb_2000": 0.93, "descend_2000": 0.02, "maintain": 0.05}},
    "persistent_warming": {"type": "noul", "noul": 0.97},
    "forecast_reliability": {"type": "score", "score": 2.0, "confidence": 0.8},
    "operational_feasibility": {"type": "score", "score": 1.0, "confidence": 0.6},
}


def test_state_is_compact_json_with_all_options():
    state = json.loads(jev.build_state(humid_assessment(), "WET350"))
    assert state["flight"] == "WET350"
    assert set(state["options"]) == {"maintain_FL350", "climb_to_FL370", "descend_to_FL330"}
    assert state["options"]["climb_to_FL370"]["net_climate_benefit_co2e_kg"] == 826.0
    assert "Do not recalculate" in state["note"]


def test_parse_answers():
    d = jev.parse_answers(humid_assessment(), ANSWERS, threshold=0.9)
    assert d.action == Action.CLIMB and d.decided_by == "jev"
    assert d.confidence == 0.93 and d.route == Route.AUTO
    assert d.forecast_reliability == 1.0 and d.operational_feasibility == 0.5
    assert jev.parse_answers(humid_assessment(), ANSWERS, threshold=0.95).route == Route.HUMAN


def test_decide_calls_api_once_per_flight(monkeypatch):
    sent = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        sent.append(body)
        assert request.headers["Authorization"] == "Bearer test-key"
        assert body["model"] == config.JEV_MODEL and set(body["questions"]) == set(jev.QUESTIONS)
        return httpx.Response(200, json={"model": "jev-test", "answers": ANSWERS,
                                         "usage": {"input_tokens": 600, "output_tokens": 70}})

    real_client = httpx.Client
    monkeypatch.setattr(jev.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    decisions, usage = jev.decide([humid_assessment(), humid_assessment()], 0.8, {"aaa111": "WET350"})
    assert len(sent) == 2 and usage["jev_calls"] == 2 and usage["jev_input_tokens"] == 1200
    assert all(d.action == Action.CLIMB for d in decisions)


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        jev.decide([humid_assessment()], 0.8)
