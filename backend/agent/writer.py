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


def granite_advisory(decision: Decision, assessment: RiskAssessment) -> tuple[Advisory, dict]:
    """Advisory written locally by Granite. Returns (advisory, impacts) with impacts = {energy_wh, latency_ms}."""
    raise NotImplementedError


def claude_advisory(decision: Decision, assessment: RiskAssessment) -> tuple[Advisory, dict]:
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
