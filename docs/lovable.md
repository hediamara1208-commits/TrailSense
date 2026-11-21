# Building the frontend with Lovable

Lovable code (CodeJam, opening slides): **COMM-MCGILL-BSA6** (Pro plan, 100 credits, one month).

## How it plugs in
1. Lovable builds the UI from the prompt below, with the example JSON as fake data.
2. Connect the Lovable project to GitHub (Lovable creates its own repo).
3. We pull that repo, switch `fetchSnapshot()` to `/api/snapshot`, run `npm run build`,
   and FastAPI serves the build (same origin: no CORS problem). The old `frontend/` stays as plan B.

Optional: to test the Lovable preview directly against your laptop, `api.py` allows CORS from
Lovable domains; set `VITE_API_BASE=http://localhost:8000` (Chrome may ask to allow local network access).

## Status (Sat 02:45)
- Lovable project: "Pixel Perfect Screenshot Muse", synced to GitHub `hediamara1208-commits/pixel-perfect-screenshot-muse-09` (branch `main`, two-way sync).
- It is a TanStack Start app (server-rendered). Recorded cycles are bundled from `src/data/snapshots/*.json`;
  a previous/next picker steps through them (real cycles with flagged flights first, then the fictional example, then dry cycles).
- `VITE_API_BASE=http://localhost:8000` makes it read the live API instead (CORS is allowed in `api.py`).

## Refreshing the demo cycles (T1)
1. Laptop, VS Code: run `scripts/export_snapshots.py` (real Jev calls) -> `data/exports/snapshots/`.
2. Copy the `*.json` cycle files (not `index.json`) into the Lovable repo's `src/data/snapshots/`, commit, push to `main`.
3. Lovable picks it up; click Publish to update the public link.

## Prompt 1 (paste as is)

Build a single-page dashboard called **TrailSense** for an airline dispatcher named Sophie. Dark theme, calm and professional (an aviation operations look).

