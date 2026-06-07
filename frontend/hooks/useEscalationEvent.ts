import { useEffect, useState } from 'react';
import { RoomEvent } from 'livekit-client';
import { useRoomContext } from '@livekit/components-react';

const textDecoder = new TextDecoder();

export type EscalationEvent = {
  callId: string;
  reason: string;
  /** Timestamp in milliseconds since epoch */
  timestamp: number;
};

/**
 * Subscribes to the agent's `escalation` data message. The agent publishes this
 * (once) when it calls `escalate_to_human`, after force-pushing the call's Moss
 * session. The payload's `call_id` is the session name a human opens to take
 * over with the full conversation memory. Must be used within a RoomContext.
 */
export function useEscalationEvent() {
  const room = useRoomContext();
  const [escalation, setEscalation] = useState<EscalationEvent | null>(null);

  useEffect(() => {
    if (!room) return;

    const handle = (payload: Uint8Array) => {
      try {
        const msg = JSON.parse(textDecoder.decode(payload));
        if (!msg || msg.type !== 'escalation' || typeof msg.data !== 'object') return;
        const d = msg.data as Record<string, unknown>;
        if (typeof d.call_id !== 'string') return;
        setEscalation({
          callId: d.call_id,
          reason: typeof d.reason === 'string' ? d.reason : '',
          timestamp: (typeof d.timestamp === 'number' ? d.timestamp : Date.now() / 1000) * 1000,
        });
      } catch {
        /* ignore malformed packets */
      }
    };

    room.on(RoomEvent.DataReceived, handle);
    return () => {
      room.off(RoomEvent.DataReceived, handle);
    };
  }, [room]);

  return escalation;
}
