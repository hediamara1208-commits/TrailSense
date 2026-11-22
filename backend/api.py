"""[HEDI] FastAPI web server. Start it with scripts/run_api.py (VS Code Run button),
or in a terminal: uvicorn backend.api:app --reload   then open http://localhost:8000

Endpoints:
- GET /api/snapshot?mode=replay|live&threshold=0.8&i=0  -> one Snapshot as JSON
- GET /api/benchmark                                    -> latest benchmark result (scripts/run_benchmark.py)

/api/snapshot runs the real pipeline (pipeline.run_cycle). Each answer carries a "source" field:
"replay <file>", "live", or "fixture" when there is no recording yet (fictional example,
so the map still works on a fresh clone).
"""
import json
import logging
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import config
from backend.agent import pipeline
from backend.sources.recorder import replay_files

logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "sample_snapshot.json"

app = FastAPI(title="TrailSense")
# Lets the Lovable preview (and a Vite dev server) read the API on this laptop. Read-only GET API, no secrets.
app.add_middleware(CORSMiddleware, allow_methods=["GET"], allow_headers=["*"],
                   allow_origin_regex=r"https://([a-z0-9-]+\.)*(lovable\.app|lovable\.dev|lovableproject\.com)|http://localhost:\d+")


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
    if mode == "replay" and not replay_files():
        return {**load_fixture(threshold), "source": "fixture (no recording in data/replay/)"}
    snap = jsonable_encoder(asdict(pipeline.run_cycle(mode, threshold, i)))
    if mode == "replay":
        files = replay_files()
        snap["source"] = f"replay {i % len(files) + 1}/{len(files)} ({files[i % len(files)].name})"
    else:
        snap["source"] = "live"
    return snap


@app.get("/api/benchmark")
def benchmark():
    """Latest benchmark result (cascade vs all-LLM), written by scripts/run_benchmark.py.
    Not run on request: the all-LLM side takes minutes, which is exactly the point."""
    from backend.benchmark.all_llm import OUT
    if not OUT.exists():
        return JSONResponse({"status": "not_run_yet", "how": "run scripts/run_benchmark.py"}, status_code=404)
    return json.loads(OUT.read_text(encoding="utf-8"))


# The web page. Mounted LAST so it doesn't hide the /api routes above.
