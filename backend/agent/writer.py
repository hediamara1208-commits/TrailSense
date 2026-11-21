"""[HEDI] Writing advisories for the dispatcher: a cascade, cheapest first.

    1. Template (free)                -> every flagged flight by default
    2. Local Granite (IBM, Ollama)    -> the next MAX_GRANITE_ADVISORIES advisories, on the laptop
    3. Claude (cloud, small model)    -> only the MAX_CLAUDE_ADVISORIES most important advisories
                                         (night, high warming probability, large net benefit)

Granite: `ollama pull <GRANITE_MODEL>` then POST {OLLAMA_URL}/api/chat (httpx is enough).
Local energy: estimate laptop power (W) × call duration (s) / 3600 -> Wh.
Claude: anthropic SDK; measure every call with EcoLogits (EcoLogits.init(providers=["anthropic"])).
If USE_GRANITE = False or Ollama does not answer: skip tier 2 without crashing.

Expected advisory example:
"ACA871 at FL360 is flying through an ice-supersaturated layer (RHi 118%). FL340 is dry.
Proposal: descend 2,000 ft for ~12 min. Cost: +38 kg of fuel.
Estimated net benefit: +780 kg CO2e avoided. Jev confidence: 0.91."
"""
import re
import time

import httpx

from backend import config
from backend.models import Action, Advisory, Decision, RiskAssessment

_OPTION = {Action.CLIMB: ("climb", "climb", 20), Action.DESCEND: ("descend", "descend", -20)}
_WHO = {"jev": "Jev", "rule": "fallback rule", "physics": "physics, no Jev call"}


def template_advisory(decision: Decision, assessment: RiskAssessment, callsign: str = "") -> Advisory:
    """Free advisory built from a text template (no model, no energy)."""
    a, cur = assessment, assessment.current
    callsign = callsign or a.icao24
    when = "night" if a.is_night else "day"
    head = (f"{callsign} at FL{cur.flight_level} ({when}) is flying through an ice-supersaturated layer "
            f"(RHi {cur.rh_ice_pct:.0f}%) for ~{a.minutes_in_issr:.0f} min.")
    if decision.action == Action.MAINTAIN:
        body = "No altitude change avoids it at a net climate benefit: keep the current level."
    else:
        key, verb, dfl = _OPTION[decision.action]
        target = a.climb if key == "climb" else a.descend
        body = (f"No persistent contrail at FL{target.flight_level} (RHi {target.rh_ice_pct:.0f}%). "
                f"Proposal: {verb} 2,000 ft. "
                f"Cost: +{a.fuel_penalty_kg.get(key, 0):.0f} kg of fuel. "
                f"Estimated net benefit: {a.net_benefit_co2e_kg.get(key, 0):+.0f} kg CO2e.")
    tail = f"Confidence {decision.confidence:.2f} ({_WHO.get(decision.decided_by, decision.decided_by)})."
    return Advisory(a.icao24, callsign, f"{head} {body} {tail}", "template")


GRANITE_SYSTEM = (
    "You write short operational advisories for an airline dispatcher. Rewrite the facts you are given as "
    "one clear message of at most 3 sentences: what is happening, the proposal, the cost and benefit, and "
    "whether the dispatcher must review it. Use ONLY the numbers given, exactly as written. Do not add "
    "numbers, levels, units or facts. Plain text, no greeting, no markdown."
)


def _numbers(text: str) -> set[str]:
    """Numbers in a text, normalised (thousands separators and a leading + removed)."""
    return {n.replace(",", "").lstrip("+").rstrip(".") for n in re.findall(r"[+-]?\d[\d,]*\.?\d*", text)}


def check_numbers(facts: str, text: str) -> None:
    """Hallucination guard: every number the model writes must come from the facts."""
    invented = _numbers(text) - _numbers(facts) - {"2000", "2"}   # "2,000 ft" may be written "2000 ft"
    if invented:
        raise ValueError(f"model invented numbers {sorted(invented)}")


def granite_advisory(decision: Decision, assessment: RiskAssessment, callsign: str = "") -> tuple[Advisory, dict]:
    """Advisory written locally by IBM Granite via Ollama. Returns (advisory, impacts) with
    impacts = {energy_wh, latency_ms}. Raises if Ollama is off or the model invents a number,
    so the caller falls back to the free template."""
    facts = template_advisory(decision, assessment, callsign).text
    review = "auto (sent automatically)" if decision.route.value == "auto" else "human review (the dispatcher must approve)"
    body = {
        "model": config.GRANITE_MODEL, "stream": False,
        "messages": [{"role": "system", "content": GRANITE_SYSTEM},
                     {"role": "user", "content": f"Facts: {facts}\nRouting: {review}."}],
        "options": {"temperature": 0.2, "num_predict": 160},
    }
    t0 = time.perf_counter()
    r = httpx.post(f"{config.OLLAMA_URL}/api/chat", json=body, timeout=config.GRANITE_TIMEOUT_S)
    r.raise_for_status()
    data = r.json()
    latency_ms = (time.perf_counter() - t0) * 1000
    text = " ".join(data["message"]["content"].split())
    if not text:
        raise ValueError("empty answer")
    check_numbers(facts, text)
    gen_s = data.get("total_duration", latency_ms * 1e6) / 1e9          # Ollama reports nanoseconds
    impacts = {"energy_wh": round(config.LAPTOP_POWER_W * gen_s / 3600, 4), "latency_ms": round(latency_ms, 1),
               "output_tokens": data.get("eval_count", 0)}
    return Advisory(assessment.icao24, callsign or assessment.icao24, text, "granite"), impacts


def claude_advisory(decision: Decision, assessment: RiskAssessment, callsign: str = "") -> tuple[Advisory, dict]:
    """Advisory written by Claude. Returns (advisory, impacts) with impacts = {energy_wh, gco2e, cost_usd}."""
    raise NotImplementedError


def route_writers(decisions: list[Decision], assessments: list[RiskAssessment]) -> dict[str, str]:
    """Decides who writes each advisory: {icao24: "claude" | "granite" | "template"}.

    Rank by importance (night, persistent_warming_prob, net_benefit), give the top
    MAX_CLAUDE_ADVISORIES to Claude, the next MAX_GRANITE_ADVISORIES to Granite, the rest to the template.
    MAINTAIN decisions always use the template (nothing to explain beyond the numbers).
    """
    by_id = {a.icao24: a for a in assessments}

    def importance(d: Decision) -> tuple:
        a = by_id[d.icao24]
        return (a.is_night, d.persistent_warming_prob, max(a.net_benefit_co2e_kg.values(), default=0))

    routes = {d.icao24: "template" for d in decisions}
    ranked = sorted((d for d in decisions if d.action != Action.MAINTAIN), key=importance, reverse=True)
    n_claude, n_granite = config.MAX_CLAUDE_ADVISORIES, config.MAX_GRANITE_ADVISORIES if config.USE_GRANITE else 0
    for rank, d in enumerate(ranked):
        if rank < n_claude:
            routes[d.icao24] = "claude"
        elif rank < n_claude + n_granite:
            routes[d.icao24] = "granite"
    return routes
