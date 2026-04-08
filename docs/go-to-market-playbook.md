# SmartHub — Go-to-Market Playbook

**Date:** 2026-04-01
**Stage:** MVP complete, pre-launch
**Goal:** First 10 users, first paid customer

---

## Current Status

- MVP done: HA + Bun/Elysia API + OpenClaw AI layer, controlling Xiaomi TV, MA8 AC, P1V2 cooker
- Running on Raspberry Pi at home, accessible via Cloudflare tunnel
- Zero customers, zero conversations, zero revenue, zero public content
- Competitor SwitchBot AI Hub ($260) shipping but limited to SwitchBot ecosystem

## Positioning

**"Full, unrestricted Home Assistant with AI that actually controls everything — for $80, not $260."**

SwitchBot AI Hub ships crippled HA Core (no HACS, no add-ons, no USB). Their AI only controls SwitchBot devices. SmartHub runs full HA OS with OpenClaw controlling all 2,000+ integrations — Xiaomi, LG, Hue, anything.

---

## Week 1 — Start Conversations (Apr 1-7)

### Day 1-2: Find your people on r/homeassistant and HA forums

- [ ] Go through the posts below — read the threads, note the usernames, and identify who's still active
- [ ] Reply helpfully to 5 of the most recent ones — solve their actual problem, **no product mention**
- [ ] Search r/homeassistant directly (Reddit blocks web indexing, so search on-site) using: `"too complicated"`, `"gave up"`, `"WAF"`, `"simpler"`, `"frustrated"`

#### Posts: "It's too complicated / I'm giving up" (2024-2026)

These are people who hit the HA complexity wall — your exact target user.

