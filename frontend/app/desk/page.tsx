'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  type BriefingItem,
  type Memory,
  type QueryResult,
  type Turn,
  fetchMemory,
  queryMemory,
} from '@/lib/memory';
import { cn } from '@/lib/shadcn/utils';

function BriefingCard({ item }: { item: BriefingItem }) {
  return (
    <div className="border-border bg-card rounded-xl border p-4 shadow-sm">
      <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
        {item.label}
      </p>
      <p className="mt-1 text-sm leading-snug">{item.answer ?? '—'}</p>
    </div>
  );
}

function TurnBubble({ turn }: { turn: Turn }) {
  const isCaller = turn.speaker === 'caller';
  return (
    <div className={cn('flex', isCaller ? 'justify-start' : 'justify-end')}>
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-3 py-2 text-sm',
          isCaller ? 'bg-muted text-foreground' : 'bg-primary text-primary-foreground'
        )}
      >
        <span className="mb-0.5 block text-[10px] font-semibold uppercase opacity-60">
          {turn.speaker || 'unknown'}
        </span>
        {turn.text}
      </div>
    </div>
  );
}

function DeskInner() {
  const params = useSearchParams();
  const callFromUrl = params.get('call') ?? '';

  const [callId, setCallId] = useState(callFromUrl);
  const [memory, setMemory] = useState<Memory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [question, setQuestion] = useState('');
  const [answers, setAnswers] = useState<QueryResult[]>([]);
  const [asking, setAsking] = useState(false);

  const load = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true);
    setError(null);

    // Retry: the escalation push may still be propagating to Moss Cloud, so the
    // first fetch can 404 / return empty. Poll briefly until memory appears.
    let mem = null;
    for (let attempt = 0; attempt < 6; attempt++) {
      try {
        const m = await fetchMemory(id);
        if (m && m.doc_count > 0) {
          mem = m;
          break;
        }
      } catch {
        /* not propagated yet — retry */
      }
      await new Promise((r) => setTimeout(r, 700));
    }

    if (!mem) {
      setError('Could not load call memory yet');
      setMemory(null);
      setLoading(false);
      return;
    }

    setMemory(mem);
    setLoading(false);

    // Catch late-arriving turns (the agent's reassurance line lands a moment
    // after the handoff). Re-fetch a couple of times and adopt if it grew.
    for (const delay of [1800, 4000]) {
      setTimeout(async () => {
        try {
          const m2 = await fetchMemory(id);
          if (m2 && m2.doc_count >= mem.doc_count) setMemory(m2);
        } catch {
          /* ignore */
        }
      }, delay);
    }
  }, []);

  // Auto-load when arriving from the escalation link.
  useEffect(() => {
    if (callFromUrl) load(callFromUrl);
  }, [callFromUrl, load]);

  const ask = useCallback(async () => {
    if (!callId || !question.trim()) return;
    setAsking(true);
    try {
      const { results } = await queryMemory(callId, question.trim());
      setAnswers(results);
    } catch {
      setAnswers([]);
    } finally {
      setAsking(false);
    }
  }, [callId, question]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Agent Desk</h1>
          <p className="text-muted-foreground text-sm">
            Human takeover — full call memory, picked up from Moss by session name.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/desk/analytics"
            className="border-border hover:bg-muted rounded-lg border px-3 py-2 text-sm font-medium"
          >
            Analytics
          </Link>
          <button
            onClick={() => load(callId)}
            className="border-border hover:bg-muted rounded-lg border px-3 py-2 text-sm font-medium"
          >
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Call id input (fallback when not arriving from a link) */}
      <div className="mb-6 flex gap-2">
        <input
          value={callId}
          onChange={(e) => setCallId(e.target.value)}
          placeholder="call-voice_assistant_room_1234"
          className="border-border bg-background flex-1 rounded-lg border px-3 py-2 text-sm"
        />
        <button
          onClick={() => load(callId)}
          className="bg-primary text-primary-foreground rounded-lg px-4 py-2 text-sm font-semibold"
        >
          Take over
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-600">
          {error}. Is the memory service running on port 8000, and has the call been pushed?
        </div>
      )}

      {loading && !memory && (
        <div className="text-muted-foreground py-12 text-center text-sm">
          Loading call memory…
        </div>
      )}

      {memory && (
        <>
          <div className="text-muted-foreground mb-4 text-xs">
            Picked up <span className="font-mono">{memory.call_id}</span> · {memory.doc_count}{' '}
            turns of memory
          </div>

          {/* Briefing */}
          <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">Instant briefing</h2>
          <div className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {memory.briefing.map((b) => (
              <BriefingCard key={b.label} item={b} />
            ))}
          </div>

          {/* Ask the memory */}
          <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">Ask the call memory</h2>
          <div className="mb-3 flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && ask()}
              placeholder="e.g. did we confirm it's a real duplicate?"
              className="border-border bg-background flex-1 rounded-lg border px-3 py-2 text-sm"
            />
            <button
              onClick={ask}
              className="bg-primary text-primary-foreground rounded-lg px-4 py-2 text-sm font-semibold"
            >
              {asking ? '…' : 'Ask'}
            </button>
          </div>
          {answers.length > 0 && (
            <ul className="mb-8 space-y-2">
              {answers.map((a) => (
                <li key={a.id} className="border-border bg-card rounded-lg border p-3 text-sm">
                  <span className="text-muted-foreground text-[10px] font-semibold uppercase">
                    {a.speaker} · {a.score.toFixed(2)}
                  </span>
                  <p>{a.text}</p>
                </li>
              ))}
            </ul>
          )}

          {/* Full transcript */}
          <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">Full transcript</h2>
          <div className="space-y-2">
            {memory.turns.map((t) => (
              <TurnBubble key={t.id} turn={t} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}

export default function DeskPage() {
  return (
    <Suspense fallback={<div className="text-muted-foreground p-8 text-sm">Loading…</div>}>
      <DeskInner />
    </Suspense>
  );
}
