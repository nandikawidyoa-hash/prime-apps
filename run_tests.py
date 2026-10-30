#!/usr/bin/env python3
"""
Test runner for PRIME APPS
Usage: python3 run_tests.py
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / "bootstrap.py") as f:
    exec(f.read(), globals())

import tests.test_suite as ts

if __name__ == "__main__":
    ts.run_all_tests()
