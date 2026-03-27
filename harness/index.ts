/**
 * SmartHub Frontend Harness
 *
 * Generator-Evaluator architecture for producing high-quality frontend.
 * Based on Anthropic's harness design: https://www.anthropic.com/engineering/harness-design-long-running-apps
 *
 * Optimized for HOME USERS — people who want to control their house,
 * not admire a design portfolio.
 *
 * Usage: bun run index.ts
 */

import { query, type SDKMessage } from "@anthropic-ai/claude-agent-sdk";

// ─── Configuration ────────────────────────────────────────────────────────────

const CONFIG = {
  dashboardDir: "/home/edgenesis/Downloads/home-assistant/dashboard",
  projectDir: "/home/edgenesis/Downloads/home-assistant",
  dashboardUrl: "http://localhost:3000",
  maxRounds: 15,
  passThreshold: 4,
  model: "claude-sonnet-4-6",
  evaluatorModel: "claude-opus-4-6",
  plannerModel: "claude-opus-4-6",
};

// ─── Prompt Templates ─────────────────────────────────────────────────────────

const PLANNER_PROMPT = `You are a product designer at a smart home company. Your users are REGULAR PEOPLE — families, parents, elderly people, renters, anyone who wants to control their home easily.

The dashboard is a React 19 + TypeScript + Tailwind CSS app served by Vite.
It controls real Home Assistant devices: lights, switches, climate, cameras, sensors, media players.

READ all source files in the src/ directory to understand the current state.

YOUR DESIGN MUST PRIORITIZE (in order):

1. **USABILITY** — Can a non-technical person figure this out in 5 seconds?
   - Device state must be obvious at a glance (ON = visually loud, OFF = visually quiet)
   - Controls must have large touch targets (min 44px) for phone/tablet use
   - The most common action (toggle a device) must be ONE tap
   - Labels must be plain English, not technical jargon
   - Room grouping must feel natural, like walking through your house

2. **WARMTH** — This is someone's HOME, not a server room
   - Soft, rounded shapes. Generous padding. Breathing room.
   - A warm color palette — NOT cold grays and blues
   - Friendly, readable sans-serif font (not monospace, not ultra-thin)
   - Device icons should be recognizable and charming, not abstract
   - Light theme or warm dark theme — not pitch black

3. **GLANCEABILITY** — Dashboard on a wall tablet, seen from across the room
   - Active devices should POP visually (color, size, or position)
   - Offline/problem devices need clear but not alarming indicators
   - Temperature, humidity, and sensor values should be readable at arm's length
   - Room names should be prominent section headers

4. **POLISH** — Small details that signal quality
   - Smooth transitions (200-300ms) on state changes
   - Satisfying toggle animations
   - Consistent spacing rhythm (8px grid)
   - Proper loading/empty states

REFERENCE PRODUCTS (study their UX, not copy their look):
- Apple Home app — large device tiles, room tabs, clear on/off states
- Google Home app — friendly cards, warm colors, prominent device names
- Philips Hue app — beautiful color pickers, ambient room visualization
- IKEA Home Smart — simple, approachable, no-jargon controls

BANNED:
- Monospace fonts (this is a home, not a terminal)
- Pure black backgrounds (#000-#111)
- Acid/neon accent colors
- Brutalist/industrial aesthetics
- Tiny text below 14px for any user-facing label
- Technical jargon (entity_id, MAC address) shown by default
- Glassmorphism / frosted glass (overused AI pattern)
- Purple-blue gradients (overused AI pattern)

Produce a SPRINT CONTRACT with:

1. **Design Direction** — Describe the feeling/mood, not just the look. How does a user FEEL using this?
2. **Color Palette** — Warm, home-appropriate colors. Include semantic colors (device-on, device-off, warning, room-header).
3. **Typography** — A friendly, readable Google Font. Good at small AND large sizes. Has character but isn't distracting.
4. **Layout** — How are rooms/devices organized? What's the visual hierarchy? How do device cards differ by type?
5. **Interaction Design** — Toggle behavior, hover/press states, touch targets, animations
6. **Component-by-Component Changes** — For EACH file in src/components/, specify exact changes
7. **Acceptance Criteria** — Testable UX conditions:
   - "A user can identify which devices are ON within 2 seconds of seeing the page"
   - "Toggle touch targets are at least 44x44px"
   - "Room names are readable from 1 meter away on a tablet"
8. **Implementation Order**

The result should feel like an app you'd be PROUD to show friends who visit your house. Not a tech demo — a product.`;


