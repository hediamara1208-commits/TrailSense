"""[HEDI] Benchmark: our cascade against an "all-LLM" agent on the SAME flights.

This is the measured proof for the Agent Solution prize.

Protocol:
1. Take a recorded cycle with at least one flagged flight (data/replay/...), limited to
   BENCHMARK_MAX_FLIGHTS flights: every flagged flight + the first others, so the all-LLM mode stays cheap.
2. Mode A, all-LLM: send EACH aircraft + its raw weather profile to an LLM (the same local IBM Granite
   by default, so the energy comparison is like-for-like) and ask it for the whole job: is there a
   persistent contrail, what should the dispatcher do, and the advisory. Measure calls, tokens, time, Wh.
3. Mode B, ContrailWatch: the normal pipeline on the same flights (physics -> Jev only for flagged
   flights with a beneficial option -> Granite only for the advisories).
4. Quality: does the all-LLM agent find the contrails the physics finds, and does it pick the same action?
Output: data/benchmark/latest.json, read by GET /api/benchmark and shown in the interface.

Energy: Granite Wh = laptop power x generation time (estimate, config.LAPTOP_POWER_W). Jev runs on
TypeSafe's servers and is not metered here: we report its calls and tokens, not Wh.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from backend import config
from backend.agent import pipeline
from backend.physics.cycle import _profile_lookup, assess_cycle
from backend.sources.recorder import load_replay, replay_files

OUT = Path(__file__).resolve().parents[2] / "data" / "benchmark" / "latest.json"

ALL_LLM_SYSTEM = (
    "You are an AI agent that helps airline dispatchers avoid warming contrails. For the aircraft below, "
    "use its flight level and the weather profile (temperature and relative humidity at pressure levels; "
    f"relative humidity is given {'with respect to ice' if config.RH_CONVENTION == 'ice' else 'over water'}) "
    "to decide whether the aircraft leaves a PERSISTENT contrail at its current level, then recommend "
    "climb_2000, descend_2000 or maintain, and write a short advisory (max 3 sentences) for the dispatcher. "
    'Reply with JSON only: {"persistent_contrail": true|false, "action": "climb_2000"|"descend_2000"|"maintain", '
    '"advisory": "..."}'
)


def pick_flights(max_flights: int) -> tuple[int, dict, list[str]]:
    """First recorded cycle with a flagged flight; keep its flagged flights + the first others."""
    for i in range(len(replay_files())):
        data = load_replay(i)
        aircraft, assessments, _ = assess_cycle(data)
        flagged = [a.icao24 for a in assessments if a.flagged]
        if flagged:
            assessed = {a.icao24 for a in assessments}           # aircraft with weather nearby
            others = [ac.icao24 for ac in aircraft if ac.icao24 in assessed and ac.icao24 not in flagged]
            keep = (flagged + others)[:max_flights]
            data = {**data, "aircraft": [a for a in data["aircraft"] if a["icao24"] in keep]}
            return i, data, flagged
    raise RuntimeError("No recorded cycle with a flagged flight in data/replay/")


def granite_json(system: str, user: str) -> tuple[dict, dict]:
    """One local Granite call returning JSON. Returns (answer, usage)."""
    body = {"model": config.GRANITE_MODEL, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": 0.2, "num_predict": 220}}
    t0 = time.perf_counter()
    r = httpx.post(f"{config.OLLAMA_URL}/api/chat", json=body, timeout=config.GRANITE_TIMEOUT_S * 2)
    r.raise_for_status()
    data = r.json()
    wall_ms = (time.perf_counter() - t0) * 1000
    gen_s = data.get("total_duration", wall_ms * 1e6) / 1e9
    usage = {"input_tokens": data.get("prompt_eval_count", 0), "output_tokens": data.get("eval_count", 0),
             "ms": wall_ms, "wh": config.LAPTOP_POWER_W * gen_s / 3600}
    try:
        answer = json.loads(data["message"]["content"])
    except (json.JSONDecodeError, KeyError):
        answer = {}
    return answer, usage


def run_all_llm(data: dict) -> dict:
    """Mode A: one LLM call per aircraft, the LLM does everything."""
    profile_at = _profile_lookup(data.get("weather", []))
    totals = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "ms": 0.0, "wh": 0.0}
    answers = {}
    for ac in data["aircraft"]:
        prof = profile_at(ac["lat"], ac["lon"])
        if prof is None:
            continue
        levels = [{"pressure_hpa": lv.pressure_hpa, "altitude_ft": round(lv.altitude_ft),
                   "temperature_c": round(lv.temperature_c, 1), "rh_pct": round(lv.rh_pct, 1)} for lv in prof.levels]
        user = json.dumps({"aircraft": {k: ac[k] for k in ("callsign", "flight_level", "heading_deg", "speed_kt", "lat", "lon")},
                           "time_utc": time.strftime("%H:%M", time.gmtime(ac["timestamp"])),
                           "weather_profile": levels})
        answer, usage = granite_json(ALL_LLM_SYSTEM, user)
        answers[ac["icao24"]] = answer
        totals["calls"] += 1
        for k in ("input_tokens", "output_tokens", "ms", "wh"):
            totals[k] += usage[k]
    totals["ms"] = round(totals["ms"], 1)
    totals["wh"] = round(totals["wh"], 4)
    return {"totals": totals, "answers": answers}


def run_benchmark(max_flights: int | None = None) -> dict:
    max_flights = max_flights or config.BENCHMARK_MAX_FLIGHTS
    index, data, flagged = pick_flights(max_flights)

    # Mode B first (the real agent), then Mode A
    t0 = time.perf_counter()
    snap = pipeline.compute_from_data(data, "replay", config.DEFAULT_THRESHOLD)
    cascade_ms = (time.perf_counter() - t0) * 1000
    r = snap.receipt
    all_llm = run_all_llm(data)
    a = all_llm["totals"]

    # Quality: physics is the reference for "persistent contrail"; actions compared on flagged flights
    decisions = {d.icao24: d.action.value for d in snap.decisions}
    callsigns = {ac.icao24: ac.callsign for ac in snap.aircraft}
    found = sum(1 for i in flagged if all_llm["answers"].get(i, {}).get("persistent_contrail") is True)
    false_alarms = sum(1 for i, ans in all_llm["answers"].items()
                       if i not in flagged and ans.get("persistent_contrail") is True)
    same_action = sum(1 for i in flagged if all_llm["answers"].get(i, {}).get("action") == decisions.get(i))
    unparsed = sum(1 for ans in all_llm["answers"].values() if "action" not in ans)

    cascade_calls = r.jev_calls + r.local_llm_calls + r.llm_calls
    cascade = {"model_calls": cascade_calls, "jev_calls": r.jev_calls, "jev_input_tokens": r.jev_input_tokens,
               "granite_calls": r.local_llm_calls, "claude_calls": r.llm_calls, "physics_ms": r.physics_ms,
               "ms": round(cascade_ms, 1), "local_wh": round(r.local_llm_energy_wh, 4)}
    result = {
        "cycle": replay_files()[index].name, "flights": len(data["aircraft"]), "flagged_by_physics": len(flagged),
        "llm": config.GRANITE_MODEL,
        "all_llm": {"model_calls": a["calls"], "input_tokens": a["input_tokens"], "output_tokens": a["output_tokens"],
                    "ms": a["ms"], "local_wh": a["wh"]},
        "contrailwatch": cascade,
        "ratios": {
            "model_calls": round(a["calls"] / max(cascade_calls, 1), 1),
            "time": round(a["ms"] / max(cascade_ms, 1), 1),
            "local_energy": round(a["wh"] / r.local_llm_energy_wh, 1) if r.local_llm_energy_wh else None,
        },
        "quality": {
            "contrails_found_by_all_llm": f"{found}/{len(flagged)}",
            "all_llm_false_alarms": false_alarms,
            "same_action_on_flagged": f"{same_action}/{len(flagged)}",
            "all_llm_unparsed_answers": unparsed,
            "flagged": [{"callsign": callsigns.get(i, i), "contrailwatch": decisions.get(i),
                         "all_llm": all_llm["answers"].get(i, {}).get("action"),
                         "all_llm_says_persistent": all_llm["answers"].get(i, {}).get("persistent_contrail")}
                        for i in flagged],
        },
        "notes": [
            "Same flights and same raw data (aircraft + weather profile) for both agents.",
            "Physics is the reference for persistent contrails (Schmidt-Appleman + ice supersaturation).",
            f"Local Wh = {config.LAPTOP_POWER_W} W x generation time (estimate). Jev runs remotely: calls and tokens only.",
        ],
        "measured_at": int(time.time()),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result
