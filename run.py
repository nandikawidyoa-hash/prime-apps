#!/usr/bin/env python3
"""
PRIME APPS — Webstore Application Launcher
Starts the production-grade FastAPI server via Uvicorn.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
bootstrap_path = BASE_DIR / "bootstrap.py"
if bootstrap_path.exists():
    with open(bootstrap_path) as bf:
        exec(bf.read(), globals())

import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🚀 PRIME APPS running on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