const GENERATOR_PROMPT = (contract: string, feedback: string) => `You are a senior frontend engineer implementing a smart home dashboard for regular home users.

STACK: React 19, TypeScript, Tailwind CSS, Vite
PROJECT: Read files in the src/ directory.

SPRINT CONTRACT:
${contract}

${feedback ? `EVALUATOR FEEDBACK FROM PREVIOUS ROUND:\n${feedback}\n\nFix every issue listed above. The evaluator interacts with the live page — if they say something is wrong, it IS wrong.` : "This is round 1. Implement the full sprint contract."}

RULES:
- Edit existing files. Do NOT create new files unless absolutely necessary.
- Use Tailwind classes. Add custom CSS to index.css only if Tailwind can't do it.
- Keep all functionality working — device controls, polling, area filtering.
- Icons should be clear and recognizable — use Lucide React if needed (install it).
- Touch targets: minimum 44x44px for all interactive elements.
- Text: minimum 14px for labels, 12px only for metadata that's not critical.
- Test your changes compile: run "npx vite build" after editing.
- If the build fails, FIX IT before finishing.
- Hide technical details (MAC, IP, entity_id) behind a "details" toggle or remove from the default view.

After implementing, run the build and report what changed.`;


const EVALUATOR_PROMPT = (contract: string, round: number) => `You are a UX evaluator testing a smart home dashboard. You represent HOME USERS — a parent managing their family's devices, a retiree who just wants the lights to work, a renter with a few smart plugs.

Open the dashboard at ${CONFIG.dashboardUrl}, interact with it, and score it.

SPRINT CONTRACT:
${contract}

ROUND: ${round}

EVALUATION PROCESS:
1. Navigate to the dashboard
2. Take a full-page screenshot
3. Try to identify which devices are ON vs OFF — time yourself, is it instant?
4. Try to toggle a device — how many clicks? How large is the target?
5. Click through room/area filters
6. Check if the page would work on a tablet (resize to 768px width)
7. Screenshot at tablet size
8. Read device names and values — are they clear?

SCORING CRITERIA (1-5 each):

**Usability** — Can a regular person use this without instructions?
- 1: Confusing layout, unclear what to tap, technical jargon visible
- 2: Basic functionality discoverable but some controls are unclear
- 3: Most actions are intuitive but some require guessing
- 4: Clear, obvious controls. A new user could figure it out immediately
- 5: Delightfully obvious. Every interaction feels natural and expected

**Visual Comfort** — Does this feel like a home, not a tech demo?
- 1: Cold, dark, technical. Feels like a server monitoring tool
- 2: Some warmth but overall sterile or overly techy
- 3: Neutral — neither inviting nor repelling
- 4: Warm, friendly, feels appropriate for a living room wall tablet
- 5: Beautiful and inviting. You'd want this displayed in your home

**Glanceability** — Can you understand the state of your home at a glance?
- 1: All devices look the same regardless of state
- 2: On/off is distinguishable but requires reading text
- 3: Active devices are somewhat visually distinct
- 4: Instant recognition of device states from visual cues alone
- 5: The page is like a "status board" — one look tells you everything

**Responsiveness** — Does it work across screen sizes?
- 1: Broken at tablet/mobile sizes
- 2: Functional but cramped or poorly laid out on small screens
- 3: Acceptable on both desktop and tablet
- 4: Good experience on all sizes, proper touch targets
- 5: Optimized for each size — feels native on tablet, great on desktop

**Functionality** — Does everything still work?
- 1: Page doesn't load or major features broken
- 2: Some controls don't work
- 3: Core features work but edge cases broken
- 4: Everything works, minor visual glitches
- 5: Fully functional, smooth interactions

SCORING PHILOSOPHY:
You are STRICT but FAIR. You don't hand out 4s for "good enough" — a 4 means a real home user would genuinely enjoy using this. But you also recognize progress: if the generator fixed 5 issues and introduced 1 new one, acknowledge the wins and focus feedback on the remaining gap. You are NOT a perfectionist gatekeeper — you are a demanding product manager who ships quality.

IMPORTANT SCORING RULES:
- A score of 4 means "I would confidently give this to my parents to use." If you wouldn't, it's a 3 or below.
- A score of 3 is NOT a failure — it means "functional and decent but not delightful yet." Most round-1 outputs land here.
- Never give a 4+ on Usability if touch targets are below 44px or text is below 14px.
- Never give a 4+ on Visual Comfort if you see monospace fonts, pure black backgrounds, or neon accents.
- Never give a 4+ on Glanceability if ON and OFF devices look the same at arm's length.
- DO give credit where earned. If one area is excellent, score it high even if others lag.
- Track progress across rounds. In your critique, note what IMPROVED since last round (if applicable) — this helps the generator know what's working.

OUTPUT FORMAT (you MUST follow this exactly):
\`\`\`
SCORES:
- Usability: X/5
- Visual Comfort: X/5
- Glanceability: X/5
- Responsiveness: X/5
- Functionality: X/5
- LOWEST: X/5

VERDICT: PASS or FAIL

WHAT IMPROVED (from previous round):
- [list improvements, or "First round" if round 1]

WHAT'S WORKING (keep these):
- [things the generator got right — be specific so they don't regress]

SPECIFIC ISSUES (ranked by impact):
1. [highest impact issue — what most hurts a home user's experience]
2. [second highest]
3. [etc.]

CRITIQUE FOR GENERATOR:
[Specific, actionable fixes. Frame as user stories: "A user trying to turn off their living room light would struggle because..." not "the toggle opacity is too low". Prioritize: fix the TOP 3 issues first. Don't overwhelm with 15 nitpicks — focus on what moves the needle most.]
\`\`\`

CALIBRATION:

**Usability = 2:** Toggle switches exist but they're 24px wide and have no labels. A user has to guess that the tiny switch controls the device. Technical info (MAC address, entity_id) is shown prominently but device name is truncated.

**Usability = 4:** Each device has a clearly labeled toggle with a 44px+ touch target. Device names are prominent. ON/OFF is obvious. A first-time user wouldn't hesitate. Room headers help you find things fast. (NOT a 5 because: maybe the toggle animation isn't satisfying, or the layout isn't optimized for the most common actions.)

**Usability = 5:** Everything in 4, PLUS: the most-used devices feel prioritized. Toggling is satisfying with micro-feedback. The whole flow feels like it was designed by someone who lives in this house.

**Visual Comfort = 2:** Dark gray background, thin gray text, monospace font, neon accent colors. Looks like a hacker's tool. You'd never put this on a kitchen tablet.

**Visual Comfort = 4:** Warm, friendly palette. Rounded cards with soft shadows. Good font that's readable and has personality. You'd put this on a wall tablet and not be embarrassed. (NOT a 5 because: maybe the color palette is slightly generic, or the dark/light balance isn't quite cozy enough.)

**Visual Comfort = 5:** Everything in 4, PLUS: the design has a distinct personality. The color choices feel intentional and cohesive. It genuinely makes the room feel smarter and warmer. Guests would comment on it.

**Glanceability = 2:** All device cards are the same gray rectangle. You have to read the text "on"/"off" to know the state. Sensor values are tiny text buried in a corner.

**Glanceability = 4:** ON devices clearly stand out (color, glow, or visual weight). You can tell the state of your home from 3 feet away. Sensor values are readable. (NOT a 5 because: maybe some device types blend together, or the visual hierarchy could be sharper.)

**Glanceability = 5:** The dashboard is a genuine "status board." One glance from across the room and you know: lights on in the kitchen, AC running, front door sensor triggered. Visual encoding is so clear you don't need to read text.

Score honestly but constructively. This dashboard will be used by real families. Your job is to PUSH it to be great, not to block it from shipping.`;

