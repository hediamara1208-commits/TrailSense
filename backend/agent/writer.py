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
from backend.models import Advisory, Decision, RiskAssessment


def template_advisory(decision: Decision, assessment: RiskAssessment) -> Advisory:
    """Free advisory built from a text template."""
    raise NotImplementedError


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
    """
    raise NotImplementedError