| # | Post | Platform | Est. Date | Pain point |
|---|---|---|---|---|
| 1 | [Homeassistant is sometimes an unreliable time waster](https://community.home-assistant.io/t/homeassistant-is-sometimes-an-unreliable-time-waster/731161) | HA Forum | Early 2024 | "Becomes less reliable and less transparent as it grows" |
| 2 | [Thinking of dropping HA due to poor integration connectivity and consistency](https://community.home-assistant.io/t/thinking-of-dropping-home-assistant-due-to-poor-integration-connectivity-and-consistency/779978) | HA Forum | Mid 2024 | Reliability — "not wife or guest friendly" |
| 3 | [Disappointed rant - any suggestions?](https://community.home-assistant.io/t/disappointed-rant-any-suggestions/783280) | HA Forum | Mid 2024 | Catch-22: "people seeking automation to save time must spend time configuring" |
| 4 | [Issue with Core Update 2025.1.0](https://community.home-assistant.io/t/issue-with-core-update-2025-1-0/821725) | HA Forum | Jan 2025 | Update breaks system — users losing trust in stability |
| 5 | [Update to 2026.1.0 and UI no longer loads](https://community.home-assistant.io/t/update-to-2026-1-0-and-ui-no-longer-loads/971893) | HA Forum | Jan 2026 | Update kills the entire UI — users stranded |
| 6 | [Error in migration of new template entities 2025.12](https://community.home-assistant.io/t/error-in-migration-of-new-template-entities-in-2025-12-depretated-in-2026-6/972962) | HA Forum | Early 2026 | Forced migration breaking configs |

#### Posts: YAML / Automation Frustration (2024-2026)

People who can't create automations — the exact problem your AI solves.

| # | Post | Platform | Est. Date | Pain point |
|---|---|---|---|---|
| 7 | [New automation setup failed on 2025.1.2](https://community.home-assistant.io/t/new-automation-setup-failed-on-2025-1-2/830685) | HA Forum | Jan 2025 | Automation saves but setup times out — beginner stuck |
| 8 | [Playing around with automation yaml - 2 issues](https://community.home-assistant.io/t/playing-around-with-automation-yaml-2-issues/928274) | HA Forum | Late 2025 | Automation syntax confusion |
| 9 | [Help with automation in YAML. Beginner.](https://community.home-assistant.io/t/help-with-automation-in-yaml-beginner/967552) | HA Forum | Dec 2025 | Beginner can't create automations at all |

#### Posts: Wife/Spouse/Family Acceptance Factor (2024-2026)

People whose families can't or won't use HA — your "simple enough for your parents" angle.

| # | Post | Platform | Est. Date | Pain point |
|---|---|---|---|---|
| 10 | [Best practices for sharing with spouse/family?](https://community.home-assistant.io/t/best-practices-for-sharing-with-spouse-family/729862) | HA Forum | May 2024 | Can't figure out how to make HA usable for wife and kids |
| 11 | [WTH: Schedule for non-admins (Increase wife approval factor!)](https://community.home-assistant.io/t/wth-schedule-for-non-admins-increase-wife-approval-factor/805003) | HA Forum | Late 2024 | Non-admin family members locked out of basic features |
| 12 | [Help with spouse approval factor transitioning away from Google Home](https://community.home-assistant.io/t/help-with-spouse-approval-factor-transitioning-away-from-google-home/882561) | HA Forum | Mid 2025 | Spouse can't switch from Google Home to HA — too complicated |

#### Articles: People Quitting or Warning Others (2024-2026)

Written pieces from people who left HA or documented the downsides. **Read the comment sections** — they're full of frustrated users you can engage.

| # | Article | Source | Year | Key quote |
|---|---|---|---|---|
| 13 | [Self-hosting isn't always the answer — why HA is no longer powering my home](https://www.howtogeek.com/self-hosting-isnt-always-the-answer-why-home-assistant-is-no-longer-powering-my-home/) | HowToGeek | Feb 2026 | "Could not install HA on wife's phone with confidence she could use it on her own" |
| 14 | [4 uncomfortable truths about Home Assistant](https://www.howtogeek.com/uncomfortable-truths-about-home-assistant/) | HowToGeek | 2025 | Honest assessment of HA's real limitations for average users |
| 15 | [These are Home Assistant's biggest weaknesses](https://www.howtogeek.com/these-are-home-assistants-biggest-weaknesses/) | HowToGeek | 2025 | Setup complexity, reliability, learning curve |
| 16 | [5 things I wish I knew before going all-in on Home Assistant](https://www.xda-developers.com/things-wish-knew-before-going-all-in-home-assistant/) | XDA | 2025 | Regrets and lessons learned — many commenters agree |
| 17 | [Home Assistant review after one year of use](https://www.loopwerk.io/articles/2025/home-assistant-review/) | Loopwerk | 2025 | One-year retrospective — mixed feelings, reliability concerns |
| 18 | [Home Assistant Alternatives for Non-Technical Users](https://www.smarthomeadmin.com/alternatives/home-assistant-alternatives/) | SmartHomeAdmin | 2024-2025 | People actively searching for simpler alternatives |

#### How to use these posts

1. **Read the threads** — understand what specifically frustrated each person
2. **Check if they're recent and active** — recent posts (2024-2025) are more likely to have active users
3. **Reply helpfully** — answer their actual question or share a tip. No product mention.
4. **Note usernames** — people who posted AND people who commented agreeing. The commenters are your hidden audience.
5. **DM after helping** — "Hey, saw your post about [X]. I've been building something that might help..."
6. **Read the article comments** — HowToGeek and XDA articles have comment sections with frustrated users too

> **Important:** Reddit blocks web search indexing, so direct Reddit post URLs don't appear in web searches. You MUST search r/homeassistant directly on Reddit using the search terms above. The HA Community Forum posts listed here are from the same community — many users are active on both platforms.

### Day 3-4: DM those people

- [ ] DM each person you helped. Use this template (customize per person):

> Hey, saw your post about [specific problem]. I've been working on the same thing — I built an AI layer on top of HA that lets you control devices through Discord chat instead of the HA UI. You just type what you want in natural language and it does it.
>
> Would you be up for a 20-min screen share where I show you how it works? No charge, just looking for honest feedback. I want to know if this actually solves the problem or if I'm building something nobody needs.

- [ ] Track responses in a spreadsheet:

| Name | Source | Date DMed | Response | Interested? | Screen share scheduled? | Feedback |
|---|---|---|---|---|---|---|

### Day 5-7: Set up SmartHub on one other person's system

- [ ] Pick ONE person — friend, family member, or anyone who said yes to a DM
- [ ] Do the setup via screen share (or in person if local)
- [ ] **Watch them use it.** Don't guide them. Note:
  - Where they get confused
  - What they try that doesn't work
  - What they say out loud ("oh that's cool" or "wait, what?")
  - How long setup takes
- [ ] Ask them after: "Would you pay for this? If so, how much?"

### Week 1 success metric: 3+ real conversations with HA users

---

## Week 2 — Go Public (Apr 8-14)

### Record a demo

- [ ] Record a 2-minute screen recording showing:
  1. You type a message in Discord → AI controls a real device (AC or TV)
  2. You ask "what devices do I have?" → AI lists them
  3. You say "create an automation: turn off AC at midnight" → it does it
- [ ] Keep it raw — screen capture + voiceover, no fancy editing
- [ ] Upload to YouTube (unlisted is fine) or directly to Reddit

### Post to r/homeassistant

- [ ] Title: something like *"I built an AI chat layer for HA — type what you want in Discord and it controls your devices. Roast my setup."*
- [ ] Include: 2-min demo video, brief explanation of how it works, what you'd like feedback on
- [ ] **Frame as feedback request, not product launch**
- [ ] Respond to every comment, especially criticism

### Post to HA Community Forum

- [ ] Post in [Share your Projects](https://community.home-assistant.io/c/projects/9)
- [ ] More technical format: architecture diagram, how OpenClaw connects to HA, GitHub link
- [ ] Frame as: *"Here's a project I built — looking for feedback and contributors"*

### Join HA Discord

- [ ] Join [Home Assistant Discord](https://discord.com/invite/home-assistant) (159K members)
- [ ] Spend 2-3 days answering questions in #help
- [ ] Share your project in #show-off or equivalent channel

### Week 2 success metric: 1 public post with 10+ comments, 1 more screen share completed

---

## Week 3 — Broaden Reach (Apr 15-21)

### Broader Reddit

- [ ] Post to r/homeautomation (4.5M members)
  - Less technical audience — focus on the outcome, not the stack
  - Title angle: *"I replaced 5 smart home apps with one AI chat on a Raspberry Pi"*
- [ ] Post to r/smarthome (1.5M members)
  - Consumer angle: *"Control all your devices from one chat — no new app needed"*
- [ ] Post to r/selfhosted (700K members)
  - Privacy/local angle: *"Self-hosted AI smart home controller — no cloud, no subscription"*
- [ ] Post to r/raspberry_pi
  - Project angle: *"Here's what I'm running on my Pi — AI-powered smart home hub"*

### Local market — Malaysia/Singapore

- [ ] Post on [Lowyat.NET Smart Home section](https://www.lowyat.net/smart-home/)
  - Lead with price: *"SwitchBot AI Hub RM1,100 vs this Pi setup for RM300"*
  - Mention you're based in Malaysia
- [ ] Search Facebook for and join:
  - "Smart Home Malaysia" (groups)
  - "Home Automation Malaysia"
  - "Raspberry Pi Malaysia"
- [ ] Lurk for 2-3 days, help people, then share your setup story

### Week 3 success metric: 3+ platforms posted on, feedback from non-HA users

---

## Week 4 — Assess and Decide (Apr 22-28)

### Review all feedback

- [ ] Compile every piece of feedback from Reddit, forums, DMs, screen shares
- [ ] Answer these questions:
  1. **What excited people most?** (This is your actual value prop)
  2. **What confused people?** (This is what to fix)
  3. **What did people ask for that you don't have?** (This is your roadmap)
  4. **Did anyone say "I'd pay for this"?** (This is validation)
  5. **Which platform/community had the best response?** (This is where to focus)

### Decide positioning

Based on what resonated, pick ONE:
- **"The $80 open-source SwitchBot AI Hub alternative"** — if price/openness resonated
- **"AI that makes HA simple enough for your family"** — if the complexity-reduction resonated
- **"Control everything from chat — no new app"** — if the messaging-app interface resonated

### If you got positive signals (3+ people interested, 1+ "I'd pay"):

- [ ] Set up a landing page (Carrd.co — $19/year, takes 30 minutes)
  - One screenshot, one sentence, one CTA (email signup or "Get started")
- [ ] Price the first paid offering: $49 for remote setup via screen share
- [ ] Reach out to the people who showed interest and offer the paid setup

### If signals were weak (0-2 interested, nobody would pay):

- [ ] Re-read the feedback — is it a positioning problem or a product problem?
- [ ] Try a different angle on a different community
- [ ] Consider: is the problem not painful enough, or are you reaching the wrong people?

### Week 4 success metric: Clear go/no-go decision based on real evidence

---

## Month 2 Roadmap (if validated)

| Week | Action |
|---|---|
| Week 5-6 | 5 more paid setups ($49 each). Iterate based on each one. |
| Week 6-7 | First YouTube video: *"I built an $80 alternative to the $260 SwitchBot AI Hub"* |
| Week 7-8 | Landing page + email list. Offer a free guide: *"The $20 Smart Home Setup"* |
| Week 8 | 10 users, 3+ paying. Run `/minimalist-review` again with real data. |

---

## Outreach Platform Reference

### Tier 1 — Your exact audience (Week 1-2)

**Reddit:**

| Subreddit | Link | Size | Audience | Your angle |
|---|---|---|---|---|
| r/homeassistant | https://reddit.com/r/homeassistant | 444K-519K | HA users frustrated with complexity | AI simplifies HA |

**Non-Reddit:**

| Platform | Link | Size | Audience | Your angle |
|---|---|---|---|---|
| HA Community Forum — Share your Projects | https://community.home-assistant.io/c/projects/9 | Large, active | Technical HA users | Project showcase |
| HA Community Forum — Configuration | https://community.home-assistant.io/c/configuration/13 | Large, active | HA users needing help | Help first, build reputation |
| Home Assistant Discord | https://discord.com/invite/home-assistant | 159K | HA users seeking help | Help in #help, share in #show-off |

### Tier 2 — Broader smart home audience (Week 3)

**Reddit:**

| Subreddit | Link | Size | Audience | Your angle |
|---|---|---|---|---|
| r/homeautomation | https://reddit.com/r/homeautomation | 4.5M | General home automation | One app to rule them all |
| r/smarthome | https://reddit.com/r/smarthome | 1.5M | Consumer smart home | No more app juggling |
| r/selfhosted | https://reddit.com/r/selfhosted | 700K | Privacy-focused self-hosters | Local-first, no cloud |
| r/raspberry_pi | https://reddit.com/r/raspberry_pi | Large | Pi tinkerers | Cool Pi project |
| r/OpenClaw | https://reddit.com/r/OpenClaw | Small | OpenClaw users/developers | Built with OpenClaw showcase |

**Non-Reddit:**

| Platform | Link | Audience | Your angle |
|---|---|---|---|
| OpenClaw Discord | Check https://openclaws.io for invite link | OpenClaw community | Showcase a real OpenClaw deployment |
| Hacker News (Show HN) | https://news.ycombinator.com | Tech-savvy builders | Open-source AI + smart home |

### Tier 3 — Local SEA market (Week 3-4)

**Forums:**

| Platform | Link | Audience | Your angle |
|---|---|---|---|
| Lowyat.NET — Smart Home | https://www.lowyat.net/smart-home/ | Malaysian tech enthusiasts | RM price comparison vs SwitchBot |
| Lowyat.NET Forum — Hardware | https://forum.lowyat.net | Malaysian tech community | DIY Pi smart home build |
| HardwareZone Forums | https://forums.hardwarezone.com.sg/ | Singaporean tech users | SGD price comparison |

**Facebook Groups (search and join directly on Facebook):**

| Group name to search | Audience | Your angle |
|---|---|---|
| Smart Home Malaysia | Malaysian homeowners | Local, affordable, hot climate |
| Home Automation Malaysia | Malaysian DIY smart home | Pi-based setup, Xiaomi integration |
| Raspberry Pi Malaysia | Malaysian Pi tinkerers | Cool Pi project |
| Smart Home Singapore | Singaporean homeowners | No-subscription alternative |
| Home Automation Singapore | Singaporean DIY smart home | Local-first, privacy angle |

### Tier 4 — Amplifiers (Month 2+, after 10+ users)

| Platform | Link | When | How |
|---|---|---|---|
| YouTube | https://youtube.com | After 10+ users | Demo video: "$80 alternative to $260 SwitchBot AI Hub" |
| HA Creator Network | https://creators.home-assistant.io/ | After polished demo | Reach out to creators for coverage |
| Twitter/X | https://x.com | Ongoing | Build-in-public updates, screenshots, GIFs |
| Product Hunt | https://producthunt.com | After 30+ users | "Launch" as celebration, not acquisition |
| Dev.to | https://dev.to | After first blog post | Technical write-up for developer audience |
| Medium | https://medium.com | After first blog post | Non-technical write-up for broader audience |

---

## Rules

1. **Help first, pitch second.** First 5 interactions on any platform = answering questions, not promoting.
2. **No "launch" event.** Give it to 10 people. Then 30. Then 100. Launch is a celebration at 100.
3. **Every conversation is data.** Track what people say, what excites them, what confuses them.
4. **Don't write more code until Week 4.** The product is sufficient. The missing piece is people.
5. **Charge something by Week 4.** Even $10 proves more than 1,000 free signups.

---

## Kill Criteria

| Deadline | If this hasn't happened... | Decision |
|---|---|---|
| **Apr 15** (2 weeks) | Haven't had 5 real conversations | You're avoiding the market. Force yourself or accept this is a hobby. |
| **Apr 29** (4 weeks) | Nobody outside your household has used it | There's a delivery/setup problem. Simplify the install. |
| **May 13** (6 weeks) | Nobody has said "I'd pay for this" | Problem isn't painful enough or positioning is wrong. Pivot or park. |
| **Jul 1** (3 months) | Zero revenue | Kill it as a business. Keep it as a personal project if you enjoy it. |

---

## Templates

### Reddit DM — after helping someone

> Hey, saw your post about [specific problem]. I've been building something that might help — an AI layer on top of HA that lets you control devices through Discord/chat. You type "turn off the AC" and it does it. No YAML, no UI navigation.
>
> Would you try it? I'd do a 20-min screen share to set it up. Free, just want honest feedback.

### Reddit post — "roast my setup"

> **Title:** I built an AI chat layer for Home Assistant — type what you want in Discord and it controls your devices
>
> I got tired of navigating the HA UI for simple things, so I built an OpenClaw-based AI agent that sits on top of HA and talks through Discord.
>
> What it does:
> - "Turn off the AC" → calls the HA service
> - "What devices do I have?" → lists everything with status
> - "Create an automation: lights off at midnight" → builds and saves it
>
> Running on a Pi with HA in Docker. Currently controlling a Xiaomi AC, TV, and smart cooker.
>
> [2-min demo video]
>
> Looking for feedback — what's useful, what's pointless, what would you actually want this to do?

### Lowyat/Facebook post — price angle

> I've been building a smart home setup on a Raspberry Pi that controls all my devices from one chat interface — Xiaomi AC, TV, everything.
>
> Total cost: ~RM300 (Pi + setup). For comparison, SwitchBot AI Hub is RM1,100 and only works with SwitchBot devices.
>
> Mine works with Xiaomi, LG, Philips Hue, basically anything Home Assistant supports (2,000+ integrations). And it runs fully local — no cloud, no subscription.
>
> Anyone else running a Pi-based smart home here? Would love to compare setups.
