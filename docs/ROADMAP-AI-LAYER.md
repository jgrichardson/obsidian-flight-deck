# Roadmap: the optional AI layer (harness-agnostic)

The core of Flight Deck is a **plain data dashboard** — no AI, no lock-in. This document plans an
*optional* AI layer that stays true to that: pluggable across whatever coding agent you already use
(Claude Code, Codex, Gemini CLI, or any command that reads a prompt and writes text).

## Why it's optional and pluggable
- The dashboard must work with zero AI for people who just want their tools unified.
- Nobody should be forced onto one vendor. The AI layer shells out to a **configurable command**, so
  it works with any CLI harness — you bring your own.

## What it would add (two features)

### 1. Compose the standup
Instead of you writing the Standup card, the AI reads the day's structured data (the `github_prs`
output, waiting-on, calendar) plus your saved preferences and drafts the standup in your voice. You
still edit it; it just removes the blank page.

### 2. Ask your deck
Natural-language questions over the current deck + the daily JSON snapshots:
*"what am I working on today?"*, *"what shipped this week?"*, *"when did project X start?"*.

## Design

- **`[ai]` config block** names the harness command, e.g.
  ```toml
  [ai]
  command = "claude -p"          # or "codex exec", "gemini -p", "llm", any stdin->stdout CLI
  ```
- A tiny `flightdeck/ai.py` runs `command`, piping a prompt on stdin and capturing stdout. No SDK,
  no API keys in Flight Deck — the harness you name already has your auth.
- **Structured history**: the generator emits `Archive/<date>.json` (durable, redacted: no
  email/calendar/quota). The "ask" feature retrieves the relevant days and passes them to the harness.
- New commands: `flightdeck standup` (compose today's), `flightdeck ask "<question>"`.
- New optional panel: `ai_standup` (embeds the composed file, same as the manual standup embed).

## Privacy
The AI layer sends deck data to whatever command you configure. Keep the redacted JSON as the "ask"
context (no private email/calendar). Document clearly that enabling it sends content to your chosen
harness.

## Positioning decision (for maintainers)
- **Stay a general tool** → keep AI as this opt-in layer; headline stays "dashboard from your dev tools."
- **Lead with AI** → rename/pitch around "AI standup + ask your deck," ship the AI layer as a first-class
  feature, keep it harness-agnostic so it's not "a Claude thing" or "a Codex thing."

Recommendation: ship the general tool first (done), add this layer in a `0.2` once there's usage
signal, and keep it harness-agnostic from day one.
