"""Starts the TrailSense server. In VS Code: open this file, click Run (top-right).

Then open http://localhost:8000 in your browser.
Stop it with the trash-can icon of the terminal (or Ctrl+C in the terminal).
reload=True: the server restarts by itself every time you save a Python file.
"""
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so that "backend" can be imported

if __name__ == "__main__":
    print("TrailSense -> http://localhost:8000")
    uvicorn.run("backend.api:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(ROOT))
