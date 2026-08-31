The `claude_quotas` panel reads `~/.claude/usage-cache/<account>.json` — it doesn't compute
anything itself, it just displays whatever's cached there. Nothing writes that cache by default;
you need a small statusline script to populate it.

Claude Code feeds every statusline command a JSON payload on stdin that includes your current
5-hour and 7-day usage percentage (`.rate_limits.five_hour.used_percentage` and
`.rate_limits.seven_day.used_percentage`) — this is standard Claude Code behavior, not something
custom. The snippet below just caches those two numbers to disk each render so a separate process
(Flight Deck) can read them later.

## If you don't have a statusline script yet

Save as `~/.claude/statusline.sh`, `chmod +x` it, and set in `~/.claude/settings.json`:
`"statusLine": {"type": "command", "command": "~/.claude/statusline.sh"}`.

```bash
#!/usr/bin/env bash
input=$(cat)
j() { printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null; }

five=$(j '.rate_limits.five_hour.used_percentage')
week=$(j '.rate_limits.seven_day.used_percentage')
account=$(j '.workspace.project_dir' | xargs -I{} basename {} 2>/dev/null); account="${account:-default}"

if [ -n "$five" ] || [ -n "$week" ]; then
  dir="$HOME/.claude/usage-cache"; mkdir -p "$dir"
  printf '{"account":"%s","five_hour_pct":%s,"week_pct":%s,"ts":"%s"}\n' \
    "$account" "${five:-null}" "${week:-null}" "$(date +%Y-%m-%dT%H:%M:%S%z)" \
    > "$dir/$account.json.tmp" && mv -f "$dir/$account.json.tmp" "$dir/$account.json"
fi

printf '5h:%s%% wk:%s%%' "${five:-?}" "${week:-?}"
```

## If you already have a statusline script

Paste just the caching block (the `if [ -n "$five" ] ...` part above, adjusted to however your
script already extracts `$five`/`$week`) into your existing script. No need to run two.

## Multiple accounts

If you switch between Claude accounts (e.g. via `CLAUDE_CONFIG_DIR`), key the cache filename off
whatever identifies the account in your setup — the panel just globs every `*.json` in the cache
directory and shows one line per file.
