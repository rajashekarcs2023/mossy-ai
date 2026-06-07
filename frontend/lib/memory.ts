// Client for the Pickup Memory Service (FastAPI). The Agent Desk uses this to
// open a call's Moss session by name and read its memory — the human takeover.

export const MEMORY_URL = process.env.NEXT_PUBLIC_MEMORY_URL ?? 'http://localhost:8000';

// Staff auth: the memory service enforces this header on /memory/* and /analytics
// when PICKUP_STAFF_KEY is set server-side (otherwise it allows + warns, so
// dev/demo keeps working). We always send it; "" is fine when unset.
function staffHeaders(extra?: Record<string, string>): Record<string, string> {
  return {
    'X-Pickup-Key': process.env.NEXT_PUBLIC_PICKUP_KEY ?? '',
    ...extra,
  };
}

export type Turn = { id: string; speaker: string; text: string };
export type BriefingItem = { label: string; answer: string | null; score: number };
export type Memory = {
  call_id: string;
  doc_count: number;
  turns: Turn[];
  briefing: BriefingItem[];
};
export type QueryResult = { id: string; speaker: string; text: string; score: number };

export type IntentCount = { intent: string; count: number };
export type LanguageCount = { lang: string; count: number };
export type Analytics = {
  total_calls: number;
  bookings: number;
  messages: number;
  escalations: number;
  by_intent: IntentCount[];
  languages: LanguageCount[];
};

export async function fetchMemory(callId: string): Promise<Memory> {
  const res = await fetch(`${MEMORY_URL}/memory/${encodeURIComponent(callId)}`, {
    cache: 'no-store',
    headers: staffHeaders(),
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
    headers: staffHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ query, top_k: 3 }),
  });
  if (!res.ok) throw new Error(`Memory query returned ${res.status}`);
  return res.json();
}

// Right-to-be-forgotten: delete a single call's session index.
export async function deleteMemory(callId: string): Promise<{ call_id: string; deleted: boolean }> {
  const res = await fetch(`${MEMORY_URL}/memory/${encodeURIComponent(callId)}`, {
    method: 'DELETE',
    cache: 'no-store',
    headers: staffHeaders(),
  });
  if (!res.ok) throw new Error(`Memory delete returned ${res.status}`);
  return res.json();
}

export async function fetchAnalytics(): Promise<Analytics> {
  const res = await fetch(`${MEMORY_URL}/analytics`, {
    cache: 'no-store',
    headers: staffHeaders(),
  });
  if (!res.ok) throw new Error(`Analytics returned ${res.status}`);
  return res.json();
}
