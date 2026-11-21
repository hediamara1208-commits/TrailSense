# Task split: Dawud and Hedi

**Principle:** each of us owns our modules, but **each of us must be able to explain the other's** to the jury (the Q&A judges the whole team). At every sync point, we walk each other through what we did in 5 minutes.

*Version 5 (Sat 01:50): Dawud tasks D7-D10 added. Version 4 (Sat 01:35): repo translated to English, PR #1 merged, progress updated. Version 3 (Fri 23:05): local Granite tier and hackathon tools (Cloud LLM Builder Club, 1Password). Version 2 (Fri 22:45): roles swapped, benchmark moved to the LLM side, no-Jev fallback, recording rate limits, shared pitch, repo public by 11:00.*

## Dawud: "the science and the data" (critical path)
**Goal:** real aircraft, real weather, a correct and defensible contrail risk. This is the riskiest part: Dawud focuses on it and nothing else.

- [x] **D1 · Fri night (urgent)** `sources/opensky.py`: cruising aircraft over the area (OAuth2, 429 handling).
- [x] **D2 · Fri night (urgent)** `sources/recorder.py`: overnight recording. **Aircraft every 2-5 min (`RECORD_S`) with a free OpenSky account; weather on a fixed grid over the BBOX**, to stay within the OpenSky and Open-Meteo limits.
- [x] **D3 · Fri night / Sat morning** `sources/weather.py`: Open-Meteo profiles + cache. Humidity convention checked (`RH_CONVENTION = "ice"`, threshold `RHI_THRESHOLD = 95`).
- [x] **D4 · Sat morning** `physics/contrails.py`: RHi, Schmidt-Appleman, interpolation, day/night, `assess()` + `tests/test_physics.py` (14 tests).
- [x] **D5 · Sat afternoon** `physics/fuel.py` + `physics/cycle.py` (`assess_cycle()`) + ISSR length along the track + `docs/hypotheses.md` (Borella et al. 2024: 50 kg CO2e/km at night, 15 by day).
- [ ] **D6 · Sat evening** Pitch, science part: the physics slide and the jury's physics questions. *Draft in `docs/pitch_physics.md` (30 s script + 5 Q&A + backups); to rehearse.*
- [x] **D7 · Sat 01:40** Multi-region recording (PR #2): `--region north_atlantic|europe|us_northeast|east_canada`, one terminal per region, `--once` snapshots, `scan [region]`. Weather budgets keep all regions under the Open-Meteo free tier.
- [ ] **D8 · Sat night / morning** Pick the demo cycles: `python -m backend.physics.scan [region]`, commit the 5-10 best night cycles (most flagged flights) to `data/replay/`. Re-scan in the morning and swap if better ones appear.
- [ ] **D9 · Sat afternoon** Integration with Hedi: help plug `assess_cycle()` into `pipeline.py` (H6), then sanity-check the agent's climb/descend decisions on 2-3 flagged flights.
- [ ] **D10 · Sat evening** Fact-check every number in the README and pitch against its source (35 % share, −54 %, −11.6 %, Borella, Teoh).

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
- [ ] **H8 · Sat afternoon/evening** Final interface **built with Lovable** (decided Sat 01:57): prompt + example in `docs/lovable.md`, then pull the Lovable repo, point `fetchSnapshot()` at `/api/snapshot`, serve the build from FastAPI. Replay/Live toggle, benchmark button, best demo cycles. Plan B: the current `frontend/`.
- [ ] **H9 · Sun morning** Backup video + submission README (GIF, instructions, sources).

## Hackathon tools: getting the most out of them (plan agreed Sat 02:30)
Order: tonight (1), Saturday morning (3) → (2) → H7, Saturday alongside (4) and the extras.

- [x] **T1 · Sat night, Lovable public demo** *(done 02:52: published at https://pixel-perfect-screenshot-muse-09.lovable.app/ with AAL278 + UAL46 and real Jev decisions; QR in docs/demo-qr.png)*: `scripts/export_snapshots.py` writes 5-10 real recorded cycles as JSON into the Lovable app, which reads them when no API is reachable. Publish (lovable.app URL) → QR code on the last slide, for judges and Popular Vote.
- [ ] **T2 · Sat morning, Jev grouped call + uncertainty** *(02:55: grouped call built and measured: -67% calls, -15% tokens, -57% time, but it inflates confidence (UAL46 0.67 → 0.91, review → auto), so OFF by default; probabilities stored in `Decision.probabilities`, bars in the UI next)*: all flagged flights of a cycle in ONE request (fewer calls/tokens on the receipt); show Jev's per-option probabilities as bars in the flight panel. Hedi: ask the TypeSafe team at the venue for 5 min of feedback ("reviewed with TypeSafe's engineers").
- [ ] **T3 · Sat morning, IBM Granite local tier (= H5b):** Hedi installs Ollama; Cloud LLM wires `granite_advisory()` + local Wh. Also unlocks H7 if Cloud LLM credits never arrive. Cut-off 15:00.
- [ ] **T4 · Sat, 1Password:** shared vault with Dawud (Jev, OpenSky, Cloud LLM keys), `op run --env-file=.env -- python scripts/run_api.py`, README section. Hedi installs the 1Password CLI and signs in.
- [ ] **T5 · Sat, Cloud LLM:** if Ed hasn't replied by 10:00, go to the Cloud LLM Builder Club in person. Cloud LLM writes the 1-2 key advisories + the all-LLM side of H7 (EcoLogits). README line: "built with help from Cloud LLM".
- [ ] **X1 · Lovable booth:** show them the app.
- [ ] **X2 · Discord #meme-submissions:** one contrail meme.
- [ ] **X3 · Énergie 3R:** 2-minute chat to test the Sustainability angle.
- [ ] **X4 · TypeSafe:** feedback on our Jev usage (see T2).

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
