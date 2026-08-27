# 🛫 Obsidian Flight Deck

**Your day, on one Obsidian page — built automatically from your live tools.**

Flight Deck turns an Obsidian note into a self-refreshing dashboard: what you shipped, what's in
progress, who you're waiting on, today's calendar, the email that actually needs you, your unsent
Slack drafts, and the status of the services you depend on. It reads from GitHub, Google, Slack,
and any status page — and writes a clean, card-based page into your vault every few minutes.

No servers. No database. Pure-Python, standard library only. Your data stays on your machine.

```
┌─ 🔥 Standup ──────────────────────────┐  ┌─ ℹ️ System status 🟢 ─────────────┐
│ Focused on top priorities this week    │  │ • GitHub  🟢 operational          │
│ • Billing — shipped, awaiting QA        │  │ • Claude  🟢 operational          │
│ • Onboarding — in progress, 3/5 PRs     │  └──────────────────────────────────┘
│ What's next: …                          │  ┌─ ❓ Waiting on ───────────────────┐
└────────────────────────────────────────┘  │ Alice · sign-off on the API spec  │
┌─ 📊 Tech progress — last 24h ─────────┐  │ Bob   · QA on the transfers build │
│ opened 8 · merged 6 · +5,981 / -104     │  └──────────────────────────────────┘
│ ┌ PR ─── project ──── what ──────────┐  │  ┌─ 📅 Calendar — today ─────────────┐
│ │ #18792 Billing   data model         │  │  │ 11:30  Tech Standup  ↗            │
│ │ #18758 Onboarding dashboard tiles   │  │  │ ✉️ invite to respond — Planning   │
│ └────────────────────────────────────┘  │  └──────────────────────────────────┘
└────────────────────────────────────────┘
```
*(Rendered as native Obsidian callout cards — see `docs/mockups/flight-deck.html` for the styled look.)*

---

## What each panel does

| Panel | Shows | Needs |
|---|---|---|
| **Standup** | An editable note you curate (embedded live) | nothing |
| **My notes** | A scratch note, editable beside the deck | nothing |
| **Tech progress** | Last-24h PR metrics + merged/in-progress tables, tagged by project | GitHub |
| **Waiting on** | Who owes you, scanned from your project notes | nothing |
| **System status** | Any Statuspage service (GitHub, Claude, your own…) | nothing |
| **Calendar** | Today's events + invites to answer, clickable | Google (read-only) |
| **Email — needs you** | Unread person-to-person mail, newsletters filtered | Google (read-only) |
| **Slack drafts** | Your unsent drafts (never posts) | Slack |

Every panel is **optional and reorderable** — you list the ones you want, in the order you want,
in one config file. Every panel is **extensible** — the status panel takes any list of status
URLs; the GitHub panel takes any repos and your own project-label rules.

## Quickstart

```bash
pip install obsidian-flight-deck          # or: pipx install obsidian-flight-deck
flightdeck init                           # writes ~/.config/flightdeck/flightdeck.toml
$EDITOR ~/.config/flightdeck/flightdeck.toml   # set your vault path + repos
flightdeck setup github                   # reuses `gh` if you have it, else paste a token
flightdeck run                            # builds the deck into your vault
flightdeck install-schedule               # auto-refresh every few minutes
```

Open the deck note in Obsidian (Reading view). Done.

Add calendar/email/slack when you want them:

```bash
flightdeck setup google                   # read-only Calendar + Gmail (5-min one-time OAuth)
flightdeck setup slack                    # browser-session tokens, no app approval
```
…then uncomment those panels in your config. See [`docs/AUTH.md`](docs/AUTH.md).

## Configuration

One file, `flightdeck.toml`. Panels are declared as an ordered list — see
[`flightdeck.example.toml`](flightdeck.example.toml). Example:

```toml
[vault]
path = "~/Obsidian/MyVault"

[[panels]]
name = "status"
[[panels.services]]
label = "GitHub"
url = "https://www.githubstatus.com"
[[panels.services]]
label = "My API"
url = "https://status.mycompany.com"      # any Statuspage works

[[panels]]
name = "github_prs"
repos = ["my-org/app", "my-org/infra"]
active_projects = ["Billing", "Onboarding"]
[panels.github_prs.project_labels]
"bill|invoice" = "Billing"
```

## Extending it

- **Add a status endpoint** — just add another `[[panels.services]]` with a URL. No code.
- **Add repos / project mapping** — edit the `github_prs` panel options. No code.
- **Add a whole new panel** — write a `Panel` subclass, register it, enable it in config.
  Full guide: [`docs/PANELS.md`](docs/PANELS.md). A panel is ~30 lines.

## Design

- **Pure stdlib.** No pip dependencies. Config is TOML (read via `tomllib`).
- **Everything derived.** The deck is regenerated every run; you never hand-edit it. The only
  hand-edited inputs are the notes you embed (Standup, My notes).
- **Read-only by default.** Google and Slack use read-only scopes; the Slack integration can create
  drafts but **cannot post**.
- **Your machine.** Credentials live in your OS keychain (macOS) or a `0600` file. Nothing is sent
  anywhere except the APIs you configured.

## Roadmap

- Optional per-viewer web export (share a redacted subset).
- An "ask your deck" agent over the daily JSON snapshots.
- More built-in panels (CI, incidents, on-call, metrics).

## License

MIT. Originally generalized from a personal Flight Deck by Greg Richardson.
