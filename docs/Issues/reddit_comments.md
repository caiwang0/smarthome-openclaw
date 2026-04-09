# Reddit Feedback — r/homeassistant

Source: Reddit post "Comments on using openclaw for HA"

---

## Safety & Trust Concerns

- **AI having write access to HA is risky** — Users are hesitant to give any AI direct control over their setup, even with approval steps. Multiple commenters had bad experiences with automation testing going sideways. (East_Owl_9652, mgithens1, undrwater)
- **"Giving the keys to a bum on the streets"** — Strong distrust of autonomous AI control over home infrastructure. If it goes wrong, it goes very wrong. (Brtrnd2)
- **Approval gating is the expected pattern** — Users want read access to be automatic, but any config mutation (create/edit/delete automations, integrations) should require explicit user confirmation before executing. (Just-Imagination-761, Deep_Ad1959)
- **Data exfiltration allegations** — Claim that OpenClaw has "been shown to exfiltrate data or do other harm to systems." Needs to be investigated and addressed publicly if false. (Brtrnd2)
- **Open source claims questioned** — Commenter alleges "OpenClaw is NOT open source, at least not the parts that matter." Need to clarify what is and isn't open source. (Brtrnd2)

## Usability & Reliability

- **AI "craps the bed" occasionally** — Even after 3-4 weeks of use, the AI still makes mistakes often enough that users won't trust it with HA write access. Currently only trusted with lower-risk services like Sonarr/Radarr. (mgithens1)
- **Dashboard redesign doesn't work well** — Attempted 5 times to redesign dashboard, results were broken or ugly. Used free Claude tier. (BoKKeR111)
- **Energy usage graphing failed** — Attempting to create a graph of average energy usage by hour over a month didn't work, though a SQLite query for raw data export worked first try. (Just-Imagination-761)
- **Accumulated automation confusion** — When multiple people give instructions, nobody remembers what was set up. Example: "You ask it to turn off the AC at 3am... two weeks later you're pulling your hair out trying to figure out why the AC never works overnight." (Just-Imagination-761)

## Comparison with Alternatives

- **ha-mcp preferred by power users** — Approval-gated approach where read ops are auto-approved but config changes need confirmation. Seen as the safer, more correct approach. (Just-Imagination-761, Brtrnd2, Deep_Ad1959)
- **Copy-paste YAML approach** — Some users prefer using AI just to generate YAML, then manually pasting it into HA. Lower risk, easy to revert, and lets them switch between ChatGPT/Grok/Claude. (mgithens1)
- **Apple HomeKit / Google Home for non-technical users** — For family members who aren't technical, mainstream smart home platforms are simpler. (Brtrnd2)
- **Home Assistant Builder CLI (hab)** — Alternative tool mentioned: `balloob/home-assistant-build-cli` with OpenCode app for HA. (Gamester17)
- **Test bed instance recommended** — Run a separate non-production HA instance for testing AI changes, then copy working config to production. (undrwater)

## Local AI / Self-Hosting

- **Users want local model support** — Running models via Ollama locally for privacy and control. Willingness to trade speed for accuracy, especially for background/overnight tasks. (mgithens1)
- **Model flexibility is valued** — Ability to swap between small (4B) models for quick tasks and large (14B) models for accuracy is seen as a strength of OpenClaw. (mgithens1)
- **MoE models as potential sweet spot** — Mixture of Experts models could offer large-model accuracy with better performance on consumer hardware. (mgithens1)

## Positive Feedback

- **Skill files system praised** — Teaching the agent device-specific quirks (e.g., Xiaomi TV vs Hue bulbs) makes it less likely to give generic advice. (OP)
- **Script review before execution** — Agent flagging sketchy scripts before running them has saved users from mistakes. (OP)
- **Random system tasks work surprisingly well** — Setting up a network printer (CUPS install and config) worked and surprised the user. (OP)

---

## Action Items

1. **Address open source and data exfiltration claims** — Publicly clarify what is open source and refute data exfiltration allegations if untrue
2. **Consider adding approval gating** — Implement a confirmation step for all write/mutate operations on HA (this may already exist per CLAUDE.md rules, but users don't seem aware)
3. **Improve dashboard generation** — Dashboard redesign was cited as broken/ugly
4. **Add automation audit/visibility** — Help users understand what automations exist and why, to prevent the "who set this up?" confusion
5. **Document model recommendations** — Guide users on which local models work best for different task types
