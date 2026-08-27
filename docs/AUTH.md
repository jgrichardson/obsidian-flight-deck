# Connecting your services

Flight Deck stores credentials in your OS keychain (macOS) or a `0600` file. Nothing leaves your
machine except calls to the APIs you configure. All scopes are read-only (Slack can draft, never post).

## GitHub
Easiest: install the [`gh` CLI](https://cli.github.com) and `gh auth login`. Flight Deck detects it
and uses it automatically. Otherwise `flightdeck setup github` and paste a token with read access to
your repos + pull requests.

## Google (Calendar + Gmail, read-only)
One-time, ~5 minutes:
1. In [Google Cloud Console](https://console.cloud.google.com) pick (or create) a project you own.
2. Enable the **Google Calendar API** and **Gmail API**.
3. **OAuth consent screen → Audience:** if you're on Google Workspace, choose **Internal**
   (no verification, no test-user list). Personal Gmail: External + add yourself as a test user.
4. **Credentials → Create OAuth client ID → Desktop app.** Copy the client id + secret.
5. `flightdeck setup google` — paste them, approve in the browser. Done; the refresh token is stored.

Only read-only scopes are requested — Flight Deck can never send, delete, or modify mail or events.

## Slack (read + draft)
`flightdeck setup slack`, then paste two values from `app.slack.com` in your browser:
- **xoxc token** — DevTools Console:
  `JSON.parse(localStorage.localConfig_v2).teams[Object.keys(JSON.parse(localStorage.localConfig_v2).teams)[0]].token`
- **xoxd cookie** — DevTools → Application → Cookies → the `d` cookie value.

These are browser-session tokens (no app creation / admin approval). They expire when you log out of
Slack in that browser; re-run setup to refresh. The integration can create drafts but **cannot post**.
