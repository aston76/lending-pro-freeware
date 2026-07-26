# Contributing

## Before opening a change

1. Use fictitious test data only.
2. Keep changes focused and backward-compatible.
3. Never commit databases, exports, logs, backups, credentials, tokens, or personal information.
4. Add or update tests for business-logic changes.

## Local verification

```bash
npm ci
npm run build:css
npm run check
npm test
```

For interface changes, also launch the desktop application and verify the affected workflow in both personal and demo modes.

## Pull requests

Explain the user-facing behavior, testing performed, and any migration or compatibility risk. Security vulnerabilities must follow [SECURITY.md](SECURITY.md) instead of being posted publicly.
