# Contributing

Thanks for helping improve Flight Deck! It's small, dependency-free, and easy to hack on.

## Dev setup
```bash
git clone https://github.com/jgrichardson/obsidian-flight-deck && cd obsidian-flight-deck
python -m pip install -e .
flightdeck init && flightdeck run     # point [vault] at a throwaway vault to test
python -m pytest                       # run the tests
```
No dependencies to install — it's standard-library only. Please keep it that way for panels in core.

## Adding a panel
A panel is ~30 lines. See [`docs/PANELS.md`](docs/PANELS.md). In short: subclass `Panel`,
implement `render()`, register it in `flightdeck/panels/__init__.py`, document its options.

## Guidelines
- **Stdlib only** in core panels (`urllib` for HTTP). Optional heavy deps go in clearly-labeled extras.
- **Read-only by default.** Never add a write/post capability without an explicit opt-in and docs.
- Keep secrets in `creds` (keychain / 0600 file). Never log secret values.
- Match the existing style; add a test when you add behavior.

## Pull requests
- One focused change per PR. Update `CHANGELOG.md` under `## [Unreleased]`.
- CI must pass (import + render smoke test).
- Be kind. See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
