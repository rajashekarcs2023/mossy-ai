'use client';

import * as React from 'react';
import type { EscalationEvent } from '@/hooks/useEscalationEvent';
import { cn } from '@/lib/shadcn/utils';

interface EscalationBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  escalation: EscalationEvent | null;
}

/**
 * Shown when the agent escalates. Links the human to the Agent Desk, which opens
 * the same Moss session by name — the full call memory, zero context loss.
 */
export function EscalationBanner({ escalation, className, ...props }: EscalationBannerProps) {
  if (!escalation) return null;

  const deskUrl = `/desk?call=${encodeURIComponent(escalation.callId)}`;

  return (
    <div
      className={cn(
        'pointer-events-auto flex items-center justify-between gap-4 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 shadow-lg backdrop-blur',
        className
      )}
      {...props}
    >
      <div className="min-w-0">
        <p className="text-sm font-semibold text-amber-600 dark:text-amber-400">
          Escalated to a human specialist
        </p>
        <p className="text-muted-foreground truncate text-xs">
          {escalation.reason || 'A specialist can pick up this call with full context.'}
        </p>
      </div>
      <a
        href={deskUrl}
        target="_blank"
        rel="noreferrer"
        className="shrink-0 rounded-lg bg-amber-500 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-amber-600"
      >
        Open Agent Desk →
      </a>
    </div>
  );
}
