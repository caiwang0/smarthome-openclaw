# Product Research: AI-Powered Smart Home Hub

> **What we're building:** A Raspberry Pi-based smart home hub that makes every device in your home smart — even old ACs, fans, and TVs — through IR blasters and auto-discovery. Controlled via a simple web dashboard and AI chat (OpenClaw) in WhatsApp/Telegram. Runs locally, no cloud required.

---

## Table of Contents

1. [Executive Summary for Leadership](#1-executive-summary-for-leadership)
2. [What We're Building & How We Differentiate](#2-what-were-building--how-we-differentiate)
3. [Competitive Landscape](#3-competitive-landscape)
4. [Feature Comparison: What They Have vs. What We Have](#4-feature-comparison-what-they-have-vs-what-we-have)
5. [Pros and Cons](#5-pros-and-cons)
6. [Market Opportunity](#6-market-opportunity)
7. [User Pain Points We Solve](#7-user-pain-points-we-solve)
8. [Risks and Mitigations](#8-risks-and-mitigations)
9. [Recommended Strategy](#9-recommended-strategy)
10. [Refined Research Prompt for Next Steps](#10-refined-research-prompt-for-next-steps)
11. [Sources](#11-sources)

---

## 1. Executive Summary for Leadership

> **Use the "For the Onepager" section directly under "Why." The "Supporting Evidence" section is backup for Q&A.**

### For the Onepager (Why)

**1. 87% of homes still have "dumb" devices — we make them smart for $20/room.**

Most households have ACs, fans, and old TVs controlled by remotes. Replacing them with smart versions costs $800-2,000. We use a $20 IR blaster per room — auto-discovered and controlled through one dashboard alongside all their smart devices. No app juggling, no cloud, no subscription.

| Approach | Cost to make an AC "smart" |
|----------|---------------------------|
| Buy a new smart AC | $800-2,000 |
| Sensibo (AC only, subscription) | $119 + $2.49/mo |
| Tado (AC only, mandatory subscription) | $179 + $0.99/mo |
| SwitchBot Hub 2 (cloud-dependent) | $70 |
| **Our product (all devices, local, AI)** | **~$20/room + hub** |

**2. We build on Home Assistant's 2,000+ device integrations — the hard part is already done.**

Home Assistant (86k GitHub stars, 2M+ users) has 10+ years of community-built protocol support for virtually every smart device brand. We wrap it as an engine and add what it lacks: a simple UI that non-technical users can actually use, IR control for dumb devices, and AI chat for natural-language automation. The engineering challenge is making Home Assistant invisible to the end user — not rebuilding device support from scratch.

**3. Users control their home from WhatsApp — no app to install, no cloud required.**

Our AI (OpenClaw) lives in the messaging apps people already use — WhatsApp, Telegram, Discord. Say "turn off everything when I leave" and it creates the automation. Runs fully local: no cloud dependency, no data collection, no subscriptions. 57% of Americans are concerned about smart home data collection (Ring/Nest privacy scandals, EU AI Act) — we're the only solution that's fully private.

### Supporting Evidence (for Q&A)

**Market size:** The IR blaster hub market is $2.31B (2024) growing to $7.23B by 2033 (13.8% CAGR). The broader smart home market is $140-174B. 75% of AI app subscribers say they'd pay for smart home AI.

**Competitors are poorly serving this space:** Broadlink ($26) has the worst app in the category. SwitchBot ($70) requires cloud. Sensibo ($119) and Tado ($179) only control ACs and charge subscriptions for basic features — Tado's mandatory $0.99/mo paywall triggered a user backlash. No product combines: all-device IR control + smart device unification + AI automation + local processing + free core features. We do.

**Big tech AI is shipping but unreliable:** Alexa+ and Gemini for Home launched in 2025-2026, but early reviews report reliability regressions on basic commands (sources: XDA, Android Central). Their AI requires cloud, and neither offers "create a persistent automation rule from a natural-language description" — they execute commands, not build rules.

**Go-to-market:** We start with Home Assistant's 2M-user technical community to validate demand and refine the product, then expand to mainstream consumers via retail/Amazon/YouTube.

---

## 2. What We're Building & How We Differentiate

### Our Product

A plug-and-play smart home hub that:
1. **Auto-discovers** every smart device on your network (lights, cameras, speakers, plugs, TVs)
2. **Makes dumb devices smart** via $20 IR blasters in each room (AC, fan, old TV, projector)
3. **Unifies everything** in one simple web dashboard — no multiple apps
4. **AI chat control** — tell OpenClaw what you want via WhatsApp/Telegram ("turn off everything when I leave") and it creates the automation
5. **Runs fully local** — no cloud, no subscription, no data collection

### How We Differentiate (vs. every competitor)

| Differentiator | Why it matters | Who else does this? |
|---------------|----------------|-------------------|
| **All devices in one UI** (smart + dumb via IR) | Users currently need 3-5 apps to control everything | SwitchBot partially (their ecosystem only). Nobody does all devices + IR in one dashboard. |
| **AI chat via messaging apps** | Control your home from WhatsApp/Telegram — no new app to install | No commercial product offers turnkey chat-app home control for non-technical users. HA has raw Telegram/WhatsApp integrations but they require manual configuration. |
| **"Vibe" automations** | "Turn off everything when I leave" → AI creates the rule | Google/Amazon are working on this but haven't shipped it as "create persistent rule from description." HA has it but it's technical. |
| **Fully local, no cloud** | Privacy, reliability (no server = no outage), no subscription | Hubitat ($200, no AI). HA Green ($159, no simplified UI). Nobody else in the IR blaster space. |
| **No subscription for core features** | Tado charges $0.99/mo for basic controls. Sensibo charges $2.49/mo for useful features. All device control and IR features are free forever. AI premium features may have optional pricing (never mandatory). | Broadlink and SwitchBot don't charge subscriptions, but they require cloud. |
| **2,000+ device integrations** (inherited from HA) | Works with virtually every smart home brand | Home Assistant itself, and SwitchBot AI Hub (ships with HA Core). Our value-add: making these integrations accessible to non-technical users via simplified UI + AI. |

---

## 3. Competitive Landscape

### Tier 1: IR Blaster Products (Direct Competitors)

| Product | Price | Controls | Cloud Required | Subscription | AI | App Quality |
|---------|-------|----------|---------------|-------------|-----|------------|
| **SwitchBot Hub 2** | $70 | All IR + SwitchBot ecosystem | Yes (mostly) | None | None (AI Hub $260 has local AI) | Good |
| **SwitchBot AI Hub** | $260 | All IR + cameras + NVR | No (local AI) | Cloud AI optional | Local VLM, built-in HA | Good |
| **Broadlink RM4 Mini** | $26 | All IR | Yes | None | None | Poor |
| **Broadlink RM4 Pro** | $45 | IR + RF (433MHz) | Yes | None | None | Poor |
| **Tuya generics** | $10-18 | All IR | Yes (100% cloud) | None | None | Adequate |
| **Sensibo Air** | $119 | AC only | Yes | $2.49/mo for useful features | Climate React (paywalled) | Good (AC only) |
| **Aqara Hub M3** | $70 | IR + Zigbee + Matter | Partial (local capable) | None | None | Good |
| **Tado V3+** | $179 | AC only | Yes | $0.99/mo mandatory! | Predictive AI (paywalled) | Good (but trust destroyed) |

### How Competitors Work vs. How We Work

Every competitor's IR blaster is a **standalone WiFi puck** (~$20-70) that you plug into power. The puck connects to your WiFi and talks to the **manufacturer's cloud**, which talks to their phone app. We use the **same physical hardware** (e.g., a $20 Broadlink RM4 Mini) but replace their cloud and app with our local system.

```
Their architecture:

Phone App  →  Internet  →  Manufacturer Cloud  →  Internet  →  IR Blaster (WiFi)  →  AC/TV/Fan
                                  ☁️
                     (if internet goes down, everything stops)


Our architecture (two control paths):

1. Dashboard (local):   Browser  →  Raspberry Pi  →  IR Blaster (WiFi)  →  AC/TV/Fan
                                      🏠 local network only — no internet needed

2. AI Chat (internet):  WhatsApp/Telegram  →  Internet  →  Raspberry Pi  →  IR Blaster  →  AC/TV/Fan
                                                ☁️ messaging services need internet
```

| Scenario | Their system | Our system |
|----------|-------------|------------|
| WiFi + internet working | Everything works | Everything works (dashboard + AI chat) |
| **WiFi working, internet down** (ISP outage) | **Everything stops** — app can't reach their cloud, devices uncontrollable | **Dashboard still works** — control all devices from local browser. AI chat unavailable (WhatsApp/Telegram need internet). |
| WiFi router down | Both dead | Both dead |

**Key advantage:** During an ISP outage, their devices become completely uncontrollable — you can't even turn off your AC. Ours still gives you full device control via the local dashboard. The AI chat is an internet feature, but the core device control never depends on anyone's cloud server.

**We don't build or sell an IR blaster.** Users buy a commodity $20 Broadlink RM4 Mini, plug it in, and Home Assistant auto-discovers it. No Broadlink app needed. Our value is the software layer — the dashboard, the AI, and the local control — not the hardware puck.

### Competitor Business Model Summary

| Company | Core Product | Controls | Subscription | Business Model |
|---------|-------------|----------|-------------|----------------|
| **Broadlink** | IR blaster puck | Everything with a remote | None | Cheap hardware, one-time sale. Terrible app is the tradeoff. |
| **SwitchBot** | Smart home hub + ecosystem | IR devices + own accessories | None for core, optional cloud AI | Ecosystem lock-in — hub is the gateway to buying more SwitchBot products |
| **Sensibo** | AC-only IR controller | ACs only | $2.49/mo for useful features | Hardware + subscription upsell. Paywalls geo-fencing, auto-off, energy reports. |
| **Tado** | AC-only IR controller | ACs only | $0.99/mo mandatory for basic app | Hardware + mandatory subscription. Previously free features paywalled in Feb 2025 — massive user backlash. |
| **Us** | Software layer on Raspberry Pi | Everything (smart + dumb via IR) | None for core; optional AI premium | Software product. Users bring their own IR blasters ($20 commodity hardware). Our revenue is the hub/software, not the puck. |

**The gap we exploit:** Broadlink controls everything but has a terrible app and requires cloud. SwitchBot has a good app but locks you into their ecosystem and requires cloud. Sensibo and Tado have good apps but only do ACs and charge subscriptions. Nobody offers: all-device control + good UX + local processing + AI + no mandatory subscription.

### Tier 2: Smart Home Hubs (Indirect Competitors)

| Product | Price | IR Control | AI | Local | Subscription |
|---------|-------|-----------|-----|-------|-------------|
| **Amazon Echo + Alexa+** | $50-250 | Via SwitchBot/Broadlink skill (cloud-to-cloud, 1-3s latency) | Alexa+ (strong, agentic) | No | Free w/Prime, $20/mo otherwise |
| **Google Home + Gemini** | $99 | Via Matter IR bridge | Gemini (strong, natural language) | Partial | Free |
| **Apple Home** | $99-299 | Via Matter IR bridge | Siri AI (delayed to Fall 2026) | Yes (on-device) | Free |
| **Samsung SmartThings** | $120 | No native IR | Galaxy AI (moderate) | Partial | Free |
| **Hubitat C-8 Pro** | $200 | No | Minimal | Full | None |
| **Home Assistant Green** | $159 | Via Broadlink integration | Built-in (400+ LLMs) | Full | $6.50/mo cloud optional |
| **Homey Pro 2026** | $399 | Built-in IR | Moderate | Full | None |

### Key Competitor: SwitchBot AI Hub ($260)

This is our most direct competitor, launched Feb 2026:
- Local AI processing with vision language model
- Built-in Home Assistant Core (limited version, not full HA OS)
- Built-in Frigate NVR for cameras (up to 8 cameras, 32GB expandable to 16TB)
- IR blaster + Matter bridge
- OpenClaw compatibility (via built-in HA Core — not a native integration; users would need to configure it themselves, same as any HA add-on)

**Our advantage over SwitchBot AI Hub:**
- **Price** — targeting competitive pricing vs $260 (BOM needs validation — see Risks section)
- **Turnkey chat-app control** — WhatsApp/Telegram integration works out of the box; SwitchBot users would need to self-configure OpenClaw through HA
- **Full Home Assistant** (not just Core) — full add-on ecosystem, full automation engine
- **Open/extensible** — not locked into SwitchBot's ecosystem
- **User-created AI skills** — extend what the AI can do from the web app

**Their advantage over us:**
- Shipping now with established brand and retail distribution
- Integrated camera NVR (security cameras are often the #1 reason people enter the smart home space)
- Polished, purpose-built hardware with dedicated NPU
- Larger IR device database (80,000+ devices)

---

## 4. Feature Comparison: What They Have vs. What We Have

### What competitors have that we DON'T have (gaps to address)

| Feature | Who has it | Priority for us |
|---------|-----------|----------------|
| **Retail distribution** (buy at Target/Amazon) | SwitchBot, Amazon, Google | Critical — we can't reach non-technical users without this |
| **Polished mobile app** | SwitchBot, Sensibo, Google, Apple | High — our web app works on mobile but isn't a native app |
| **Built-in camera NVR** | SwitchBot AI Hub | Medium — could add via Frigate integration |
| **Voice speaker built-in** | Amazon Echo, Google Home, Apple HomePod | Low — we can integrate with existing speakers |
| **RF control (433MHz)** | Broadlink RM4 Pro | Low — IR covers most use cases |
| **Thread/Zigbee radio built-in** | SwitchBot AI Hub, SmartThings, HA Yellow (discontinued) | Medium — requires USB dongle for now |
| **Established brand trust** | All major competitors | Critical — we're unknown |
| **Massive IR device database** | SwitchBot (80K+), Broadlink (50K+) | We inherit HA's database + blaster learning mode |

### What WE have that competitors DON'T have

| Feature | Why it matters | Closest competitor |
|---------|---------------|-------------------|
| **AI chat via WhatsApp/Telegram/Discord** | Control home from apps you already use. No new app needed. | Nobody does this. |
| **"Vibe" automations from natural language** | "When I leave, turn off everything" → AI creates persistent rule | Google/Amazon do voice commands but not persistent rule creation from description |
| **Fully local AI + control, no cloud** | Privacy, reliability, no outage risk | SwitchBot AI Hub is local but costs $260 and is ecosystem-locked |
| **All devices unified (smart + IR) in one dashboard** | No app juggling — one place for everything | SwitchBot (their ecosystem only), Homey ($399) |
| **2,000+ device integrations** | Works with virtually everything | Only raw Home Assistant |
| **No subscription for core features** | Tado/Sensibo paywall basic device controls. All our device control + IR features are free forever. Optional premium for advanced AI. | Broadlink (no sub, but terrible app). Hubitat (no sub, but no AI). |
| **User-created AI skills** | Extend what the AI can do from the web app | Nobody in the consumer space |
| **Open, extensible platform** | Not locked into one company's ecosystem | Home Assistant (but harder to use). Hubitat (but no AI). |

---

## 5. Pros and Cons

### Pros (Reasons to build)

| # | Pro | Strength |
|---|-----|----------|
| 1 | **Solves a problem big tech doesn't** — making dumb devices smart with a good UX | Strong |
| 2 | **IR blaster market ($2.3B) is poorly served** — best app (SwitchBot) is cloud-dependent, cheapest option (Broadlink) has terrible UX | Strong |
| 3 | **Privacy-first is a growing advantage** — 57% of Americans concerned about data collection, EU regulations tightening | Strong |
| 4 | **Chat-app control is genuinely novel** — WhatsApp/Telegram interface, no competitor offers this | Strong |
| 5 | **Retrofit economics are compelling** — $20/room vs $800-2,000 for replacement | Strong |
| 6 | **Leverage 10+ years of Home Assistant** — 2,000+ integrations, 2M+ users, skip protocol work | Strong |
| 7 | **No subscription for core features** — competitors are paywalling basic controls (Tado backlash). All device control is free; only advanced AI features may have optional premium pricing | Moderate |
| 8 | **AI timing window** — big tech AI home features are shipping but unreliable, 12-18 month window | Moderate |
| 9 | **Phased approach** — can ship IR + dashboard MVP in 2-3 months and validate before heavy investment | Moderate |

### Cons (Risks and challenges)

| # | Con | Severity |
|---|-----|----------|
| 1 | **SwitchBot AI Hub ($260) already exists** — local AI, built-in HA, IR, Matter, shipping now | High |
| 2 | **Raspberry Pi supply chain risk** — DRAM crisis caused 42-71% price increases, HA Yellow died from this exact problem | High |
| 3 | **Target user ≠ delivery mechanism** — non-technical homeowners don't buy Pi products, they buy at retail | High |
| 4 | **Support burden is expensive** — estimated 7-17% of revenue, smart home products have above-average support costs | High |
| 5 | **Home Assistant is improving its own UX** — new dashboards, AI features, voice control all on their 2025-2026 roadmap | Medium |
| 6 | **OpenClaw is a third-party dependency** — community-driven, single creator, risk of abandonment | Medium |
| 7 | **Small team (2-5) vs massive scope** — 4 phases, 20+ features, hardware + software + AI | Medium |
| 8 | **No brand recognition** — competing against established names (SwitchBot, Broadlink, Google, Amazon) | Medium |
| 9 | **Google/Amazon will eventually add "create automation from description"** — differentiation window is limited | Medium |
| 10 | **$300-500K capital needed** for hardware path to break-even | Medium |

---

## 6. Market Opportunity

### The Retrofit Market

| Metric | Value |
|--------|-------|
| Global households with non-smart appliances | **~87%** (smart appliance penetration is only 12.9%) |
| AC units installed globally | **~2 billion**, vast majority non-smart, IR-controlled |
| IR blaster hub market (2024) | **$2.31B**, growing to $7.23B by 2033 (13.8% CAGR) |
| Cost to replace a dumb AC with smart | $800-2,000 |
| Cost to retrofit with IR blaster | $15-70 |
| US households with no smart appliances | ~62% |
| AC units projected by 2050 | **Triple** current installed base (IEA) |

### The Smart Home Hub Market

| Metric | Value |
|--------|-------|
| Global smart home market (2025) | $140-174B |
| AI in smart home (2025) | $15.7-20.5B, growing to $58.9-75.2B by 2029-2033 |
| US smart device ownership | 77.6% own at least one |
| Willingness to pay for AI home features | 75% of AI app subscribers would pay |
| Privacy concern driving purchase decisions | 57% of Americans concerned about data collection |

### Who Buys This?

**Primary:** Homeowners with a mix of smart and dumb devices who are frustrated by app juggling and want one unified control point. They've tried Alexa/Google but their AC and ceiling fan still need separate remotes.

**Secondary:** Privacy-conscious users who want smart home features without cloud dependency or data harvesting.

**B2B opportunity:** Airbnb hosts managing multiple properties (consistent automation across units), property managers (bulk deployment), smart home installers (white-label our software).

### How Big Is the "App Juggling + Dumb Devices" Problem?

| Metric | Number | Source |
|--------|--------|--------|
| Smart home users juggling multiple apps | 45% use individual apps as primary control; avg 5-10 apps per household | Deloitte, Portworld |
| NOT on a single ecosystem | ~69% use multiple platforms | Deloitte |
| Homes with smart + non-smart devices | Est. 70-80%+ (90% have non-smart AC, 81% of fans are conventional, 63-93% own a smart device) | Grand View Research, Straits Research, AHS |
| Speaker owners with uncontrollable dumb devices | 73% own a smart speaker, but no smart device category exceeds 30% penetration — huge gap between what the speaker can control and what they own | AHS, Deloitte |
| Frustrated at least once/week | 1 in 3 Americans | Digital Information World |
| Say they spend MORE time managing smart home | 29% | AHS |
| Average remote controls per home | 4 | Consumer Electronics Association |
| Installed AC units that are non-smart | 85-90% | Grand View Research |
| Tried smart home setup and gave up / returned | 22% gave up; 36% of returns are setup-related | Accenture, Parks Associates |

**Bottom line:** The primary target audience — homeowners with mixed smart/dumb devices frustrated by app juggling — is not a niche. It's the majority of smart home households.

---

## 7. User Pain Points We Solve

### Pain points from Reddit, Amazon reviews, and community forums

| Pain Point | Frequency | How we solve it |
|------------|-----------|----------------|
| **"I need 5 different apps to control my home"** | #1 complaint | One dashboard for everything — smart devices auto-discovered, dumb devices via IR |
| **"My AC/fan/old TV isn't smart"** | Very common | $20 IR blaster per room, auto-discovered, controlled from dashboard and AI chat |
| **"Cloud went down and my devices stopped working"** | Common (Google Nest had major outage in early 2025) | Fully local — no cloud dependency, works even if internet is out |
| **"Setting up automations is too complicated"** | Common | AI chat: "Turn off everything when I leave" → done |
| **"I'm worried about privacy/data collection"** | 57% of Americans | No cloud, no data collection, runs on your hardware |
| **"Subscriptions for basic features are unacceptable"** | Growing (Tado backlash) | All device control features free forever. Optional premium only for advanced AI. |
| **"Home Assistant is too complicated"** | #1 HA complaint | We wrap HA's power in a simple dashboard — users never see YAML or HA's complex UI |
| **"My family can't use the smart home when it breaks"** | Common ("wife test") | Simple, resilient dashboard that non-technical household members can use |

### Competitor-Specific Pain Points We Exploit

| Competitor | Their biggest complaint | Our answer |
|------------|----------------------|------------|
| **Broadlink** | "App is terrible, multiple confusing apps, takes 2+ hours to set up" | Clean dashboard, auto-discovery, no setup pain |
| **SwitchBot** | "Matter/HomeKit 'No Response' errors, cloud-dependent" | Fully local, no cloud dependency |
| **Sensibo** | "Core features locked behind paywall — like buying a fridge and paying to use the freezer" | All device control free. No paywalled basics. |
| **Tado** | "Mandatory $0.99/mo subscription for basic app controls — predatory practices" | Device control is always free. Period. |
| **Tuya** | "100% cloud dependent, cheap build quality fails within months" | Local processing, quality hardware |
| **Google Home** | "Gemini broke basic commands that used to work" | Local AI, reliable deterministic controls + AI layer on top |
| **Alexa** | "Double cloud hop (Alexa cloud → manufacturer cloud) = 1-3s latency for IR" | Direct local IR control, near-instant response |
| **Home Assistant** | "YAML is intimidating, dashboard creation takes hours, not wife-friendly" | Simple UI built on top of HA — users never touch YAML |

---

## 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Pi supply chain / DRAM crisis** | High | Consider software-only path first (Option D/A). Explore custom SBC or partner hardware. Don't commit to hardware until demand is validated. |
| **SwitchBot AI Hub is already shipping** | High | Differentiate on: price ($149 vs $260), chat-app interface (they don't have), no ecosystem lock-in, open platform. Position as "SwitchBot AI Hub but open and cheaper." |
| **Reaching non-technical consumers** | High | Start with HA's 2M technical users as beachhead. Use them to validate, then expand to consumer market via retail/Amazon/YouTube marketing. |
| **HA improves its own UX** | Medium | Our value isn't just "better HA UI" — it's IR control + AI chat + privacy + simplicity as a package. HA improving its UI actually helps us (better engine). |
| **OpenClaw dependency** | Medium | OpenClaw is open-source and forkable. Contingency: direct LLM API integration (Claude/GPT → HA REST API). Test OpenClaw reliability before committing. |
| **Support costs eating margins** | Medium | Invest heavily in self-service (docs, video tutorials, community forum). Self-service deflects 40-60% of tickets and costs $0.50-2.37 per resolution vs $28-35 per ticket. |
| **Google/Amazon ship "create automation from description"** | Medium | Our moat isn't just AI automation — it's local + private + no subscription + chat-app interface + IR control as a package. No single competitor offers all of these. |
| **Capital requirements ($300-500K for hardware)** | Medium | Start software-only ($5-10K for Option D) to validate demand. Only invest in hardware after proven traction. |

---

## 9. Recommended Strategy

### Phase the risk — don't bet everything on hardware upfront

```
VALIDATE FIRST (Weeks 1-8)
├── Week 1-2: Build working demo (Pi + HA + Broadlink RM4 + dashboard controlling AC/fan)
├── Week 2-4: Film demo video, create landing page, test demand
├── Week 4-6: Build Option D (AI chat layer — OpenClaw + HA + IR control via WhatsApp)
└── Week 6-8: Launch to HA's 2M-user community as technical beachhead

IF VALIDATED (Month 3-6)
├── Build full dashboard as HA add-on (Option A)
├── All device control features free (no subscription for core)
└── Test optional AI premium pricing ($8/mo for advanced AI automations, or $99 one-time)

IF STRONG TRACTION (Month 6-12)
├── Explore hardware partnership (Option C) — don't build your own hardware yet
├── Expand marketing to non-technical consumers (YouTube, TikTok, Amazon)
└── Consider Airbnb host / property manager B2B angle

IF HARDWARE DEMAND PROVEN (Month 12+)
├── Consider own hardware (custom SBC, not Pi — learn from HA Yellow's failure)
└── Or continue software-only with partner hardware
```

### Go/No-Go Criteria

**GO** (need 4 of 6):
- 500+ landing page signups in 30 days
- 30%+ of interviewees willing to pay $8+/mo
- Average 7+/10 on "describe a rule in English" value question
- OpenClaw reliably executes 8/10 common HA commands via chat
- Google/Amazon haven't shipped "create persistent automation from description"
- Team has frontend, backend, and AI/ML skills covered

**NO-GO** (any one is a stop):
- <100 signups in 30 days
- <10% willing to pay anything
- OpenClaw fails >50% of common commands
- HA announces native AI chat dashboard shipping in 2026

---

## 10. Refined Research Prompt for Next Steps

> **Phase 2 Research: Validate before building**
>
> 1. **Customer discovery (10 interviews minimum)**
>    - Recruit homeowners with 3+ devices including at least one "dumb" device (AC, fan, old TV)
>    - Key questions:
>      - How many remote controls do you have? How annoying is that?
>      - Would you pay $20/room to make your AC/fan controllable from your phone?
>      - If you could text "turn off everything when I leave" to a WhatsApp contact and have it just work, how valuable is that? (1-10)
>      - Would you pay $150 for a box that unifies everything? What about $8/month for optional AI features on top?
>      - What do you currently use to control your AC/fan? What do you hate about it? What would make you switch?
>      - Show demo video. First reaction?
>
> 2. **Smoke test demand**
>    - Landing page: "Make every device in your home smart — even the dumb ones"
>    - Drive traffic via Reddit, Facebook smart home groups, YouTube smart home channels
>    - Target: 500+ signups in 30 days
>
> 3. **OpenClaw technical assessment**
>    - Can it reliably control IR devices via HA?
>    - Test 10 common commands via WhatsApp
>    - Latency measurement (local vs cloud)
>    - Contingency: how hard to replace with direct LLM → HA API?
>
> 4. **SwitchBot AI Hub deep-dive**
>    - Buy one. Test it. Where does it fall short?
>    - Read Amazon reviews — what do users complain about?
>    - Identify gaps we can exploit
>
> 5. **Distribution channel research**
>    - Amazon marketplace economics for smart home hardware
>    - YouTube smart home influencer partnerships (cost, ROI)
>    - Smart home installer partnerships — would they white-label?
>
> 6. **Competitive timeline monitoring**
>    - Track Google "create automation from description" announcements
>    - Track HA AI dashboard roadmap
>    - Track SwitchBot AI Hub v2 / price drops

---

## 11. Sources

### IR Blaster Competitors
- SwitchBot Hub 2, Hub Mini, AI Hub — [us.switch-bot.com](https://us.switch-bot.com)
- SwitchBot AI Hub review — NotebookCheck (Feb 2026), The Gadgeteer (Feb 2026)
- SwitchBot Hub 2 review — TechHive, AppleInsider
- Broadlink RM4 Mini/Pro — Amazon listings, HA Community forums
- Broadlink RM MAX Matter announcement — HomekitNews (Jan 2026), IoT Insider
- Broadlink Home Assistant integration — home-assistant.io/integrations/broadlink
- Tuya IR blasters — Amazon, SmartHomeScene (ZS06 review)
- Sensibo Air/Air Pro — sensibo.com, TechHive review, Trustpilot reviews, Tom's Guide
- Tado V3+ — tado.com, Matter Alpha (subscription controversy), TechRadar, Consumer Rights Wiki
- Matter-compatible IR bridges — MatterAlpha comparison
- Consumer Reports — Best Smart AC Controllers 2026

### Smart Home Hubs
- Google Gemini for Home — blog.google (Fall 2025 / Spring 2026)
- Amazon Alexa+ — CNBC (Feb 2026), aboutamazon.com
- Apple Home delays — MacRumors (Nov 2025), Bloomberg (March 2026)
- Samsung SmartThings — Android Central, Samsung CES 2026
- Hubitat C-8 Pro — Amazon
- Home Assistant — home-assistant.io (2M installs April 2025, AI blog Sept 2025, Voice Chapter 10, Roadmap 2025)
- Nabu Casa — nabucasa.com (Green pricing, Yellow EOL Oct 2025)
- Homey Pro 2026 — Z-Wave Alliance
- Josh.ai — josh.ai (2025 year in review)

### Market Data
- IR Blaster Hub Market ($2.31B) — Growth Market Reports
- IR Blaster Matter Bridge Market — Dataintelo
- Smart Home Market ($147.52B) — Fortune Business Insights
- AI in Smart Home — GlobeNewsWire 2025, InsightAce Analytic, FutureDataStats
- Smart appliance penetration (12.9%) — Statista
- AC market / IEA projections — IEA Commentary
- US adoption / consumer sentiment — AHS Survey 2024, LightNOW 2025, NIQ 2025

### User Pain Points
- Reddit: r/homeautomation, r/smarthome, r/homeassistant
- HA Community forums — "Thinking of dropping HA", "Why are things so difficult?"
- HomeSeer forums — "Has anyone found HA confusing?"
- How-To Geek — "Home Assistant's biggest weaknesses"
- XDA — "Alexa+ and Google Home AI didn't revolutionize anything in 2025, but Home Assistant did"
- S3 Europe — Smart Home Chaos: Reddit Insights
- Tado subscription backlash — Matter Alpha, TechRadar, Rossmann Group Wiki

### Licensing & Hardware
- Home Assistant Apache 2.0 license — home-assistant.io/developers/license
- Open Home Foundation brand assets — GitHub
- Raspberry Pi pricing / DRAM crisis — raspberrypi.com, Tom's Hardware, NotebookCheck, TechEduByte
- FCC certification — compliancetesting.com, sunfiretesting.com, emcfastpass.com
- EU RED cybersecurity requirements — metlabs.com
- Support cost benchmarks — MatrixFlows, LiveChatAI, Extend
