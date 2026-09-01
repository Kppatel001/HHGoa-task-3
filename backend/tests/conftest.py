import os
import sys

# Ensure the backend package root is importable when running `pytest` from anywhere.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Use an isolated demo config + temp DB for tests.
os.environ.setdefault("SEARCH_PROVIDER", "demo")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_faceproof.db")
os.environ.setdefault("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
