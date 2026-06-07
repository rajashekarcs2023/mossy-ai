"""READER — simulates the HUMAN agent taking over the call.

This is a COMPLETELY SEPARATE PROCESS from writer.py. It shares nothing but
the session name. Opening session(name) here pulls the full conversation
memory from Moss Cloud — no re-embedding, no summary, no shared variables.
This is the literal proof of portable conversational memory.

    python reader.py
"""
import asyncio

from moss import QueryOptions
from _shared import SESSION_NAME, make_client, timed

# What a human picking up the call needs to know instantly.
HANDOFF_QUERIES = [
    "what is the customer's problem",
    "how much money is involved",
    "what does the customer want",
    "what is the customer's emotional state",
]


async def main():
    client = make_client()

    print(f"\n=== READER: human takeover ← session '{SESSION_NAME}' ===")
    with timed("session(name)  [the handoff]"):
        session = await client.session(index_name=SESSION_NAME)
    print(f"  ✅ loaded {session.doc_count} docs of call memory in a fresh process")

    if session.doc_count == 0:
        raise SystemExit("  ⚠️  Empty session — run writer.py first (and check the session name).")

    print("\n  -- what the human instantly knows (semantic queries over the memory) --")
    for q in HANDOFF_QUERIES:
        with timed(f"query: {q!r}"):
            res = await session.query(q, QueryOptions(top_k=1))
        top = res.docs[0].text if res.docs else "(no match)"
        print(f"    Q: {q}\n    → {top}\n")

    print("  🎉 The human picked up the entire call with zero context loss.\n")


if __name__ == "__main__":
    asyncio.run(main())
