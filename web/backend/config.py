"""Centralized configuration for the web backend."""

import os
import sys

# Project root: memo_run/
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Database
DB_PATH = os.path.join(PROJECT_ROOT, "data", "runs.db")

# Add src/ to sys.path so we can import report_generator, pipeline, etc.
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# CORS -- read from environment, default to localhost dev servers
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
