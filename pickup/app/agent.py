"""Pickup voice agent — the AI side of the call.

A LiveKit support agent grounded in the Moss `support-kb` knowledge index. It
indexes EVERY turn (caller + agent) into a per-call Moss session, and on
escalation force-pushes that session to the cloud so a human can pick up the
exact memory via the Memory Service.

    python -m app.agent console     # talk in the terminal (needs OPENAI + DEEPGRAM)
    python -m app.agent dev         # connect from a browser (needs LIVEKIT_* too)

The session name is f"call-{room}" — the same name the human desk opens.
"""
from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent, AgentSession, ChatContext, ChatMessage, JobContext,
    RunContext, WorkerOptions, cli, function_tool,
)
from livekit.plugins import openai, deepgram, silero

from moss import MossClient, DocumentInfo, QueryOptions

# MiniMax (sponsor) is optional — fall back to OpenAI if its key is absent.
try:
    from livekit.plugins import minimax
except Exception:  # pragma: no cover
    minimax = None

load_dotenv()

KNOWLEDGE_INDEX = os.getenv("MOSS_INDEX_NAME", "support-kb")
DATA_TOPIC = "pickup"  # room data-channel topic the frontend listens on

logging.getLogger("livekit").setLevel(logging.WARNING)
logger = logging.getLogger("pickup-agent")
logger.setLevel(logging.INFO)

def _build_llm():
    if minimax and os.getenv("MINIMAX_API_KEY"):
        logger.info("LLM: MiniMax (MiniMax-Text-01)")
        return minimax.LLM(model=os.getenv("MINIMAX_LLM_MODEL", "MiniMax-Text-01"))
    logger.info("LLM: OpenAI (gpt-4o-mini)")
    return openai.LLM(model="gpt-4o-mini")


def _build_tts():
    if minimax and os.getenv("MINIMAX_API_KEY") and os.getenv("MINIMAX_GROUP_ID"):
        logger.info("TTS: MiniMax (speech-02-turbo)")
        return minimax.TTS(
            model="speech-02-turbo",
            voice_id=os.getenv("MINIMAX_VOICE", "presenter_female"),
            language_boost="English",
            sample_rate=24000,
        )
    logger.info("TTS: OpenAI")
    return openai.TTS()


def _build_stt():
    if os.getenv("DEEPGRAM_API_KEY"):
        return deepgram.STT()
    logger.info("STT: OpenAI (no Deepgram key)")
    return openai.STT()


SYSTEM_PROMPT = """You are a customer support voice agent for Orbit, a team
collaboration SaaS. You help with billing, plans, accounts, and security.

Use search_knowledge_base to ground every factual answer about Orbit's policies
(billing cycles, refunds, plans, cancellation, SSO, etc.). Never invent prices,
timelines, or policy. Answer in at most two short, conversational sentences.

Escalate with escalate_to_human when the caller: has a billing dispute or
duplicate charge needing a refund, reports fraud or account takeover, is clearly
upset and asks for a person, or needs an action you cannot perform (issuing
refunds, reversing charges). When you escalate, briefly reassure the caller that
a human specialist is joining with the full context of this call, so they will
not need to repeat anything.
"""


class SupportAgent(Agent):
    def __init__(self, ctx: JobContext, moss: MossClient, session, call_id: str):
        super().__init__(instructions=SYSTEM_PROMPT)
        self.ctx = ctx
        self.moss = moss
        self.moss_session = session   # per-call SessionIndex (Agent.session is reserved)
        self.call_id = call_id
        self._turn = 0
        self.escalated = False

    # --- publish structured events to the frontend over the room data channel ---
    async def _emit(self, payload: dict):
        try:
            await self.ctx.room.local_participant.publish_data(
                json.dumps(payload).encode("utf-8"), topic=DATA_TOPIC
            )
        except Exception as e:
            logger.warning(f"emit failed: {e}")

    async def _index_turn(self, speaker: str, text: str):
        if not text or not text.strip():
            return
        self._turn += 1
        try:
            await self.moss_session.add_docs([
                DocumentInfo(id=f"turn-{self._turn:03d}", text=f"[{speaker}] {text}",
                             metadata={"speaker": speaker})
            ])
        except Exception as e:
            logger.error(f"index turn failed: {e}")

    # --- tools ---
    @function_tool
    async def search_knowledge_base(self, context: RunContext, query: str) -> str:
        """Look up Orbit's policies and facts (billing, plans, accounts, security)."""
        res = await self.moss.query(KNOWLEDGE_INDEX, query, QueryOptions(top_k=4))
        await self._emit({"type": "context", "query": query,
                          "docs": [{"id": d.id, "text": d.text, "score": round(d.score, 3)}
                                   for d in res.docs]})
        return "\n".join(f"- {d.text}" for d in res.docs) or "No matching policy found."

    @function_tool
    async def escalate_to_human(self, context: RunContext, reason: str) -> str:
        """Hand the call to a human specialist with full context. Use for billing
        disputes, refunds, fraud, or when the caller asks for a person."""
        self.escalated = True
        logger.info(f"ESCALATING ({reason}) — pushing session '{self.call_id}'")
        try:
            await self.moss_session.push_index()  # make the memory available to the human NOW
        except Exception as e:
            logger.error(f"push on escalate failed: {e}")
        await self._emit({"type": "escalation", "call_id": self.call_id, "reason": reason})
        return ("Escalation ready. A human specialist can now open the full call "
                "memory. Reassure the caller they won't need to repeat anything.")

    # --- turn capture ---
    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        await self._index_turn("caller", new_message.text_content or "")
        await super().on_user_turn_completed(turn_ctx, new_message)


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    moss = MossClient(os.environ["MOSS_PROJECT_ID"], os.environ["MOSS_PROJECT_KEY"])

    await moss.load_index(KNOWLEDGE_INDEX)
    call_id = f"call-{ctx.room.name}"
    session = await moss.session(index_name=call_id)
    logger.info(f"📞 call session: '{call_id}' (knowledge='{KNOWLEDGE_INDEX}')")

    async def persist(*_):
        try:
            await session.push_index()
            logger.info(f"pushed session '{call_id}' on shutdown")
        except Exception as e:
            logger.error(f"shutdown push failed: {e}")
    ctx.add_shutdown_callback(persist)

    agent = SupportAgent(ctx, moss, session, call_id)

    agent_session = AgentSession(
        stt=_build_stt(),
        llm=_build_llm(),
        tts=_build_tts(),
        vad=silero.VAD.load(),
    )

    # Capture the agent's own turns into the session too (so the human sees both sides).
    @agent_session.on("conversation_item_added")
    def _on_item(ev):
        try:
            item = ev.item
            if getattr(item, "role", None) == "assistant":
                text = item.text_content if hasattr(item, "text_content") else str(getattr(item, "content", ""))
                # schedule async indexing without blocking the event callback
                import asyncio
                asyncio.create_task(agent._index_turn("agent", text or ""))
        except Exception as e:
            logger.warning(f"agent-turn capture failed: {e}")

    await agent_session.start(agent=agent, room=ctx.room)
    await agent_session.generate_reply(
        instructions="Greet the caller as Orbit support in one sentence and ask how you can help."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
