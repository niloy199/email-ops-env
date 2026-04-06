"""
server/app.py — Entry point for multi-mode deployment.
Imports and re-exports the FastAPI app from main.py.
"""
import sys
import os

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main import app

__all__ = ["app"]