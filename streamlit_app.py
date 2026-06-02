"""Deployment entry point for the LG refrigerator advisor Streamlit app."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


sys.dont_write_bytecode = True

APP_DIR = Path(__file__).resolve().parent / "artifacts" / "lg-advisor"
APP_FILE = APP_DIR / "app.py"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

runpy.run_path(str(APP_FILE), run_name="__main__")
