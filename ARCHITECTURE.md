# TrailSense architecture

## In one sentence
A frugal AI agent that helps airline dispatchers avoid climate-warming contrails: in a few milliseconds it finds the few flights concerned and proposes ±2,000 ft, using far less compute than a conventional agent (ratio measured by our benchmark).

## The flow (one cycle)
```
 OpenSky (aircraft)          Open-Meteo GFS (T, humidity 300→150 hPa)
        │                              │  fixed grid over the BBOX, cached, batched calls
        └──────────────┬───────────────┘
                       ▼
        physics/cycle.assess_cycle()     ← FREE, deterministic (~3.7 ms for 40 aircraft)
        Schmidt-Appleman + RHi ≥ threshold at FL, FL+20, FL-20,
        ISSR length along the track, fuel and net CO2e for each option
                       │  only the "flagged" flights
                       ▼
        no option with a positive net benefit? → MAINTAIN in code, no call
                       │  otherwise
                       ▼
        agent/jev.decide()               ← SYSTEM 1: fast, calibrated
        (plan B: agent/fallback.py if Jev is unavailable)
        action + confidence → AUTO (≥ threshold) or HUMAN (< threshold)
                       │  only the 2-3 most important
                       ▼
        agent/writer.py                  ← SYSTEM 2, as a cascade:
          template (free) → local Granite, IBM via Ollama (routine advisories)
          → Claude (1-2 key advisories only)
                       │
                       ▼
        Snapshot + Receipt  →  api.py  →  frontend (Leaflet map)
```

## Who owns what
| Folder / file | Owner | Role |
|---|---|---|
| `backend/models.py` | **both** | Data contracts. Any change is decided by both. |
| `backend/config.py` | both | Settings (area, levels, threshold, cache) |
| `backend/sources/opensky.py` | Dawud | Live aircraft |
| `backend/sources/weather.py` | Dawud | Weather profiles + cache |
| `backend/sources/recorder.py` | Dawud | Record / replay the sky (aircraft every 5 min, weather grid) |
| `backend/physics/contrails.py` | Dawud | SAC, RHi, risk per level, day/night |
| `backend/physics/fuel.py` | Dawud | Fuel penalty, warming avoided (Borella et al. 2024), net CO2e |
| `backend/physics/cycle.py` | Dawud | `assess_cycle()`: the whole physics step in one call |
| `backend/agent/jev.py` | Hedi | Jev decision, autonomy threshold |
| `backend/agent/fallback.py` | Hedi | Plan B without Jev (hard-coded rule) |
| `backend/agent/writer.py` | Hedi | Advisories: template → local Granite → Claude, EcoLogits measurement |
| `backend/agent/pipeline.py` | Hedi | Orchestration of one cycle, Receipt |
| `backend/benchmark/all_llm.py` | Hedi | Comparison with an all-LLM agent (~20 flights) |
| `backend/api.py` | Hedi | FastAPI |
| `frontend/` | Hedi | Map, flight details, threshold slider, receipt |
| `data/fixtures/sample_snapshot.json` | both | Fictional example so both sides can work in parallel |

## Contact points between Hedi and Dawud
1. `assess_cycle(data) -> (aircraft, assessments, stats)`: Dawud produces it, Hedi calls it in `pipeline.py`. `data` comes from `load_replay(i)` (Replay) or `live_cycle_data()` (Live).
2. `stats` (aircraft_scanned, flagged_by_physics, weather_calls, weather_cache_hits, physics_ms) goes straight into the `Receipt`.
3. The `Snapshot` JSON: produced by the backend, read by the frontend. `sample_snapshot.json` is the example.

While a module isn't ready, the other side uses the example file. Nobody waits for anybody.

## Running the project
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                      # or on Windows: run scripts/setup_env.py
cp .env.example .env                                  # fill in the keys (or: op run --env-file=.env -- ...)
ollama pull granite4:micro                            # local tier (check the exact name with ollama list)
uvicorn backend.api:app --reload                      # or run scripts/run_api.py, then open http://localhost:8000
```

## Hackathon tools used (status Sat 04:25)
- **Jev** (TypeSafe AI, recommended by the organizers): System 1 decision, real API calls (`agent/jev.py`). Grouped call measured and kept off (inflates confidence).
- **IBM Granite** (`granite4:micro`, local via Ollama): advisories with a numbers guard (`agent/writer.py`) and the all-LLM side of the benchmark.
- **Lovable**: the published frontend (separate repo, see `docs/lovable.md`).
- **Claude** (Anthropic): coding assistant; the top writing tier is wired in the cascade but needs API credits (asked to the McGill Claude Builder Club).
- **1Password** (`op run`): planned (T4) for sharing keys; until then keys stay in `.env`, never committed.

## Assumptions
All physics assumptions (humidity convention, persistence threshold, propulsive efficiency, fuel penalty, warming factor per km, day/night) are documented and sourced in [`docs/hypotheses.md`](docs/hypotheses.md).
