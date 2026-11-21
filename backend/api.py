"""[HEDI] FastAPI web server. Start it with scripts/run_api.py (VS Code Run button),
or in a terminal: uvicorn backend.api:app --reload   then open http://localhost:8000

Endpoints:
- GET /api/snapshot?mode=replay|live&threshold=0.8&i=0  -> one Snapshot as JSON
- GET /api/benchmark                                    -> benchmark result (not built yet)
- GET /                                                 -> the web page (frontend/)

STEP 5 (now): /api/snapshot returns the FICTIONAL fixture, so the map can be built
before the real pipeline exists. Later: replace load_fixture() by pipeline.run_cycle().
"""
import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import config

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "sample_snapshot.json"

app = FastAPI(title="ContrailWatch")


def load_fixture(threshold: float) -> dict:
    """Reads the fictional example and applies the autonomy threshold.

    Even with fake data, the threshold slider must work: a decision goes out
    automatically ("auto") if Jev's confidence >= threshold, otherwise Sophie reviews it.
    """
    snap = json.loads(FIXTURE.read_text(encoding="utf-8"))
    snap.pop("_note", None)
    snap["threshold"] = threshold
    for d in snap["decisions"]:
        d["route"] = "auto" if d["confidence"] >= threshold else "human_review"
    return snap


@app.get("/api/snapshot")
def snapshot(
    mode: str = Query("replay", pattern="^(replay|live)$"),
    threshold: float = Query(config.DEFAULT_THRESHOLD, ge=0.0, le=1.0),
    i: int = Query(0, ge=0),
):
    # TODO (later step): return asdict(pipeline.run_cycle(mode, threshold, i))
    return load_fixture(threshold)


@app.get("/api/benchmark")
def benchmark():
    # TODO (later step): return the result of benchmark/all_llm.run_benchmark()
    return JSONResponse({"status": "not_built_yet"}, status_code=501)


# The web page. Mounted LAST so it doesn't hide the /api routes above.
app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