Data: one JSON "snapshot" (example below) with `aircraft`, `assessments`, `decisions`, `advisories` and `receipt`, joined by `icao24`. Put ALL data loading in one function `fetchSnapshot(threshold)` in `src/lib/api.ts`. For now it returns the example below (with each decision's `route` recomputed: "auto" if `confidence >= threshold`, else "human_review"). Later it will call `GET /api/snapshot?mode=replay&threshold=<value>` prefixed by `import.meta.env.VITE_API_BASE ?? ""` (empty = same origin).

Layout:
1. **Header:** title, the `mode` and `source` text, and an "Autonomy threshold" slider (0 to 1, step 0.05, default 0.8) that reloads the data. Legend: grey = no persistent contrail, orange = flagged, green = sent automatically, purple = Sophie reviews.
2. **Map (Leaflet + react-leaflet, OpenStreetMap tiles `https://tile.openstreetmap.org/{z}/{x}/{y}.png`):** centred on 50°N, 64°W, zoom 5. One plane marker per aircraft, rotated by `heading_deg`. Colour: grey if the assessment is missing or not `flagged`; orange if flagged without a decision; green if the decision `route` is "auto"; purple if "human_review".
3. **Side panel:** when a flight is clicked, show callsign, flight level, speed. A small table "now / climb / descend" with flight level, `rh_ice_pct` and whether `persistent` (a lasting contrail). Then extra fuel (`fuel_penalty_kg`) and net benefit (`net_benefit_co2e_kg`, kg CO₂e) for each option. Jev's decision (`action`) with a confidence bar, who decided (`decided_by`: "jev" = Jev, "rule" = fallback rule, "physics" = no beneficial option, no Jev call), and the advisory `text` in a card with "written by" (`written_by`).
4. **Bottom strip, "Compute receipt":** planes scanned, flagged by physics, physics ms, Jev calls, Jev tokens, Granite calls, Claude calls, total Wh (`llm_energy_wh + local_llm_energy_wh`), cost $, total latency ms. Make the frugality numbers stand out.
5. **"Review queue"** list of decisions whose `route` is "human_review", each with Approve / Reject buttons (local state only).

No login, no database, no backend, no Supabase.

## Example snapshot (paste right after the prompt)

```json
{
  "mode": "replay",
  "timestamp": 1795237200,
  "threshold": 0.8,
  "aircraft": [
    {
      "icao24": "c0ffee",
      "callsign": "TEST101",
      "lat": 49.6,
      "lon": -65.8,
      "altitude_ft": 36000,
      "flight_level": 360,
      "heading_deg": 250,
      "speed_kt": 470,
      "timestamp": 1795237200
    },
    {
      "icao24": "c0ffef",
      "callsign": "TEST202",
      "lat": 50.8,
      "lon": -61.9,
      "altitude_ft": 35000,
      "flight_level": 350,
      "heading_deg": 60,
      "speed_kt": 455,
      "timestamp": 1795237200
    },
    {
      "icao24": "c0fff0",
      "callsign": "TEST303",
      "lat": 48.7,
      "lon": -62.4,
      "altitude_ft": 38000,
      "flight_level": 380,
      "heading_deg": 280,
      "speed_kt": 480,
      "timestamp": 1795237200
    }
  ],
  "assessments": [
    {
      "icao24": "c0ffee",
      "current": {
        "flight_level": 360,
        "temperature_c": -52.0,
        "rh_ice_pct": 118.0,
        "sac_satisfied": true,
        "persistent": true
      },
      "climb": {
        "flight_level": 380,
        "temperature_c": -55.0,
        "rh_ice_pct": 104.0,
        "sac_satisfied": true,
        "persistent": true
      },
      "descend": {
        "flight_level": 340,
        "temperature_c": -48.0,
        "rh_ice_pct": 71.0,
        "sac_satisfied": true,
        "persistent": false
      },
      "is_night": true,
      "flagged": true,
      "minutes_in_issr": 14.0,
      "fuel_penalty_kg": {
        "climb": 25.0,
        "descend": 38.0
      },
      "warming_avoided_co2e_kg": {
        "climb": 0.0,
        "descend": 900.0
      },
      "net_benefit_co2e_kg": {
        "climb": -79.0,
        "descend": 779.9
      }
    },
    {
      "icao24": "c0ffef",
      "current": {
        "flight_level": 350,
        "temperature_c": -50.0,
        "rh_ice_pct": 106.0,
        "sac_satisfied": true,
        "persistent": true
      },
      "climb": {
        "flight_level": 370,
        "temperature_c": -53.0,
        "rh_ice_pct": 92.0,
        "sac_satisfied": true,
        "persistent": false
      },
      "descend": {
        "flight_level": 330,
        "temperature_c": -46.0,
        "rh_ice_pct": 110.0,
        "sac_satisfied": true,
        "persistent": true
      },
      "is_night": true,
      "flagged": true,
      "minutes_in_issr": 9.0,
      "fuel_penalty_kg": {
        "climb": 22.0,
        "descend": 35.0
      },
      "warming_avoided_co2e_kg": {
        "climb": 520.0,
        "descend": 0.0
      },
      "net_benefit_co2e_kg": {
        "climb": 450.5,
        "descend": -110.6
      }
    },
    {
      "icao24": "c0fff0",
      "current": {
        "flight_level": 380,
        "temperature_c": -56.0,
        "rh_ice_pct": 64.0,
        "sac_satisfied": true,
        "persistent": false
      },
      "climb": null,
      "descend": null,
      "is_night": true,
      "flagged": false,
      "minutes_in_issr": 0.0,
      "fuel_penalty_kg": {},
      "warming_avoided_co2e_kg": {},
      "net_benefit_co2e_kg": {}
    }
  ],
  "decisions": [
    {
      "icao24": "c0ffee",
      "action": "descend_2000",
      "confidence": 0.91,
      "persistent_warming_prob": 0.87,
      "forecast_reliability": 0.7,
      "operational_feasibility": 0.8,
      "route": "auto",
      "decided_by": "jev"
    },
    {
      "icao24": "c0ffef",
      "action": "climb_2000",
      "confidence": 0.62,
      "persistent_warming_prob": 0.66,
      "forecast_reliability": 0.5,
      "operational_feasibility": 0.7,
      "route": "human_review",
      "decided_by": "jev"
    }
  ],
  "advisories": [
    {
      "icao24": "c0ffee",
      "callsign": "TEST101",
      "text": "TEST101 at FL360 is flying through an ice-supersaturated layer (RHi 118%). FL340 is dry. Proposal: descend 2,000 ft. Cost: +38 kg of fuel. Confidence: 0.91.",
      "written_by": "claude"
    },
    {
      "icao24": "c0ffef",
      "callsign": "TEST202",
      "text": "TEST202 FL350 -> FL370 proposed (RHi 106% -> 92%). +22 kg. Confidence 0.62: needs review.",
      "written_by": "granite"
    }
  ],
  "receipt": {
    "aircraft_scanned": 3,
    "weather_calls": 2,
    "weather_cache_hits": 1,
    "flagged_by_physics": 2,
    "physics_ms": 0.4,
    "jev_calls": 1,
    "jev_input_tokens": 600,
    "local_llm_calls": 1,
    "local_llm_energy_wh": 0.05,
    "llm_calls": 1,
    "llm_energy_wh": 0.5,
    "llm_gco2e": 0.2,
    "cost_usd": 0.003,
    "latency_ms": 900
  },
  "source": "fixture (fictional example)"
}
```

## Follow-up prompts (one at a time, only if needed)
- "Add a Replay / Live toggle in the header that passes `mode=replay|live` to fetchSnapshot."
- "Add a 'Benchmark' button that calls `GET /api/benchmark` and shows the result in a modal (cascade vs all-LLM: calls, tokens, Wh, $, latency)."
- "Add Previous / Next buttons that pass `i=<index>` to fetchSnapshot to step through recorded cycles."
