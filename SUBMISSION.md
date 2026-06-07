# Pickup — the AI front desk that never forgets

**Track:** Support · **Built on:** Moss (memory) · LiveKit (voice) · MiniMax (briefing)

> An AI front desk for clinics and local businesses that **remembers every caller across every call** — and when it hands off to a human, the human already knows everything. Patients never repeat themselves. To anyone. Ever.

---

## The problem

Local businesses live and die by the phone. A dental office misses **~30% of inbound calls**, and each missed call is a lost patient worth thousands in lifetime value. So everyone is racing to put an **AI receptionist** on the phone.

But today's AI receptionists are **goldfish** — they're *stateless*. Every call starts from zero:

- The patient re-explains who they are and what they need, *every single time*.
- When the AI can't handle something (an insurance dispute, a treatment-plan question), it dumps the caller to a human who picks up **completely blind** — and makes them explain it *all over again*.

"I had to explain my problem three times" is the **#1 customer-service complaint**, and it happens at the exact moment a business is trying to win or keep someone.

**The bottleneck isn't the voice anymore — it's the memory.**

## What Pickup is

An AI front desk with a **shared, persistent memory** that the AI *and* the human staff both read and write:

1. **It answers every call**, grounded in the practice's real info (hours, insurance, costs, services) — no hallucinated prices.
2. **It remembers each caller across calls and channels.** A returning patient is greeted with their history; they never start over.
3. **When it hands off to a human, the human already knows everything.** A care coordinator joins the *same call* and their first words reference the caller's exact situation — pulled live from the shared memory — so the patient never repeats a word.

The magic moment, live: you ask for a person, and **a different voice picks up that already knows your whole story.**

### What it does today

- **Answers** any practice question (hours, insurance, costs, services), grounded in real info — never hallucinated.
- **Books appointments** — captures the service and time and confirms, then logs it to the patient's memory.
- **Takes messages** — name, callback, and reason, so no after-hours or overflow call is ever lost.
- **Remembers returning patients** — greets them with a specific detail from a prior call; they never start over.
- **Escalates to a human in-call** — a care coordinator joins the same call already knowing the full history.
- **Persists memory per customer** — across calls, channels, and the AI→human seam.

## Why this is hard / why now

Voice models got cheap and fast in 2026 — that part is solved. What's *not* solved is giving a conversation a **memory that outlives the speaker** and travels across the AI→human seam, across channels, and across time. Every "warm transfer" product on the market today passes a **frozen text summary**. Pickup passes the **living, searchable memory itself**.

## How it works (and why each sponsor is load-bearing)

- **Moss** is the memory. Each caller is a Moss **session** keyed by customer. The AI writes every turn into it in-process (**sub-10ms**); when it escalates, the human opens *the same session by name* in a separate process and instantly has a live, **queryable** memory — not a summary, no re-embedding. This is the entire product, and it is *only* practical because Moss runs retrieval in-process. *(We verified the cross-process handoff cold: process A writes + pushes, process B reopens by name and recalls — 3–7ms queries.)*
- **LiveKit** is the voice + the handoff. Real-time STT/LLM/TTS via LiveKit Inference, a live "what the AI is retrieving" panel over data channels, and a first-class **in-call multi-agent handoff** — the care coordinator joins the same call with a distinct voice.
- **MiniMax** synthesizes the human's instant briefing. When a person takes over, MiniMax turns the raw recalled turns into a crisp 5-field heads-up (calling about / appointment / insurance / mood / next step), grounded only in the memory.

## Who it's for

**Wedge:** SMB practices that live on the phone and churn front-desk staff — **dental, medical, vet, salons, law firms, home services.** Buyer: the office owner/manager. The pain (missed calls, re-explaining, blind handoffs) is acute and has budget today.

**Expansion:** the same memory layer is horizontal — any business where customers talk to an AI *and* a human, across phone, chat, and email.

## Why it's a company, not a feature

"Context on handoff" is a feature any one vendor can bolt on. **A portable memory layer that works across every channel, every agent, and every human — keyed to the customer, not the call — is infrastructure.** The defensible, hard problems we'd build the company on:

1. **Identity resolution** — stitching one memory across phone numbers, emails, and devices.
2. **Memory curation** — what to keep, summarize, decay, and how to resolve contradictions (the active frontier: mem0, Letta, Zep).
3. **Privacy & compliance** — consent and right-to-be-forgotten on persistent customer memory (and HIPAA for healthcare).
4. **Integrations** — being the memory that plugs into every channel and the practice-management system.

## Status / what's real

Working live demo: a spoken call to the AI front desk → grounded answers → an **audible in-call handoff to a care coordinator who already knows the caller's situation**, backed by a real cross-process Moss session. Memory persists per customer across calls.
