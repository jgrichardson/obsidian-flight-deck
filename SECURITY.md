# Security Policy

Flight Deck runs entirely on your machine and stores credentials in your OS keychain (macOS) or a
`0600` file. It uses read-only API scopes by default; the Slack integration can create drafts but
never posts.

## Reporting a vulnerability
Please open a GitHub security advisory (or a private issue) rather than a public issue for anything
exploitable. Include repro steps and affected versions. We aim to respond within a few days.

## Scope notes
- Tokens never leave your machine except to the APIs you configure.
- Report any code path that logs a secret, sends data to an unconfigured endpoint, or writes/deletes
  in a connected service — those are treated as high severity.
