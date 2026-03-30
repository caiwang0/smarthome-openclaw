# SmartHub Market Research — Skill Prompts

Run these in order. Each builds on the previous.

---

## 1. `/find-community`

```
I'm building SmartHub — an AI-powered smart home hub running on a Raspberry Pi. It wraps Home Assistant in a simple web dashboard and adds an AI chat assistant (OpenClaw) that lets users control devices and create automations via natural language.

The product auto-discovers every smart device on your network, and in Phase 3, uses $20 IR blasters to make "dumb" devices (ACs, fans, old TVs) controllable too. Runs fully local — no cloud, no subscription, no data collection.

I'm already part of several communities:
- Home Assistant users (2M+ installs, very active Reddit/Discord/forums)
- Smart home enthusiasts (r/homeautomation, r/smarthome)
- Raspberry Pi tinkerers
- Privacy-conscious tech users
- Renters/homeowners frustrated with app juggling (5-10 apps per household)
- People in hot climates where AC control matters (Southeast Asia, Middle East)

Help me identify which 1-3 communities to focus on first, evaluate each using the framework, and identify the specific persistent problems I can solve for them.
```

---

## 2. `/validate-idea`

```
I'm building SmartHub — a Raspberry Pi smart home hub that:
1. Auto-discovers all smart devices via Home Assistant
2. Shows them in a simple web dashboard (no YAML, no technical UI)
3. Adds AI chat (OpenClaw) — "turn off everything when I leave" creates an automation
4. Makes dumb devices smart via $20 IR blasters (Phase 3)
5. Runs fully local — no cloud, no subscription

The target user is homeowners with a mix of smart and dumb devices who are frustrated by:
- Juggling 5-10 apps (69% aren't on a single platform)
- Dumb devices (ACs, fans) that can't be controlled from their phone
- Setup difficulty (36% of smart home returns are setup-related, 22% give up entirely)
- Privacy concerns (57% of Americans worried about data collection)
- Subscription creep (Tado now charges $0.99/mo just to open their app)

Competitors:
- SwitchBot AI Hub ($260) — local AI, but ecosystem-locked, just launched
- Broadlink RM4 Mini ($26) — cheapest IR, but terrible app, cloud-required
- Sensibo ($119) — AC only, $2.49/mo subscription for useful features
- Tado ($179) — AC only, mandatory $0.99/mo subscription, massive user backlash
- Home Assistant directly — powerful but too complex for non-technical users

Market: IR blaster hub market is $2.3B (2024) → $7.2B by 2033. 87% of homes still have non-smart appliances. 85-90% of installed ACs are non-smart.

I have a working prototype: HA + Elysia API + React dashboard + OpenClaw chat, all running in Docker on a Pi. I've been using it to control my own Xiaomi TV and other devices.

Validate this idea using the minimalist entrepreneur framework. Be honest about red and green flags.
```

---

## 3. `/mvp`

```
Based on my validated idea for SmartHub (AI smart home hub on Raspberry Pi), I need to define my MVP scope.

What I've already built (Phase 1):
- Home Assistant running in Docker on a Pi
- Bun/Elysia API that aggregates HA device/entity/area registries via WebSocket
- React dashboard with device cards (lights, switches, climate, cameras, sensors, media players)
- Area/room filtering, real-time status polling, new device notifications
- OpenClaw AI chat sidebar that streams responses via SSE proxy

What's planned but NOT built:
- Phase 2: "Vibe" automations from natural language, visual automation builder, AI notifications, skill builder
- Phase 3: IR blaster control, IR remote learning, Zigbee/Z-Wave support

The research doc suggests this strategy:
- Weeks 1-2: Working demo (Pi + HA + Broadlink RM4 + dashboard controlling AC/fan)
- Weeks 2-4: Demo video, landing page, test demand
- Weeks 4-6: AI chat layer (OpenClaw + HA + IR control via WhatsApp)
- Weeks 6-8: Launch to HA's 2M-user community

Help me ruthlessly cut scope. What's the ONE thing my MVP does? What can I ship this weekend to start getting feedback? What should I charge?
```

---

## 4. `/processize`

```
My product idea: SmartHub — a smart home hub that makes every device controllable from one dashboard + AI chat. Currently it's a software stack (HA + API + Dashboard + AI) running on a Raspberry Pi.

Before I try to sell a polished product, how would I deliver this value manually?

Some context:
- The core value is: "control all your devices from one place, even dumb ones, with AI"
- The technical stack already works for MY house
- Setting up another person's house requires: installing HA, discovering their devices, configuring integrations, possibly IR blaster setup
- The AI chat already works for basic device control

Who are the first 3-10 people I should deliver this to by hand? How would the manual process work — do I go to their house and set it up? Do I do it remotely? What's the "magic piece of paper" for this?
```

---

## 5. `/first-customers`

