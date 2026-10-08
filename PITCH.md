# 🎤 ScamShield — Pitch Playbook

> **Tagline options** (pick one and use it everywhere):
> 1. *"An immune system for your inbox."*
> 2. *"Think fast. Then think hard. Then ask a human."*
> 3. *"The scam filter that shows its work."*

**Recommended:** "An immune system for your inbox" as the headline, "Think fast. Think hard. Ask a human." as the sub-line.

---

## 1. Why this pitch is different

Most teams will show: *message in → LLM says "scam" → done.* Judges will see that five times today. ScamShield wins on **five things they won't see elsewhere**:

| # | Differentiator | One-line proof for judges |
|---|---|---|
| 1 | **Two speeds of thinking** | Instant reflex (Jev) tags in ~0.4 s; deep ADK investigation runs only where needed |
| 2 | **Explainable by construction** | Every flag cites the tool that found it. No black box |
| 3 | **Consent by design** | The agent can't delete or block anything. It proposes; a human approves; the audit log proves it |
| 4 | **Never down, never leaking** | Gemini → OpenRouter → local model → rules, plus a **privacy mode** where nothing leaves the laptop |
| 5 | **Operator-grade control** | A Control Center where you watch the agents think, override providers, dial autonomy, and run a red-team scoreboard live |

The emotional hook is simple: **"Everyone here has a parent or grandparent who got a 'KYC expired' message."**

## 2. The story arc (4 minutes)

