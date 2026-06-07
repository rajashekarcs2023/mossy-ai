# Pickup — the AI front desk that never forgets

> A team of specialist voice AIs that hand off calls to each other with **shared memory**, so customers never repeat themselves.

Built for the **YC × Moss Conversational AI Hackathon** on **Moss** (real-time memory), **LiveKit** (voice), and **MiniMax** (briefing).

---

## The problem

Local clinics and businesses miss up to a third of their calls, and the ones that get answered are stateless — every AI receptionist is a goldfish. Callers re-explain who they are and what they need *every single time*, and when the bot can't handle something it dumps them to a colleague who picks up **blind**. "I had to explain my problem three times" is the #1 customer-service complaint.

Voice models are cheap and fast now. **The bottleneck is memory.**

## The idea

Pickup is a front desk staffed by a **team of specialist voice AIs** — a receptionist, a billing & insurance specialist, and a scheduling coordinator — that **hand the live call to one another** as the conversation moves between topics. They all read and write **one shared [Moss](https://usemoss.dev) session** (the team's brain), so when a new specialist takes over, their first words already know the whole story. The same memory persists **per customer across calls and channels**, so a returning caller is greeted with what they told you last time.

One primitive — a portable, in-process, semantically-searchable Moss session — viewed by the whole team.

## How it works

```
 Caller ──voice──▶  LiveKit  ──▶  Reception AI ──hand off──▶ Billing AI ──hand off──▶ Scheduling AI
                                      │                 │                    │
                                      └──────── shared Moss session "customer-<id>" ────────┘
                                              (every turn + action written; <10ms reads)
```

- **Moss** — each customer is a named Moss session. Every turn and action is written in-process (~1–10 ms); each specialist queries it on takeover. Persists to the cloud so it survives across calls, channels, and the hand-off.
- **LiveKit** — real-time STT/LLM/TTS via LiveKit Inference, in-call multi-agent hand-off (each specialist has a distinct voice), and a live "what the AI is retrieving" panel over data channels.
- **MiniMax** — synthesizes a crisp briefing of the call memory for the human/agent desk.

## What it does

- **Answers** practice questions (hours, insurance, costs, services), grounded in real info — never hallucinated.
- **Books & reschedules** appointments and **takes messages** so no call is lost.
- **Routes** to the right specialist AI mid-call, carrying full context.
- **Remembers returning callers** across calls — they never start over.
- **Agent Desk** (`/desk`) — a human can open the same memory: instant briefing + transcript + ask-the-memory.

## Repo structure

```
frontend/   Next.js voice UI — live call, knowledge panel, and the Agent Desk
agent/      Python LiveKit voice-agent team (reception → billing → scheduling)
pickup/     FastAPI memory service (human/agent takeover) + the de-risk spike + support KB
```

## Run it

You need **LiveKit** and **Moss** credentials (and a MiniMax key for the briefing). Speech runs through LiveKit Inference, so those are most of the secrets.

```bash
# 1) Agent (Python, uv)
cd agent
cp .env.example .env.local            # add LIVEKIT_* + MOSS_* (+ MINIMAX_* optional)
uv sync
uv run src/create_index.py            # build the knowledge index from knowledge.json
uv run src/agent.py dev               # registers the voice-agent team

# 2) Frontend (Next.js, pnpm)
cd ../frontend
cp .env.example .env.local            # add LIVEKIT_* + AGENT_NAME=agent-py
pnpm install && pnpm dev              # http://localhost:3000

# 3) Memory service (FastAPI) — powers the Agent Desk
cd ../pickup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # add MOSS_* (+ MINIMAX_* for synthesized briefing)
uvicorn app.memory_service:app --port 8000
```

Open http://localhost:3000, start a call, and move between topics — listen as a new specialist voice takes over already knowing everything.

## Why it's a company, not a feature

"Context on hand-off" is a feature. A **portable memory layer** that works across every channel, agent, and human — keyed to the customer, not the call — is infrastructure. The hard problems behind it: identity resolution across channels, memory curation (what to keep, summarize, decay), privacy and consent, and integrations into every channel and practice-management system.

---

See [`SUBMISSION.md`](./SUBMISSION.md) for the full write-up.
