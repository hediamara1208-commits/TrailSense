"""One-time project setup: virtual environment + libraries + .env file.

Run from the project folder (VS Code: open this file, click the Run button top-right).
Safe to run again: it skips what already exists.
"""
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

print(f"1/4  Python used: {sys.version.split()[0]} ({sys.executable})")
if sys.version_info < (3, 10):
    sys.exit("     Python 3.10 or newer is required (the Jev SDK needs it). Install it and run again.")

if VENV.exists():
    print("2/4  .venv already exists, skipping")
else:
    print("2/4  Creating .venv ...")
    venv.create(VENV, with_pip=True)

print("3/4  Installing libraries from requirements.txt (1-2 min) ...")
subprocess.check_call([str(PY), "-m", "pip", "install", "--upgrade", "pip", "-q"])
subprocess.check_call([str(PY), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt"), "-q"])

env = ROOT / ".env"
if env.exists():
    print("4/4  .env already exists, not touched")
else:
    shutil.copy(ROOT / ".env.example", env)
    print("4/4  Created .env from .env.example: paste your keys into it")

print("\nDONE. Installed in .venv:")
subprocess.call([str(PY), "-m", "pip", "list", "--format=freeze"])
