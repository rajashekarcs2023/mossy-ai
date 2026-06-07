'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { type Analytics, fetchAnalytics } from '@/lib/memory';

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="border-border bg-card rounded-xl border p-5 shadow-sm">
      <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">{label}</p>
      <p className="mt-2 text-4xl font-bold tabular-nums">{value}</p>
    </div>
  );
}

function isEmpty(a: Analytics): boolean {
  return (
    a.total_calls === 0 &&
    a.bookings === 0 &&
    a.messages === 0 &&
    a.escalations === 0 &&
    a.by_intent.length === 0
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const a = await fetchAnalytics();
      setData(a);
    } catch {
      setError(true);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const empty = !loading && !error && data !== null && isEmpty(data);
  const showStats = !loading && !error && data !== null && !empty;

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground text-sm">
            Call volume, bookings, messages and escalations across recent sessions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/desk"
            className="border-border hover:bg-muted rounded-lg border px-3 py-2 text-sm font-medium"
          >
            Back to Desk
          </Link>
          <button
            onClick={load}
            className="border-border hover:bg-muted rounded-lg border px-3 py-2 text-sm font-medium"
          >
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-muted-foreground py-12 text-center text-sm">Loading analytics…</div>
      )}

      {error && (
        <div className="border-border bg-card rounded-xl border p-8 text-center">
          <p className="text-sm font-medium">Analytics service unavailable</p>
          <p className="text-muted-foreground mt-1 text-sm">
            Could not reach the memory service. Is it running on port 8000?
          </p>
        </div>
      )}

      {empty && (
        <div className="border-border bg-card rounded-xl border p-8 text-center">
          <p className="text-sm font-medium">No analytics yet</p>
          <p className="text-muted-foreground mt-1 text-sm">
            Once calls start flowing through Moss, stats will show up here.
          </p>
        </div>
      )}

      {showStats && data && (
        <>
          <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard label="Calls handled" value={data.total_calls} />
            <StatCard label="Bookings" value={data.bookings} />
            <StatCard label="Messages" value={data.messages} />
            <StatCard label="Escalations" value={data.escalations} />
          </div>

          <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">Top intents</h2>
          {data.by_intent.length > 0 ? (
            <ul className="space-y-2">
              {data.by_intent.map((i) => (
                <li
                  key={i.intent}
                  className="border-border bg-card flex items-center justify-between rounded-lg border px-4 py-3 text-sm"
                >
                  <span className="font-medium">{i.intent}</span>
                  <span className="text-muted-foreground tabular-nums">{i.count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground text-sm">No intent data yet.</p>
          )}
        </>
      )}
    </main>
  );
}
