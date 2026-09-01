# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org).

## [Unreleased]
### Added
- New built-in panel `decile_base` — mentions-owed + channel activity via a Claude Code MCP server,
  with auto-discovered credentials (no `flightdeck setup` step) and a `whoami` identity lookup instead
  of a hardcoded user.
- New built-in panel `claude_quotas` — 5h/weekly Claude usage % per account, read from small JSON
  cache files a statusline script writes; see `docs/CLAUDE_QUOTAS.md` for the ~10-line snippet.
- New built-in panel `activity_scan` — feed of PR/merge mentions detected in your own Claude Code
  session transcripts (`~/.claude/projects/*/*.jsonl`), for you to review before writing your
  standup. Candidates with a PR number are resolved to the real PR title and merge state via
  `gh pr view`. Entries persist until explicitly consumed, so a Friday push is still there Monday.
  Opt-in (commented out in the example config).
- `flightdeck standup-add <id>...` files a detected item as a standup bullet, appended under a
  marked heading at the END of the note so curated content above is never touched. Pair it with the
  panel's `link_scheme` option to get a clickable `+standup` link on every item.
- `activity_scan` also detects handoffs you report in your own typed messages -- "Alice got back
  with me and approved the QA on staging" -- attributed via the new `people` option. A name is
  required, which keeps pasted logs and specs that merely contain "approved" out; questions and
  pasted content are skipped, and only `promptSource == "typed"` lines are read so tool output is
  never mistaken for something you said. Bare `git push` with no PR attached no longer registers.
### Changed
- `flightdeck run` is now a clean no-op (prints a message, writes nothing) when the configured vault
  directory doesn't exist yet, instead of silently creating a phantom directory tree.
- `flightdeck init` warns up front if Obsidian.app isn't installed (macOS).

## [0.1.0] — 2026-08-27
### Added
- First public release.
- Config-driven dashboard generator (`flightdeck run`) with a plugin panel system.
- Built-in panels: standup/notes (embed), GitHub PRs (24h metrics + tables), waiting-on,
  system status (any Statuspage), calendar, email, Slack drafts.
- Streamlined per-service auth: `flightdeck setup github|google|slack`.
- macOS launchd / cron scheduler (`flightdeck install-schedule`), `flightdeck doctor`.
- Pure standard library — no third-party dependencies.
