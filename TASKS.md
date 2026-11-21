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
- [x] **D10 · Sat evening** Fact-check every number in the README and pitch against its source (35 % share, −54 %, −11.6 %, Borella, Teoh). *(PR #3: docs/fact_check.md, all ✅)*

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
- [x] **H7 · Sat afternoon** `benchmark/all_llm.py`: cascade vs all-LLM, **limited to ~20 flights** from the recording. *(done Sat 03:34 on AAL278's cycle, 20 flights, Granite local: all-LLM 20 calls / 7.2 min / 2.60 Wh vs TrailSense 2 calls (1 Jev + 1 Granite) / 8.8 s / 0.039 Wh = 10x fewer calls, 49x faster, 67x less local energy; the all-LLM agent flagged 20/20 flights as persistent (19 false alarms) vs 1 for the physics)*
- [ ] **H8 · Sat afternoon/evening** Final interface **built with Lovable** (decided Sat 01:57): prompt + example in `docs/lovable.md`, then pull the Lovable repo, point `fetchSnapshot()` at `/api/snapshot`, serve the build from FastAPI. Replay/Live toggle, benchmark button, best demo cycles. Plan B: the current `frontend/`.
- [ ] **H9 · Sun morning** Backup video + submission README (GIF, instructions, sources).

## Hackathon tools: getting the most out of them (plan agreed Sat 02:30)
Order: tonight (1), Saturday morning (3) → (2) → H7, Saturday alongside (4) and the extras.

- [x] **T1 · Sat night, Lovable public demo** *(done 02:52: published at https://pixel-perfect-screenshot-muse-09.lovable.app/ with AAL278 + UAL46 and real Jev decisions; QR in docs/demo-qr.png)*: `scripts/export_snapshots.py` writes 5-10 real recorded cycles as JSON into the Lovable app, which reads them when no API is reachable. Publish (lovable.app URL) → QR code on the last slide, for judges and Popular Vote.
- [ ] **T2 · Sat morning, Jev grouped call + uncertainty** *(02:55: grouped call built and measured: -67% calls, -15% tokens, -57% time, but it inflates confidence (UAL46 0.67 → 0.91, review → auto), so OFF by default; probabilities stored in `Decision.probabilities`, bars in the UI next)*: all flagged flights of a cycle in ONE request (fewer calls/tokens on the receipt); show Jev's per-option probabilities as bars in the flight panel. Hedi: ask the TypeSafe team at the venue for 5 min of feedback ("reviewed with TypeSafe's engineers").
- [x] **T3 · Sat morning, IBM Granite local tier (= H5b):** Hedi installs Ollama; Cloud LLM wires `granite_advisory()` + local Wh. Also unlocks H7 if Cloud LLM credits never arrive. Cut-off 15:00. *(done Sat 03:25: granite4:micro via Ollama, ~10 s and 0.05 Wh per advisory, numbers guard OK)*
- [ ] **T4 · Sat, 1Password:** shared vault with Dawud (Jev, OpenSky, Cloud LLM keys), `op run --env-file=.env -- python scripts/run_api.py`, README section. Hedi installs the 1Password CLI and signs in.
- [ ] **T5 · Sat, Cloud LLM:** if Ed hasn't replied by 10:00, go to the Cloud LLM Builder Club in person. Cloud LLM writes the 1-2 key advisories + the all-LLM side of H7 (EcoLogits). README line: "built with help from Cloud LLM".
- [ ] **X1 · Lovable booth:** show them the app.
- [ ] **X2 · Discord #meme-submissions:** one contrail meme.
- [ ] **X3 · Énergie 3R:** 2-minute chat to test the Sustainability angle.
- [ ] **X4 · TypeSafe:** feedback on our Jev usage (see T2).

## Saturday plan (written Sat 11:00 after a full check)
**State at 11:00:** pipeline, Jev, fallback, Granite, benchmark (60 flights), published demo, README all done. Dawud's PR #3 (W5 threshold sweep, W8 cross-section, D10 fact-check, Europe cycles 14 + 22 flagged) merges cleanly, 30 tests pass. Not done: GitHub repo rename, Lovable republish (live site still says ContrailWatch), Cloud LLM credits (Ed hasn't replied), pitch deck. New on Discord: no demo video required (10:20); 9th "bonus" track revealed only at closing (all tracks but Brim eligible); projector question unanswered; someone asked about IBM Bob credits.

| When | Hedi | Dawud | Cloud LLM |
|---|---|---|---|
| 11:00-12:00 | Rename the GitHub repo (click); Lovable: rename project + address, Publish; W1 pitch storyline | Pick the best Europe cycle(s) for the demo; check the day cycle's day/night factor | Merge PR #3; export the Europe cycles with real Jev + Granite into the demo |
| **12:00 sync** | Merge hedi/agent → main together; walk through the demo cycles (D9) | same | Update README numbers |
| 12:00-13:00 | Lunch; booth visits: TypeSafe (Jev feedback), IBM (Bob credits?), Lovable | Lunch; ask organizers: projector or laptop? | Benchmark on the Europe cycles (many flagged = stronger "right action" test) |
| 13:00-17:00 | W2 demo click path, W4 agent Q&A; T4 1Password if time | Physics slide from the cross-section, threshold-sensitivity answer, day vs night | Pitch deck (W11) from W1 + Dawud's material |
| 18:00 sync | Deck review together, cut to 2.5 min | same | Fixes from the review |
| 23:00 | **Rehearsal 1**, timed, with the live demo | same | Q&A drill |
| Sun 9:00 | Rehearsal 2, feature freeze | same | Final README, QR on the new address |
| Sun 10-11 | Team check-in | same | Final push at 11:00 |

**Judging format (organizer Arthur / CloggedArtery, Discord #hacker-questions, Sat 11:01-11:02):** about **7-8 minutes in total with the judges** (pitch + demo + Q&A), and **no projectors**: demo on our own laptop, as we like. So: a short pitch (~2.5 min), the live demo on the laptop screen, the rest for Q&A; no long video.

**Cloud LLM credits:** Ed hasn't replied; same request sent Sat 11:59 by DM to CloggedArtery and in #hacker-questions; **answer at 12:00: no credits available.** Cloud LLM tier turned off (`MAX_CLOUD_LLM_ADVISORIES = 0`); Granite writes everything. Not a problem: "apart from Jev, everything runs on the laptop" is a better frugality story. Not blocking: Granite covers writing and the benchmark. Only ask in person if you pass by the Cloud LLM Builder Club.

## While the recorders run (Sat 04:00 → 12:00)
Nothing here needs new recordings. New cycles are a bonus, picked up at noon.

**Hedi**
- [ ] **W1 · Pitch storyline (30 min):** write the 2-4 min story in bullet points: hook (contrails ≈ 57% of aviation's forcing), Sophie's problem, think fast / think slow, live demo, benchmark, ask. Cloud LLM builds the deck from it.
- [ ] **W2 · Demo click path (15 min):** the exact sequence to show live: cycle 1 AAL278 (Jev hesitates 74/25 → Sophie reviews) → slider → cycle 3 UPS214 (0.98 → auto) → search "AAL278" (flagged at 04:37, clear 25 min later) → benchmark section. Time it: max 60 s.
- [ ] **W3 · Phone test of the live site (10 min):** open the QR code on your phone, note anything broken or unclear.
- [ ] **W4 · Agent Q&A answers (20 min):** why Jev and not an LLM; what the 0.53-0.61 confidences mean; why the grouped call is off (inflated confidence); the 19 false alarms of the all-LLM agent; what happens if Jev is down (fallback rule).
- [ ] **T4 · 1Password** (when awake): install the CLI and sign in.

**Dawud**
- [x] **W5 · Threshold sensitivity (30 min):** run the scan with RHI_THRESHOLD 90 / 95 / 100 on the whole recording: how many flights flagged each time? Ready answer for "how sensitive is your result to the threshold?". *(PR #3: 3 → 6 flights from 95% to 90%, always < 1% of aircraft)*
- [x] **W6 · A day-time flagged cycle:** look for one in the recording, to show day vs night (day contrails partly cool; our factor 15 vs 50 kg CO2e/km). *(PR #3: Europe day cycle, 22 flagged)*
- [x] **W7 · Other regions:** `scan north_atlantic` / `scan europe`; if a cycle has several flagged flights, push it (more impressive than 1 per cycle). *(PR #3: Europe night cycle, 14 flagged)*
- [x] **W8 · Physics slide (D6):** the cross-section visual (aircraft in the humid layer, arrows to FL±20), as an image or a sketch Cloud LLM can redraw. *(PR #3: docs/figures/cross_section.svg)*
- [ ] **D10 · Fact-check the rest:** −54 %, −11.6 %, Borella factor, Teoh numbers.

**Cloud LLM**
- [x] **W9 · Benchmark on the 3 flagged cycles** (not just AAL278): a larger sample for the slide (runs on Hedi's laptop, ~7 min per cycle). *(done 04:36: 60 flights, 10x fewer calls, 27x faster, 30x less local energy; all-LLM: 57/57 false alarms, wrong action on UPS214)*
- [x] **W10 · README for the judges:** what it does, live link + QR, architecture diagram, results table, how to run, tools used, sources. *(done 04:25)*
- [ ] **W11 · Pitch deck** from W1, once Hedi has written the storyline.

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
