# Pickup — the AI front desk that never forgets

> A team of specialist voice AIs that hand a live call off to one another while sharing one memory, so callers never repeat themselves.

## What it is

Pickup is an AI phone front desk for clinics and local businesses. Instead of a single stateless bot, it's a **team of specialist voice agents** — a receptionist, a billing & insurance specialist, and a scheduling coordinator — that transfer the live call between each other as the conversation moves between topics. Every agent reads and writes **one shared, persistent memory** of the caller, so whoever picks up already knows the whole story, and a returning caller is recognized across calls.

## The problem

Local businesses miss a large share of inbound calls, and the AI receptionists meant to fix that are stateless: every call starts from zero, callers re-explain themselves each time, and when the bot can't handle something it hands off to a person (or another bot) that starts blind. Modern voice models are fast and cheap — **the real bottleneck is memory that survives across turns, agents, and calls.**

## How it works

```
 Caller ──voice──▶  Reception ──hand off──▶  Billing ──hand off──▶  Scheduling
                        │              │                  │
                        └──────  shared memory: session "customer-<id>"  ──────┘
                               every turn + action written; sub-10ms reads
```

**Shared memory (the core).** Each caller maps to a named [Moss](https://docs.moss.dev) session — an in-process, semantically-searchable index. Every turn and every action (a booking, a message) is written to it in ~1–10 ms, with no network round trip on reads. When one specialist hands the call to the next, the new agent simply *queries the same session* for context, so its first words already reference the caller's situation. The session is pushed to the cloud, so the memory persists **per customer across calls and channels** — a process started on today's call can be resumed on the next one, or opened by a human.

**Voice + handoff.** The realtime pipeline (speech-to-text, LLM, text-to-speech, turn detection) runs on [LiveKit](https://docs.livekit.io/agents) Agents. Specialists are first-class agents with distinct voices; a handoff is a tool call that transfers control within the same call while LiveKit preserves the conversation. A data channel streams what each agent retrieves to the UI in real time.

**Agent Desk.** A separate FastAPI service opens any caller's session by name and exposes it to a human: an instant briefing, the full transcript, and a free-text "ask the memory" box — the same memory the AI used, now queryable by a person.

## Repo structure

```
frontend/   Next.js voice UI — live call, live retrieval panel, and the Agent Desk
agent/      Python LiveKit voice-agent team (reception → billing → scheduling)
pickup/     FastAPI memory service (human/agent takeover) + the support knowledge base
```

## Running it

Requires a LiveKit project and a Moss project. Speech models run through LiveKit Inference, so those are most of the credentials.

```bash
# 1) Agent (Python, uv)
cd agent
cp .env.example .env.local            # LIVEKIT_* + MOSS_*
uv sync
uv run src/create_index.py            # build the knowledge index from knowledge.json
uv run src/agent.py dev               # registers the voice-agent team

# 2) Frontend (Next.js, pnpm)
cd ../frontend
cp .env.example .env.local            # LIVEKIT_* + AGENT_NAME=agent-py
pnpm install && pnpm dev              # http://localhost:3000

# 3) Memory service (FastAPI) — powers the Agent Desk
cd ../pickup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # MOSS_*
uvicorn app.memory_service:app --port 8000
```

Open http://localhost:3000, start a call, and move between topics — listen as a new specialist voice takes over already knowing everything.

## Why it's hard

Turning this into real infrastructure means solving the unglamorous problems behind a portable memory layer: resolving one identity across phone numbers, emails, and devices; deciding what to keep, summarize, and forget; consent and deletion on persistent customer memory; and integrating with the channels and systems a business already runs.
