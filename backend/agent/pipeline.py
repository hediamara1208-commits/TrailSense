"""[HEDI] Orchestrator: one full cycle, from the sky to the Snapshot.

    aircraft (live or replay)
      -> weather (cache) + physics filter     [Dawud: physics/cycle.py -> assess_cycle()]
      -> flagged, no option with a positive net benefit -> MAINTAIN in code (no Jev call)
      -> Jev on the other flagged flights      [Hedi: agent/jev.py]; plan B: agent/fallback.py
      -> advisories (template -> Granite -> Cloud LLM) [Hedi: agent/writer.py]
      -> Snapshot + Receipt                   returned by the API

Frugality:
- A cycle is computed ONCE and cached. Moving the threshold slider only re-routes the
  decisions (auto / human review): no new physics, no new Jev call.
- Live cycles are reused for LIVE_CACHE_S seconds (OpenSky credits, Jev calls).
"""
from __future__ import annotations

import logging
import time
from dataclasses import replace

from backend import config
from backend.agent import fallback, jev, writer
from backend.models import Advisory, Decision, Receipt, RiskAssessment, Snapshot
from backend.physics.cycle import assess_cycle, live_cycle_data
from backend.sources.recorder import load_replay, replay_files

log = logging.getLogger(__name__)

LIVE_CACHE_S = 60
_cache: dict[tuple[str, int], tuple[float, Snapshot]] = {}


# ---------- Decisions ----------

def _decide(assessments: list[RiskAssessment], threshold: float,
            callsigns: dict[str, str]) -> tuple[list[Decision], dict]:
    """Jev if enabled and working, otherwise the hard-coded rule (same output)."""
    if config.USE_JEV:
        try:
            return jev.decide(assessments, threshold, callsigns)
        except Exception as e:  # API down, quota, network...
            log.warning("Jev failed (%s): using the fallback rule", e)
    return fallback.decide_by_rule(assessments, threshold)


def decide_all(assessments: list[RiskAssessment], threshold: float,
               callsigns: dict[str, str] | None = None) -> tuple[list[Decision], dict]:
    """Decision for every flagged flight. Obvious MAINTAIN cases never reach Jev."""
    flagged = [a for a in assessments if a.flagged]
    obvious = [a for a in flagged if not jev.needs_jev(a)]
    to_decide = [a for a in flagged if jev.needs_jev(a)]
    decisions = [fallback.maintain_by_physics(a) for a in obvious]
    usage = {"jev_calls": 0, "jev_input_tokens": 0}
    if to_decide:
        more, usage = _decide(to_decide, threshold, callsigns or {})
        decisions += more
    return decisions, usage


# ---------- Advisories ----------

def write_advisories(decisions: list[Decision], assessments: list[RiskAssessment],
                     callsigns: dict[str, str], receipt: Receipt) -> list[Advisory]:
    """Writing cascade. Any tier that fails (not built, Ollama off, no credits) falls back to the template."""
    by_id = {a.icao24: a for a in assessments}
    routes = writer.route_writers(decisions, assessments)
    out = []
    for d in decisions:
        a, cs, who = by_id[d.icao24], callsigns.get(d.icao24, ""), routes.get(d.icao24, "template")
        tiers = {"cloud_llm": ["cloud_llm", "granite"], "granite": ["granite"]}.get(who, [])
        if not config.USE_GRANITE:
            tiers = [t for t in tiers if t != "granite"]
        adv = None
        for tier in tiers:   # cheapest acceptable fallback: Cloud LLM -> Granite -> template
            try:
                if tier == "cloud_llm":
                    adv, imp = writer.cloud_llm_advisory(d, a, cs)
                    receipt.llm_calls += 1
                    receipt.llm_energy_wh += imp.get("energy_wh", 0.0)
                    receipt.llm_gco2e += imp.get("gco2e", 0.0)
                    receipt.cost_usd += imp.get("cost_usd", 0.0)
                else:
                    adv, imp = writer.granite_advisory(d, a, cs)
                    receipt.local_llm_calls += 1
                    receipt.local_llm_energy_wh += imp.get("energy_wh", 0.0)
                break
            except NotImplementedError:
                continue
            except Exception as e:
                log.warning("%s advisory failed for %s (%s): next tier", tier, d.icao24, e)
        out.append(adv or writer.template_advisory(d, a, cs))
    return out


# ---------- One cycle ----------

def compute_cycle(mode: str, replay_index: int, threshold: float) -> Snapshot:
    """The real work: physics -> decisions -> advisories -> Receipt."""
    data = live_cycle_data() if mode == "live" else load_replay(replay_index)
    return compute_from_data(data, mode, threshold)


def compute_from_data(data: dict, mode: str, threshold: float) -> Snapshot:
    """Same as compute_cycle() for an already-loaded cycle (any region; used by scripts/export_snapshots.py)."""
    t0 = time.perf_counter()
    aircraft, assessments, stats = assess_cycle(data)
    receipt = Receipt(**stats)
    callsigns = {ac.icao24: ac.callsign for ac in aircraft}
    decisions, usage = decide_all(assessments, threshold, callsigns)
    receipt.jev_calls = usage.get("jev_calls", 0)
    receipt.jev_input_tokens = usage.get("jev_input_tokens", 0)
    advisories = write_advisories(decisions, assessments, callsigns, receipt)
    receipt.latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    return Snapshot(mode=mode, timestamp=data["timestamp"], threshold=threshold, aircraft=aircraft,
                    assessments=assessments, decisions=decisions, advisories=advisories, receipt=receipt)


def apply_threshold(snap: Snapshot, threshold: float) -> Snapshot:
    """Re-routes every decision for a new threshold, without recomputing anything."""
    decisions = [replace(d, route=fallback.route_for(d.confidence, threshold, d.forecast_reliability, d.action)) for d in snap.decisions]
    return replace(snap, threshold=threshold, decisions=decisions)


def run_cycle(mode: str = "replay", threshold: float = 0.8, replay_index: int = 0) -> Snapshot:
    """Runs one cycle (or reuses the cached one) and applies the autonomy threshold."""
    if mode == "replay":
        n = len(replay_files())
        key = ("replay", replay_index % n if n else 0)
    else:
        key = ("live", 0)
    hit = _cache.get(key)
    if hit and (mode == "replay" or time.time() - hit[0] < LIVE_CACHE_S):
        return apply_threshold(hit[1], threshold)
    snap = compute_cycle(mode, replay_index, threshold)
    _cache[key] = (time.time(), snap)
    return apply_threshold(snap, threshold)