| Time | Beat | What you say / show |
|---|---|---|
| 0:00 | **Hook** | Ask: "Who here has a family member who got a fake bank or courier message?" Hands up. "They had seconds to decide, and nothing to help them." |
| 0:20 | **Insight** | "Spam filters are black boxes: they block or miss, and never explain. And agents are about to read our messages and act for us, so *consent and evidence* matter more than ever." |
| 0:40 | **Solution** | One slide: the immune-system diagram (reflex → investigation → memory → human consent) |
| 1:00 | **Live demo, act 1: Reflex** | Open Gmail. A scam email already carries **"Don't open"**. "That decision took under a second." |
| 1:20 | **Act 2: Investigation** | Switch to the Control Center's live pipeline. Four investigators light up in parallel, then the verdict, with an evidence trail: new domain, brand lookalike, double-extension attachment. Read the Tamil explanation aloud |
| 1:50 | **Act 3: Consent** | Show the proposed quarantine. Click Approve. Show the audit log. "The agent never held the delete button" |
| 2:10 | **Act 4: Resilience (wow #1)** | Click **Simulate outage** on Gemini Pro. Re-run. The provider badge flips to the fallback and the answer still arrives. "The shield doesn't go down because an API did" |
| 2:30 | **Act 5: Privacy (wow #2)** | Toggle 🔒 **Privacy mode**. Re-run. "Local model only. No message leaves this laptop" |
| 2:50 | **Act 6: Red team (wow #3)** | Run the lab: 20 synthetic scams and legit messages. The scoreboard fills: catch rate, false positives, time per verdict. "We don't claim it works. We measure it, live" |
| 3:20 | **Autonomy dial** | Slide Observe → Ask → Auto-low-risk. "Families choose how much to trust it. Default is: ask" |
| 3:35 | **Impact + roadmap** | Android notification guard, real reputation feeds, family guardian mode, voice-call scams |
| 3:50 | **Close** | "Scammers need us to act fast. ScamShield acts faster. Then it asks a human." |

## 3. Slide outline (8 slides, or fewer)

1. **Title** — name, tagline, team
2. **The problem** — one scam message, three seconds to decide (use a fictional example)
3. **Why filters fail** — black box, no explanation, no consent
4. **The immune system** — architecture diagram (reflex / investigation / memory / consent)
5. **Live demo** (full-screen switch)
6. **Trust & resilience** — evidence trail, human approval, fallback chain, privacy mode
7. **Measured results** — *your* real numbers from the lab (catch rate, false positives, reflex vs deep latency, failovers survived)
8. **Roadmap + ask** — Android guard, real feeds, family guardian; thank you

## 4. Demo choreography checklist

- [ ] Backend runs **on the laptop** (local Ollama available); Cloud Run URL ready as backup
- [ ] Test Gmail account pre-loaded with 3 scam emails and 2 legitimate ones
- [ ] Sample messages loaded in the simulator (Tamil courier scam, UPI refund, digital arrest)
- [ ] Cache **cleared** before the live run (so the pipeline visibly runs), and one pre-warmed message ready for the "instant repeat" moment
- [ ] "Simulate outage" and "Privacy mode" buttons rehearsed
- [ ] Red-team lab batch size small enough to finish in about 30 seconds
- [ ] Browser zoom, dark theme, and font size readable from the back of the room
- [ ] **Backup screen recording** of the full flow saved locally
- [ ] Phone hotspot ready if venue Wi-Fi fails (Ollama path still works offline)

## 5. Numbers to show (measure them, don't invent them)

| Metric | Where it comes from |
|---|---|
| Catch rate and false-positive rate | Red-team lab on the sample set |
| Reflex latency vs deep-verdict latency | SSE event timestamps |
| Cache hit rate | `/control/state` |
| Failovers survived | Router log |
| Deep investigations avoided by the gate | Gate counters |

If a number isn't measured, don't put it on a slide.

## 6. Judge Q&A cheat sheet

**What if the reflex model is wrong?**
It is only a gate. A low score never silences a message that other signals flag, and a high score only adds a warning tag. Quarantine always needs approval (or the dial set to auto for reversible, low-risk cases). We show confidence, not certainty.

**How do you avoid false positives?**
We test legitimate messages in the same lab batch and report the false-positive rate. Evidence is shown for every flag, so users can overrule it. Rejections can feed the sender allow-list.

**Why not just ask one big LLM?**
Cost, latency and rate limits. The reflex layer handles every message cheaply; the heavy investigation runs only where needed. And a single LLM gives you a verdict, not an evidence trail you can audit.

**What about privacy? You're reading messages.**
Personal data is redacted before any model call, we store only the incident record, and privacy mode runs entirely on-device. The roadmap includes an on-device first pass.

**What if Gemini goes down or we hit limits?**
The router fails over to OpenRouter, then a local model, then a rules scorer. We can demonstrate it live.

**Is the intelligence real or scripted?**
Reputation sources are mock, as the problem statement specifies. The investigation logic, routing, reasoning and approval flow are real, and the lab shows it handling messages it has never seen.

**Can this be abused to generate scams?**
The lab generates clearly labelled synthetic test messages from fictional brands and non-resolving domains, only to evaluate the shield.

**WhatsApp doesn't allow this, right?**
Correct for production. The prototype uses WhatsApp Web with a test chat and a simulator. The real route is Android's consented notification access, which is on our roadmap.

**How would this scale or make money?**
Free for individuals via browser and Android; paid family and small-business plans (shared incident dashboards, admin controls), and a B2B API for banks and telecoms that want explainable scam signals.

**What did you build in 6 hours versus what's planned?**
Be honest and specific: show the built flow, name what is mocked, and list the roadmap. Judges reward clarity.

## 7. Don'ts

- Don't say "100% accurate" or "can't be fooled".
- Don't demo with real personal accounts, messages, or real brand-impersonating live links.
- Don't narrate architecture for more than 40 seconds before showing something running.
- Don't depend on Wi-Fi, Jev, or any single API for the demo path.
- Don't add a feature in the last hour. Rehearse instead.

## 8. One-paragraph elevator pitch

> ScamShield is an immune system for your inbox. A fast reflex layer flags suspicious messages in under a second, a team of AI investigators then examines the sender, links and attachments, and every verdict comes with an evidence trail in the user's own language. The agent can propose, but only a human can approve, so nothing is ever deleted without consent. It keeps working when cloud APIs fail, and in privacy mode it never sends a message off the device. We built a Control Center so anyone can watch it think, tune its autonomy, and measure how well it works.