// ─── Helper: Run an agent and collect result ──────────────────────────────────

async function runAgent(
  prompt: string,
  options: {
    model?: string;
    allowedTools?: string[];
    mcpServers?: Record<string, any>;
    cwd?: string;
    maxTurns?: number;
  } = {}
): Promise<string> {
  let result = "";
  let lastAssistantText = "";

  for await (const message of query({
    prompt,
    options: {
      model: options.model,
      allowedTools: options.allowedTools || [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
      ],
      mcpServers: options.mcpServers,
      cwd: options.cwd || CONFIG.dashboardDir,
      maxTurns: options.maxTurns || 100,
      permissionMode: "bypassPermissions",
      allowDangerouslySkipPermissions: true,
    },
  })) {
    const msg = message as any;

    if (msg.type === "assistant" && msg.message?.content) {
      for (const block of msg.message.content) {
        if (block.type === "text") {
          lastAssistantText = block.text;
        }
      }
    }

    if (msg.type === "result") {
      result = msg.result || lastAssistantText;
    }
  }

  return result || lastAssistantText;
}

// ─── Score Parser ─────────────────────────────────────────────────────────────

function parseScores(evaluation: string): Record<string, number> {
  const defaults: Record<string, number> = {
    Usability: 3,
    "Visual Comfort": 3,
    Glanceability: 3,
    Responsiveness: 3,
    Functionality: 3,
  };

  const patterns: [string, RegExp][] = [
    ["Usability", /Usability:\s*(\d)\/5/i],
    ["Visual Comfort", /Visual Comfort:\s*(\d)\/5/i],
    ["Glanceability", /Glanceability:\s*(\d)\/5/i],
    ["Responsiveness", /Responsiveness:\s*(\d)\/5/i],
    ["Functionality", /Functionality:\s*(\d)\/5/i],
  ];

  for (const [key, regex] of patterns) {
    const match = evaluation.match(regex);
    if (match) {
      defaults[key] = parseInt(match[1], 10);
    }
  }

  return defaults;
}

