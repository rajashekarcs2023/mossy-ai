// Client for the Pickup Memory Service (FastAPI). The Agent Desk uses this to
// open a call's Moss session by name and read its memory — the human takeover.

export const MEMORY_URL = process.env.NEXT_PUBLIC_MEMORY_URL ?? 'http://localhost:8000';

export type Turn = { id: string; speaker: string; text: string };
export type BriefingItem = { label: string; answer: string | null; score: number };
export type Memory = {
  call_id: string;
  doc_count: number;
  turns: Turn[];
  briefing: BriefingItem[];
};
export type QueryResult = { id: string; speaker: string; text: string; score: number };

export async function fetchMemory(callId: string): Promise<Memory> {
  const res = await fetch(`${MEMORY_URL}/memory/${encodeURIComponent(callId)}`, {
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Memory service returned ${res.status}`);
  return res.json();
}

export async function queryMemory(
  callId: string,
  query: string
): Promise<{ results: QueryResult[] }> {
  const res = await fetch(`${MEMORY_URL}/memory/${encodeURIComponent(callId)}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: 3 }),
  });
  if (!res.ok) throw new Error(`Memory query returned ${res.status}`);
  return res.json();
}
