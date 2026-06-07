"""Create the support knowledge base index in Moss from data/support_kb.json.

    python build_index.py     # run once before the agent / spike
"""
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from moss import MossClient, DocumentInfo

load_dotenv()
INDEX = os.getenv("MOSS_INDEX_NAME", "support-kb")


async def main():
    pid, key = os.environ.get("MOSS_PROJECT_ID"), os.environ.get("MOSS_PROJECT_KEY")
    if not pid or not key:
        raise SystemExit("Set MOSS_PROJECT_ID / MOSS_PROJECT_KEY in .env first.")
    client = MossClient(pid, key)

    kb = Path(__file__).parent / "data" / "support_kb.json"
    entries = json.loads(kb.read_text(encoding="utf-8"))
    docs = [DocumentInfo(id=e["id"], text=e["text"], metadata=e.get("metadata")) for e in entries]

    print(f"indexing {len(docs)} support docs into '{INDEX}'...")
    await client.create_index(INDEX, docs, model_id="moss-minilm")
    print("done.")


if __name__ == "__main__":
    asyncio.run(main())
