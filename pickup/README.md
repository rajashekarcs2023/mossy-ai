# Pickup — the memory that survives the handoff

A support voice AI that hands a live call to a human with its **entire memory
intact**, so the customer never repeats themselves. Built on **Moss** (portable
conversational memory) + **LiveKit** (voice) for the YC × Moss hackathon.

The core idea in one primitive: a single live Moss **session** that the AI writes
to during a call and a human **opens by name** to take over — full searchable
memory, no lossy summary, no re-embedding.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in MOSS_PROJECT_ID / MOSS_PROJECT_KEY
```

## Step 1 — de-risk spike (run this first)

Proves the whole product: a session written in one process, picked up in another.

```bash
python build_index.py          # create the support knowledge base (once)

python spike/writer.py         # terminal A: simulate the AI call + push
python spike/reader.py         # terminal B: human takes over the SAME session
```

If `reader.py` recalls the call in a fresh process → **GO**. Everything else builds on this.

## Architecture (3 processes, 1 idea)

1. **Voice agent** (LiveKit worker) — ambient retrieval over `support-kb`, writes
   each turn to the call's session, force-pushes on escalation.
2. **Memory service** (FastAPI) — opens `session(call_id)` independently; serves
   the human takeover. *(this is the spike, productized)*
3. **Web app** (Next.js) — Live Call view (transcript + live context) and Agent
   Desk view (Take Over → full memory + query).

See `project-dev/` (parent repo) for Moss concept docs.
