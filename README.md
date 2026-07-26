# Lending Pro Freeware

Lending Pro Freeware is a free, offline-first desktop application for managing clients, loans, repayment schedules, collections, penalties, commissions, alerts, and exports.

All operational data is stored locally on the user's computer. The repository and packaged application contain no client database, credentials, or personal records.

## Features

- Client and loan management
- Fixed-rate and declining-balance schedules
- Payment allocation, partial payments, penalties, and voids
- Collection calendar and overdue alerts
- PDF, Excel, backup, and restore tools
- Optional temporary demo mode with fictitious records
- Light and dark themes
- Clean shutdown with automatic local backup

## Install on macOS

Download the latest Apple Silicon DMG from [Releases](https://github.com/aston76/lending-pro-freeware/releases), open it, and drag **Lending Pro Freeware** into **Applications**.

The current package supports Apple Silicon Macs. It is ad-hoc signed but not Apple-notarized. If macOS blocks the first launch, Control-click the app, choose **Open**, then confirm.

The application starts with an empty personal database. Use **Tester la démo** in the top-right toolbar to load temporary fictitious data. Leaving demo mode or restarting returns to the personal database.

## Run from source

Requirements: Python 3.11+, Node.js 22+, and the native dependencies required by pywebview.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
npm ci
npm run build:css
python main.py
```

## Quality checks

```bash
npm run check
npm test
```

GitHub Actions runs the same syntax, build, and test checks on every push and pull request.

## Privacy and security

- No telemetry or analytics are included.
- Client records and settings remain in the local application data directory.
- Database files, exports, backups, credentials, logs, and build artifacts are excluded from Git.
- Map, SMS, Google Drive, and donation links require network access only when the corresponding feature is used.

See [SECURITY.md](SECURITY.md) for responsible vulnerability reporting.

## Support the project

Lending Pro Freeware remains free to use. You can support its maintenance with a donation of **€5 or more** through [Ko-fi](https://ko-fi.com/astonswissapp).

The dashboard always keeps a **Don** button available. The optional reminder appears at most once per day until it is manually disabled on that device.

## Contributing

Bug reports and focused pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a change.

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Aston Swiss App.
