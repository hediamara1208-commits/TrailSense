"""[HEDI] Advisory writers: template, Granite (Ollama mocked), hallucination guard, writer routing."""
import httpx
import pytest

from backend.agent import writer
from backend.models import Action, Decision, Route
from tests.test_jev import humid_assessment


def decision(action=Action.CLIMB, route=Route.HUMAN) -> Decision:
    return Decision("aaa111", action, 0.62, 0.9, 0.5, 0.9, route, "jev")


def test_template_has_the_key_facts():
    text = writer.template_advisory(decision(), humid_assessment(), "WET350").text
    for fact in ["WET350", "FL350", "FL370", "climb 2,000 ft", "+23 kg", "+826 kg CO2e", "0.62"]:
        assert fact in text


def test_guard_rejects_invented_numbers():
    facts = "AAL278 at FL330 ... +4 kg of fuel ... +3737 kg CO2e."
    writer.check_numbers(facts, "AAL278 should climb from FL330: 4 kg of fuel for 3,737 kg CO2e avoided.")
    with pytest.raises(ValueError):
        writer.check_numbers(facts, "AAL278 should climb: 4 kg of fuel for 5,000 kg CO2e avoided.")


def fake_ollama(monkeypatch, content: str):
    def post(url, json, timeout):
        assert url.endswith("/api/chat") and json["model"] and not json["stream"]
        return httpx.Response(200, json={"message": {"content": content}, "total_duration": 2_000_000_000,
                                         "eval_count": 60}, request=httpx.Request("POST", url))
    monkeypatch.setattr(writer.httpx, "post", post)


def test_granite_advisory(monkeypatch):
    fake_ollama(monkeypatch, "WET350 at FL350 is in a humid layer. Climb 2,000 ft to FL370: +23 kg of fuel, "
                             "+826 kg CO2e net benefit. Confidence 0.62, please review.")
    adv, impacts = writer.granite_advisory(decision(), humid_assessment(), "WET350")
    assert adv.written_by == "granite" and adv.callsign == "WET350"
    assert impacts["energy_wh"] == pytest.approx(25 * 2 / 3600, abs=1e-4)


def test_granite_inventing_a_number_is_rejected(monkeypatch):
    fake_ollama(monkeypatch, "WET350: climb to FL390, +23 kg of fuel.")
    with pytest.raises(ValueError):
        writer.granite_advisory(decision(), humid_assessment(), "WET350")


def test_route_writers_skips_maintain():
    keep = Decision("bbb222", Action.MAINTAIN, 1.0, 0.9, 1.0, 1.0, Route.AUTO, "physics")
    other = humid_assessment()
    other.icao24 = "bbb222"
    routes = writer.route_writers([decision(), keep], [humid_assessment(), other])
    assert routes["bbb222"] == "template" and routes["aaa111"] == "claude"