// ─── Main Harness Loop ────────────────────────────────────────────────────────

async function main() {
  console.log("═══════════════════════════════════════════════════");
  console.log("  SmartHub Frontend Harness");
  console.log("  Optimized for Home Users");
  console.log("═══════════════════════════════════════════════════\n");

  // ── Step 1: Planner ──
  console.log("▶ STAGE 1: PLANNER");
  console.log("  Designing for real home users...\n");

  const contract = await runAgent(PLANNER_PROMPT, {
    model: CONFIG.plannerModel,
    allowedTools: ["Read", "Glob", "Grep"],
    maxTurns: 50,
  });

  console.log("  ✓ Sprint contract created\n");

  const harnessDir = "/home/edgenesis/Downloads/home-assistant/harness";
  await Bun.write(`${harnessDir}/sprint-contract.md`, contract);
  console.log(`  Saved to ${harnessDir}/sprint-contract.md`);
  console.log("─".repeat(60));

  // ── Step 2: Generator-Evaluator Loop ──
  let feedback = "";
  let passed = false;

  for (let round = 1; round <= CONFIG.maxRounds; round++) {
    console.log(`\n▶ ROUND ${round}/${CONFIG.maxRounds}`);

    // ── Generator ──
    console.log("  ┌─ GENERATOR: Building the dashboard...");
    await runAgent(GENERATOR_PROMPT(contract, feedback), {
      model: CONFIG.model,
      cwd: CONFIG.dashboardDir,
      maxTurns: 150,
    });
    console.log("  │  ✓ Code changes applied");

    // ── Rebuild ──
    console.log("  │  Rebuilding...");
    await runAgent(
      `Run: cd /home/edgenesis/Downloads/home-assistant && docker compose up -d --build dashboard && sleep 8 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`,
      {
        model: "haiku",
        cwd: CONFIG.projectDir,
        allowedTools: ["Bash"],
        maxTurns: 10,
      }
    );
    console.log("  │  ✓ Dashboard live");

    // ── Evaluator ──
    console.log("  └─ EVALUATOR: Testing as a home user...");
    const evaluation = await runAgent(
      EVALUATOR_PROMPT(contract, round),
      {
        model: CONFIG.evaluatorModel,
        allowedTools: ["Read", "Bash"],
        mcpServers: {
          playwright: {
            command: "npx",
            args: [
              "@playwright/mcp@latest",
              "--executable-path", "/usr/bin/chromium",
            ],
          },
        },
        cwd: CONFIG.dashboardDir,
        maxTurns: 50,
      }
    );

    await Bun.write(`${harnessDir}/eval-round-${round}.md`, evaluation);

    const scores = parseScores(evaluation);
    const lowest = Math.min(...Object.values(scores));

    console.log(`\n  SCORES:`);
    for (const [criterion, score] of Object.entries(scores)) {
      const bar = "█".repeat(score) + "░".repeat(5 - score);
      const icon = score >= CONFIG.passThreshold ? "✓" : "✗";
      console.log(`    ${icon} ${criterion}: ${bar} ${score}/5`);
    }

    if (lowest >= CONFIG.passThreshold) {
      passed = true;
      console.log(`\n  ✅ PASS — All scores >= ${CONFIG.passThreshold}`);
      break;
    } else {
      console.log(`\n  ❌ FAIL — Lowest: ${lowest}. Iterating.`);
      feedback = evaluation;
    }
  }

  console.log("\n" + "═".repeat(60));
  if (passed) {
    console.log("  HARNESS COMPLETE — Dashboard ready for home users ✅");
  } else {
    console.log(`  ${CONFIG.maxRounds} rounds exhausted. Review eval files.`);
  }
  console.log("═".repeat(60));
}

main().catch((err) => {
  console.error("Harness error:", err);
  process.exit(1);
});
