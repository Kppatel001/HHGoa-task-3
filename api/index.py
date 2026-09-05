"""Vercel Python serverless entrypoint.

Vercel's @vercel/python runtime serves the ASGI `app` exported here. All routes
are rewritten to this function (see backend/vercel.json), so FastAPI receives the
original path (e.g. /api/health) and matches its own routes.
"""
import os, sys

# Ensure the backend package root (this file's parent) is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402  (ASGI app Vercel will serve)
