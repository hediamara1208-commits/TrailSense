"""[HEDI] Orchestrator: one full cycle, from the sky to the Snapshot.

    aircraft (live or replay)
      -> weather (cache) + physics filter     [Dawud: physics/cycle.py -> assess_cycle()]
      -> Jev on the flagged flights           [Hedi: agent/jev.py]
      -> advisories (template -> Granite -> Cloud LLM) [Hedi: agent/writer.py]
      -> Snapshot + Receipt                   returned by the API

Physics in one line (Dawud, PR #1):
    aircraft, assessments, stats = assess_cycle(load_replay(i))   # or live_cycle_data()
    stats = {aircraft_scanned, flagged_by_physics, weather_calls, weather_cache_hits, physics_ms}
    -> copy these straight into the Receipt.

Optimisation: keep the last RiskAssessment per aircraft in memory and only recompute it
when the aircraft changes weather cell or flight level.
"""
from backend.models import Snapshot


def run_cycle(mode: str = "replay", threshold: float = 0.8, replay_index: int = 0) -> Snapshot:
    """Runs one cycle and fills the Receipt (counters, latency, energy)."""
    raise NotImplementedError
