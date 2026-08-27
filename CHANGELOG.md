# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org).

## [0.1.0] — 2026-08-27
### Added
- First public release.
- Config-driven dashboard generator (`flightdeck run`) with a plugin panel system.
- Built-in panels: standup/notes (embed), GitHub PRs (24h metrics + tables), waiting-on,
  system status (any Statuspage), calendar, email, Slack drafts.
- Streamlined per-service auth: `flightdeck setup github|google|slack`.
- macOS launchd / cron scheduler (`flightdeck install-schedule`), `flightdeck doctor`.
- Pure standard library — no third-party dependencies.
