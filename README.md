# ContrailWatch

**McGill CodeJam 16 (Nov 20-22, 2026) · target track: Agent Solution**

A frugal AI agent that helps airline dispatchers avoid climate-warming contrails. In a few milliseconds it finds the few flights concerned and proposes to climb or descend 2,000 ft, using far less compute than a conventional agent (ratio measured by our benchmark).

## Why
- Contrails account for about 35% of aviation's warming impact (IPCC 2022), and a small minority of flights causes most of it.
- Avoiding them works on the flights that follow the plan (−54% in Google / American Airlines trials), but adoption is still low in real operations (−11.6% intent-to-treat, 2026 trial).
- Analysing every flight with a large LLM would be slow, expensive and polluting.

## How: think fast, then slow
1. **Physics (free):** Schmidt-Appleman criterion + ice supersaturation, at the current level and ±2,000 ft, with the length of the supersaturated region along the track (~3.7 ms for 40 aircraft).
2. **Jev (System 1):** a typed, calibrated decision for the flagged flights, with an autonomy threshold. If no option helps, the code decides "maintain" without calling Jev.
3. **Writing cascade (System 2):** free template, then IBM Granite locally, then Claude only for the 1-2 key advisories.
4. **Compute receipt** and **benchmark** against an all-LLM agent.

See [`ARCHITECTURE.md`](ARCHITECTURE.md), [`TASKS.md`](TASKS.md) and [`docs/hypotheses.md`](docs/hypotheses.md).

## Getting started
```bash
pip install -r requirements.txt     # Windows: run scripts/setup_env.py
cp .env.example .env
uvicorn backend.api:app --reload    # or run scripts/run_api.py, then open http://localhost:8000
```

## Team
Hedi Amara · Dawud
