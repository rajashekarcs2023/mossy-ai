"""Shared helpers for the Pickup de-risk spike."""
import os
import time
from contextlib import contextmanager

from dotenv import load_dotenv
from moss import MossClient

load_dotenv()

# The session name is the ONLY thing the writer and reader share.
# In the real product this is the call id (e.g. f"call-{room}").
SESSION_NAME = os.getenv("PICKUP_SESSION", "call-demo-001")


def make_client() -> MossClient:
    pid = os.environ.get("MOSS_PROJECT_ID")
    key = os.environ.get("MOSS_PROJECT_KEY")
    if not pid or not key:
        raise SystemExit(
            "Missing MOSS_PROJECT_ID / MOSS_PROJECT_KEY. "
            "Copy .env.example to .env and fill in creds from https://portal.usemoss.dev"
        )
    return MossClient(pid, key)


@contextmanager
def timed(label: str):
    """Print how long a block takes in ms."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = (time.perf_counter() - t0) * 1000
        print(f"  ⏱  {label}: {dt:.1f} ms")
