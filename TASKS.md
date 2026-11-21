# Task split: Dawud and Hedi

**Principle:** each of us owns our modules, but **each of us must be able to explain the other's** to the jury (the Q&A judges the whole team). At every sync point, we walk each other through what we did in 5 minutes.

*Version 4 (Sat 01:35): repo translated to English, PR #1 merged, progress updated. Version 3 (Fri 23:05): local Granite tier and hackathon tools (Cloud LLM Builder Club, 1Password). Version 2 (Fri 22:45): roles swapped, benchmark moved to the LLM side, no-Jev fallback, recording rate limits, shared pitch, repo public by 11:00.*

## Dawud: "the science and the data" (critical path)
**Goal:** real aircraft, real weather, a correct and defensible contrail risk. This is the riskiest part: Dawud focuses on it and nothing else.

- [x] **D1 · Fri night (urgent)** `sources/opensky.py`: cruising aircraft over the area (OAuth2, 429 handling).
- [x] **D2 · Fri night (urgent)** `sources/recorder.py`: overnight recording. **Aircraft every 2-5 min (`RECORD_S`) with a free OpenSky account; weather on a fixed grid over the BBOX**, to stay within the OpenSky and Open-Meteo limits.
- [x] **D3 · Fri night / Sat morning** `sources/weather.py`: Open-Meteo profiles + cache. Humidity convention checked (`RH_CONVENTION = "ice"`, threshold `RHI_THRESHOLD = 95`).
- [x] **D4 · Sat morning** `physics/contrails.py`: RHi, Schmidt-Appleman, interpolation, day/night, `assess()` + `tests/test_physics.py` (14 tests).
- [x] **D5 · Sat afternoon** `physics/fuel.py` + `physics/cycle.py` (`assess_cycle()`) + ISSR length along the track + `docs/hypotheses.md` (Borella et al. 2024: 50 kg CO2e/km at night, 15 by day).
- [ ] **D6 · Sat evening** Pitch, science part: the physics slide and the jury's physics questions.

**Fallback rule at noon Saturday:** if the physics isn't ready on real data, keep **Schmidt-Appleman + RHi only, without fuel**, and add the fuel at 18:00. *(No longer needed: physics delivered.)*

## Hedi: "the agent, the LLMs and the product"
**Goal:** an agent that decides fast and well with Jev, only calls an LLM when it's worth it, proves its frugality, and a clear interface.

- [ ] **H0 · Fri night** Ask the McGill Cloud LLM Builder Club for Cloud LLM API credits *(DM sent to Ed, Fri 23:13, waiting)*. Create a shared 1Password vault with Dawud for the keys (Jev, provider, OpenSky).
- [x] **H1 · Fri night** Jev key created; the 4 questions validated in the playground (TEST101: descend_2000, confidence 0.97, 16 ms; TEST202: maintain, confidence 0.14 → human review). Rule added: no option with a positive net benefit → MAINTAIN without calling Jev.
- [x] **H2 · Fri night** `api.py` serves the fixture + `frontend/`: Leaflet map, planes colored by status, flight panel, threshold slider, receipt.
- [x] **H3 · Sat morning** `agent/jev.py`: `build_state()` + `decide()` with the threshold. Test the grouped call. *(Done Sat 01:50: raw API via httpx, one call per flight. First real call on a synthetic humid night flight: climb_2000, confidence 0.96 → auto, 804 input tokens, 217 ms round trip. Grouped call still to test.)*
- [x] **H4 · Sat morning** `agent/fallback.py`: **plan B without Jev** (hard-coded rule, same output as `decide()`).
- [ ] **H5 · Sat noon** `agent/writer.py`: template + Cloud LLM for the 1-2 key flights + EcoLogits. *(Template and `route_writers` done Sat 01:45; Cloud LLM and Granite tiers still to do: the pipeline falls back to the template.)*
- [ ] **H5b · Sat afternoon (optional)** **Local Granite** tier: install Ollama, `ollama pull` the Granite model, `granite_advisory()`, local Wh measurement. **Cut-off: if it doesn't work by 15:00 Saturday, `USE_GRANITE = False` and we stop.**
- [x] **H6 · Sat afternoon** `agent/pipeline.py`: plug in `assess_cycle()`, fill the `Receipt` (including `physics_ms`). *(Done Sat 01:45: cycle cache, the slider re-routes without recomputing; API serves real replays, falls back to the fixture if `data/replay/` is empty; `decided_by` added to `Decision`.)*
- [ ] **H7 · Sat afternoon** `benchmark/all_llm.py`: cascade vs all-LLM, **limited to ~20 flights** from the recording.
- [ ] **H8 · Sat evening** Final interface: Replay/Live toggle, benchmark button, best demo cycles.
- [ ] **H9 · Sun morning** Backup video + submission README (GIF, instructions, sources).

## Pitch: shared
- **Hedi:** the story (hook, Sophie, System 1 / System 2), the demo, the receipt and the benchmark.
- **Dawud:** the physics in 30 seconds, and the jury's science questions.
- Both rehearse together Saturday 23:00 and Sunday 09:00.

## Sync points (15 min each)
| When | What must work |
|---|---|
| **Fri 23:30** | `models.py` validated by both. Dawud: real aircraft in the console + recording running. Hedi: the map shows the fixture. |
| **Sat 12:00** | Dawud: `assess()` on real data (otherwise: fallback rule above). Hedi: Jev **and** the plan B decide on the fixture. |
| **Sat 18:00** | **End-to-end integration** in Replay mode. Fuel added if the noon fallback was used. |
| **Sat 23:00** | Benchmark + receipt in the interface. First pitch rehearsal. |
| **Sun 09:00** | **Feature freeze.** Only fixes and rehearsal. |
| **Sun 10-11** | Mandatory team check-in (CodeJam). |
| **Sun 11:00** | Repo up to date (public), README with GIF, last commit. Margin if GitHub or the submission causes trouble. |
| **Sun 12:00** | End of all changes (CodeJam rule). |

## Working rules
- One branch per person (`dawud/...`, `hedi/...`), merged into `main` at the sync points.
- Small, frequent commits (they prove we coded during the hackathon).
- Never put an API key in the code: everything in `.env` or in 1Password (`op run --env-file=.env -- uvicorn backend.api:app`). **The repo is public**: check before every push.
