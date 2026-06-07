"""Pickup Memory Service — the human takeover endpoint.

A standalone FastAPI process that opens a call's Moss session BY NAME and serves
its memory to the human agent's desk. It shares nothing with the voice agent
except the session name — opening session(call_id) here pulls the full
conversation from Moss Cloud. That is the literal proof of portable memory.

    uvicorn app.memory_service:app --reload --port 8000

Endpoints:
    GET  /health
    GET  /memory/{call_id}            -> ordered transcript + auto-briefing
    POST /memory/{call_id}/query      -> semantic query over the call memory
"""
import os
import re
import json
import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from moss import MossClient, GetDocumentsOptions, QueryOptions

load_dotenv()
logger = logging.getLogger("pickup-memory")

# MiniMax (sponsor) — used to SYNTHESIZE the human briefing from the recalled
# Moss session turns. OpenAI-compatible endpoint; falls back to raw retrieval
# if the key is missing or the call fails, so it can never make the demo worse.
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
MINIMAX_LLM_MODEL = os.getenv("MINIMAX_LLM_MODEL", "MiniMax-Text-01")

# Questions the human needs answered the instant they pick up a support call.
BRIEFING = [
    ("Calling about", "what is the patient calling about"),
    ("Appointment", "any appointment to book, reschedule, or cancel"),
    ("Insurance / cost", "any insurance, billing, or cost question raised"),
    ("Mood", "what is the patient's emotional state"),
    ("Next step", "what the front desk already did or why it is handing to a person"),
]

_client: MossClient | None = None
_sessions: dict = {}  # call_id -> SessionIndex cache


def _turn_order(doc_id: str) -> int:
    """Sort 'turn-3' / 'user-turn-12' by their trailing number."""
    m = re.search(r"(\d+)\s*$", doc_id or "")
    return int(m.group(1)) if m else 0


def _clean(text: str) -> tuple[str, str]:
    """Split a stored '[speaker] text' doc into (speaker, text)."""
    m = re.match(r"^\[(\w+)\]\s*(.*)$", text or "", re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return "", text or ""


async def _get_session(call_id: str, refresh: bool = False):
    """Open (or reuse) a call's session. Opening pulls the latest pushed memory."""
    if refresh or call_id not in _sessions:
        try:
            _sessions[call_id] = await _client.session(index_name=call_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"No memory for call '{call_id}': {e}")
    return _sessions[call_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    pid, key = os.environ.get("MOSS_PROJECT_ID"), os.environ.get("MOSS_PROJECT_KEY")
    if not pid or not key:
        raise RuntimeError("Set MOSS_PROJECT_ID / MOSS_PROJECT_KEY in .env")
    _client = MossClient(pid, key)
    yield


app = FastAPI(title="Pickup Memory Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryBody(BaseModel):
    query: str
    top_k: int = 3


@app.get("/health")
async def health():
    return {"ok": True, "cached_calls": list(_sessions.keys())}


@app.get("/memory/{call_id}")
async def get_memory(call_id: str, refresh: bool = True):
    """Full call memory: ordered transcript + an auto-generated human briefing."""
    session = await _get_session(call_id, refresh=refresh)

    docs = await session.get_docs(GetDocumentsOptions(doc_ids=None))
    docs.sort(key=lambda d: _turn_order(d.id))
    turns = []
    for d in docs:
        speaker, text = _clean(d.text)
        meta = getattr(d, "metadata", None) or {}
        turns.append({"id": d.id, "speaker": speaker or meta.get("speaker", ""), "text": text})

    # Briefing: MiniMax-synthesized from the full transcript (crisp, correct),
    # falling back to raw Moss retrieval if MiniMax is unavailable.
    briefing = await _synthesize_briefing(turns)
    if briefing is None:
        briefing = await _retrieval_briefing(session)

    return {"call_id": call_id, "doc_count": session.doc_count, "turns": turns, "briefing": briefing}


async def _retrieval_briefing(session) -> list[dict]:
    """Fallback: one semantic query per heads-up question (raw closest turn)."""
    async def ask(label, q):
        res = await session.query(q, QueryOptions(top_k=2))
        if res.docs:
            _, text = _clean(res.docs[0].text)
            return {"label": label, "answer": text, "score": round(res.docs[0].score, 3)}
        return {"label": label, "answer": None, "score": 0.0}

    return list(await asyncio.gather(*(ask(label, q) for label, q in BRIEFING)))


async def _synthesize_briefing(turns: list[dict]) -> list[dict] | None:
    """Use MiniMax to write a crisp one-line answer per briefing field, grounded
    ONLY in the transcript. Returns None on any failure so the caller falls back."""
    if not MINIMAX_API_KEY or not turns:
        return None

    transcript = "\n".join(f"{t['speaker'] or 'unknown'}: {t['text']}" for t in turns)
    labels = [label for label, _ in BRIEFING]
    system = (
        "You brief a human support agent who is taking over a live call. Read the "
        "transcript and return ONLY a compact JSON object with these exact keys: "
        + ", ".join(labels) + ". Each value is one short, factual sentence grounded "
        "ONLY in the transcript (no guessing; use 'unclear' if not stated). "
        "'Next step' = what the AI front desk already did or why it is handing to a person."
    )
    payload = {
        "model": MINIMAX_LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Transcript:\n{transcript}\n\nReturn the JSON now."},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
                json=payload,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        # Tolerate code fences / stray prose around the JSON object.
        match = re.search(r"\{.*\}", content, re.DOTALL)
        data = json.loads(match.group(0) if match else content)
        return [
            {"label": label, "answer": str(data.get(label, "unclear")).strip(), "score": 1.0}
            for label in labels
        ]
    except Exception as e:
        logger.warning("MiniMax briefing synthesis failed (%s); using retrieval fallback", e)
        return None


@app.post("/memory/{call_id}/query")
async def query_memory(call_id: str, body: QueryBody):
    """Let the human ask a free-form question of the call memory (sub-10ms)."""
    session = await _get_session(call_id, refresh=False)
    res = await session.query(body.query, QueryOptions(top_k=body.top_k))
    results = []
    for d in res.docs:
        speaker, text = _clean(d.text)
        results.append({"id": d.id, "speaker": speaker, "text": text, "score": round(d.score, 3)})
    return {"call_id": call_id, "query": body.query, "results": results}
