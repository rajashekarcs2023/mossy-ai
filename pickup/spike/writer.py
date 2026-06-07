"""WRITER — simulates the AI voice agent during a live support call.

It opens a session by name, indexes each conversation turn locally as it
"happens", then pushes the session to Moss Cloud. In the real product this
runs inside the LiveKit agent; here it stands alone so we can prove the
handoff in isolation.

    python writer.py

Then, in a SEPARATE terminal, run reader.py to take over the call.
"""
import asyncio

from moss import DocumentInfo, QueryOptions
from _shared import SESSION_NAME, make_client, timed

# A scripted support call: customer with a duplicate-charge billing dispute.
CALL_TURNS = [
    ("turn-1", "caller", "Hi, I think I got charged twice for my Orbit subscription this month."),
    ("turn-2", "agent", "I'm sorry about that. I can see your account, Maya. Two charges of $49.99 posted on the 3rd."),
    ("turn-3", "caller", "Yeah exactly, two times forty nine ninety nine. I only have one subscription."),
    ("turn-4", "agent", "Both charges have fully settled, so this is a genuine duplicate, not a temporary hold."),
    ("turn-5", "caller", "Okay good. I'd like the extra one refunded, and honestly I'm pretty frustrated."),
    ("turn-6", "caller", "This is the second month in a row this has happened and I want to talk to a person."),
]


async def main():
    client = make_client()

    print(f"\n=== WRITER: live AI call → session '{SESSION_NAME}' ===")
    with timed("open session"):
        session = await client.session(index_name=SESSION_NAME)
    print(f"  session opened with {session.doc_count} existing docs")

    # Index each turn locally as the conversation unfolds (no network per turn).
    for tid, speaker, text in CALL_TURNS:
        with timed(f"add_docs ({tid})"):
            await session.add_docs([
                DocumentInfo(id=tid, text=f"[{speaker}] {text}", metadata={"speaker": speaker})
            ])
        print(f"    {speaker:>6}: {text}")

    # Sanity: the agent can recall earlier context in-process during the call.
    print("\n  -- in-call recall (agent querying its own session) --")
    with timed("session.query"):
        res = await session.query("what is the customer upset about", QueryOptions(top_k=3))
    for d in res.docs:
        print(f"    [{d.score:.3f}] {d.text}")

    # ESCALATION: force-push so a human in another process can pick up fresh memory.
    print("\n  -- escalation: pushing session to cloud for handoff --")
    with timed("push_index"):
        result = await session.push_index()
    print(f"  ✅ pushed {result.doc_count} docs to cloud session '{SESSION_NAME}' (job {result.job_id})")
    print(f"\nNow run:  python reader.py   (in a separate terminal)\n")


if __name__ == "__main__":
    asyncio.run(main())