```
I have a working SmartHub prototype — AI-powered smart home dashboard on a Raspberry Pi. It auto-discovers devices, shows them in a clean web UI, and has an AI chat for natural language control.

I need my first 100 customers. Context:
- I'm active in the Home Assistant community
- The product is currently software-only (runs on user's own Pi)
- SwitchBot AI Hub ($260) is the closest competitor, just launched
- My advantage: open platform, no ecosystem lock-in, AI chat via messaging apps, fully local
- I'm based in Southeast Asia (Malaysia)

Help me build my concentric circles strategy:
1. Who are my first 10 friends/family to pitch?
2. Who are my first 10 community members?
3. What does a cold outreach message look like for someone in r/homeassistant who's complaining about HA's complexity?
4. What should I charge initially?
5. How do I track progress?
```

---

## 6. `/pricing`

```
SmartHub pricing decision:

Product: AI smart home hub software that runs on a Raspberry Pi
- Phase 1 (now): Dashboard + device control + AI chat — software only, user provides their own Pi
- Phase 3 (future): + IR blaster support for dumb devices
- Potential hardware bundle (future): Pre-configured Pi + IR blaster(s)

Costs per customer:
- Software: Near-zero marginal cost (open source stack, user's own hardware)
- AI: Claude API costs if using cloud AI (~$0.01-0.10 per conversation), or zero if user has their own Claude Code auth
- Support: High for smart home products (7-17% of revenue industry average)

Competitor pricing:
- SwitchBot AI Hub: $260 one-time (hardware)
- Broadlink RM4 Mini: $26 one-time (hardware, bad app)
- Sensibo: $119 + $2.49/mo
- Tado: $179 + $0.99/mo mandatory
- Home Assistant Cloud: $6.50/mo optional
- Hubitat: $200 one-time

My research suggests: "All device control features free forever. Optional premium for advanced AI features."

Help me figure out: what's my pricing model? What do I charge from day one? How do I structure tiers? What's the path to financial independence?
```

---

## 7. `/marketing-plan`

```
I'm building SmartHub — an AI smart home hub. Assuming I hit ~100 customers from the HA community, I need a marketing plan to scale.

My strengths:
- Building in public (code is on GitHub, iterating with real hardware)
- Deep technical content (can explain HA internals, AI integration, IR control)
- Strong before/after story ($20/room vs $800 replacement)
- Privacy angle (fully local, no cloud, no data collection)
- Real competitor pain points to address (Tado subscription backlash, Broadlink terrible app)

Platforms I'm considering:
- YouTube (smart home content is huge — channels like EverythingSmartHome, BeardedTinker)
- Reddit (r/homeassistant, r/smarthome, r/homeautomation — already active)
- Twitter/X (smart home tech community)
- TikTok (short demos of "hey AI, turn off everything" → it works)

Help me create a content strategy with specific ideas for educate/inspire/entertain. What's my posting schedule? How do I build an email list? When should I consider paid ads?
```

---

## 8. `/grow-sustainably`

```
I'm at a decision point with SmartHub. Key questions:

1. Software-only vs hardware bundle: Should I sell just software (low cost, low margin, easy to scale) or a pre-configured Pi bundle (higher margin, supply chain risk, HA Yellow died from Pi DRAM crisis)?

2. Team size: Currently solo. When should I hire? The product spans hardware, backend, frontend, AI, and smart home protocols.

3. Fundraising: My research estimates $300-500K needed for the hardware path. Should I bootstrap, crowdfund (like Gumroad did), or seek VC alternatives like TinySeed?

4. Growth rate: SwitchBot AI Hub is already shipping. Google/Amazon are adding AI home features. How fast do I need to move?

5. The HA dependency: Home Assistant is our engine (Apache 2.0 licensed). They're improving their own UI and AI features. Is this a risk or a benefit?

Evaluate each decision through the profitability and sustainability lens. What's the minimalist path?
```

---

## 9. `/company-values`

```
I'm building SmartHub — an AI smart home hub. Before I hire anyone or formalize the company, I want to define values.

What I believe:
- Your home data should never leave your house
- Smart home should be simple enough for your parents to use
- $20 should be enough to make any device smart
- AI should create automations, not just execute commands
- Open source > walled gardens
- No subscriptions for basic device control, ever

The company vibe I want:
- Small team, remote, async
- Ship fast, iterate based on real user feedback
- Transparent — share financials, decisions, roadmap publicly
- Community-driven — the HA community is our foundation
- Engineering excellence — we wrap HA, so our layer must be rock-solid

Help me turn these beliefs into 3-5 proper company values with stories, not slogans.
```

---

## 10. `/minimalist-review`

```
Final gut-check on SmartHub.

Here's what I'm about to do:
1. Finish Phase 1 (dashboard + device control) and Phase 2A (AI chat) — already mostly built
2. Launch as a free, open-source HA add-on to the Home Assistant community
3. Offer a paid "SmartHub Pro" tier ($8/mo or $79/year) for: advanced AI automations, priority support, IR device profiles
4. Film a demo video showing the full flow: device auto-discovery → dashboard → "turn off everything" via AI chat → it works
5. Post to Reddit, YouTube, and HN
6. If 500+ signups in 30 days → proceed to hardware exploration
7. If <100 signups → pivot or kill

Review this plan. What's the minimalist version? What's the biggest risk? What should I try this week?
```
