# Minimalist Entrepreneur Skills — Usage Guide

Based on "The Minimalist Entrepreneur" by Sahil Lavingia. These 10 skills are installed as Claude Code slash commands.

## How They Work

Each skill **automatically reads your project context** — README, docs/, codebase — and **does web research** for current market data. You don't need to paste your product description every time. Just run the command from your project directory.

## Recommended Order

Run them in this sequence. Each builds on the outputs of the previous ones (saved to `docs/`):

| # | Command | What it does | Output file |
|---|---|---|---|
| 1 | `/find-community` | Researches communities, finds real complaint posts, ranks by fit | `docs/community-analysis.md` |
| 2 | `/validate-idea` | Green/red flag assessment with competitor research and customer interview script | `docs/validation-report.md` |
| 3 | `/mvp` | Inventories what's built vs planned, ruthlessly cuts scope | `docs/mvp-spec.md` |
| 4 | `/processize` | Designs the manual delivery playbook with intake questions and follow-up messages | `docs/service-playbook.md` |
| 5 | `/first-customers` | Draft outreach DMs, Reddit posts, cold email templates — ready to send | `docs/first-customers-playbook.md` |
| 6 | `/pricing` | Current competitor pricing research, tier design, financial independence math | `docs/pricing-model.md` |
| 7 | `/marketing-plan` | Content strategy with 15 ideas + one fully drafted piece of content | `docs/marketing-plan.md` |
| 8 | `/grow-sustainably` | Evaluates specific decisions (hire? fundraise? hardware?) with real cost data | `docs/growth-decisions.md` |
| 9 | `/company-values` | Derives values from your actual codebase decisions, not generic slogans | `docs/company-values.md` |
| 10 | `/minimalist-review` | Reads ALL previous outputs, scores you 0-8, gives hard truths and this-week actions | `docs/minimalist-review.md` |

## Re-running Skills

Skills are designed to be re-run as your situation changes:

- **After customer conversations** → re-run `/validate-idea` with what you learned
- **After first paid customer** → re-run `/pricing` and `/minimalist-review`
- **Before a big decision** → run `/grow-sustainably` with the specific question
- **Periodically** → run `/minimalist-review` as an honest gut-check

## Adding Context

The skills read your project automatically, but you can always add context in the prompt:

```
/validate-idea I talked to 5 people on Reddit this week. 3 said they'd pay, 2 said they'd just use HA directly.
```

```
/pricing We got our first paid customer at $49 for remote setup. They said it was "worth it."
```

```
/minimalist-review We have 12 users now, 3 paying. Should we start building Phase 2?
```
