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
