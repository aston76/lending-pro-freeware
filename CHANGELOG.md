# Changelog

Pour une présentation complète en français de toutes les nouveautés, consulter [`NOUVEAUTES.md`](NOUVEAUTES.md).

## Unreleased

## 1.5.1 - 2026-08-13

- Replaced the regional demo geography with fictitious Metro Manila data so public examples do not reveal the maintainer's real area.
- Replaced the personal contact address and local filesystem paths with public project support links and portable paths.
- Completed demo resets with the same guarantor, collateral, collector, fee and risk data as a first demo load.
- Included collectors, guarantors and collateral in the raw JSON backup so every documented business table is preserved.
- Removed the last regional vehicle plates and collateral locality from the public demo generator.
- Upgraded the transitive Nano ID dependency to a patched release and restored a clean npm security audit.
- Strengthened the privacy regression test without embedding former maintainer contact details in the public test source.
- Kept every mobile toolbar action inside the 390 px viewport while preserving menu, calculator and quick-create access.
- Restored the hidden state for custom buttons, sidebar actions and the login form so unavailable controls no longer appear active.
- Made the client directory readable at phone widths by retaining the primary ID, name and contact fields without horizontal clipping.

## 1.5.0 - 2026-07-27

- Added the official Lending Pro marketing banner and a GitHub-compatible animated product tour covering the dashboard, loans, payments, and client profile.
- Added full-resolution screenshots for the login screen, dashboard, collections, loans, payments, client details, settings, and donation reminder.
- Reworked the README and screenshot gallery with product positioning, feature coverage, installation, privacy, international support, and reproducible banner/GIF generation scripts.
- Replaced the legacy currency-symbol icon with a new international Lending Pro brand mark combining a financial ledger, portfolio growth and protection.
- Added matching macOS ICNS, Windows ICO and in-app PNG assets generated from one versioned brand source.
- Added an optional per-profile login screen shown before any business data is loaded.
- Added backend session locking so public business API calls remain unavailable until the active profile is authenticated.
- Added PBKDF2 password verification, legacy-hash upgrade support, five-attempt cooldown and manual session locking.
- Added independent settings for profile-password protection and login at startup; existing installations continue directly to the app by default.
- Fixed the Help & Guide module initialization order so its currency-aware content loads without a frontend error.
- Added a cross-platform test launcher that automatically uses the local project virtual environment when available.

## 1.4.0 - 2026-07-27

- Added guarantors/co-makers with contact details, identity data and local signatures.
- Added structured collateral records with valuation, identifiers and pledged/released/seized/sold lifecycle states.
- Added extended borrower KYC: identity number, date of birth, employer, occupation and gender.
- Added daily, weekly, biweekly and monthly repayment schedules while preserving legacy monthly loans.
- Added processing and insurance fees, net disbursement, upfront-interest handling and dated effective APR calculation.
- Added configurable, capped and idempotent automatic late penalties after a grace period.
- Added PAR 1/30/60/90, aging buckets, portfolio yield and post-default recovery reporting.
- Added collector management, loan assignment and performance reporting.
- Extended contracts and Excel exports with the new lending, guarantor, collateral and collector data.
- Added an About page with public project support links and made the visible application language consistently English.

## 1.3.2 - 2026-07-26

- Made the light interface the default for new installations.
- Preserved dark mode as an explicit user preference.
- Rebuilt all public screenshots in light mode with isolated fictitious data.
- Added a dedicated Markdown screenshot gallery with full-resolution links.

## 1.3.1 - 2026-07-26

- Changed the donation reminder to appear at most once every 7 days.
- Changed the reminder interval to 90 days after local donation confirmation.
- Removed the unused installation ID and future license-verification design.
- Localized the new reminder and confirmation labels in all 17 supported donation-dialog languages.

## 1.3.0 - 2026-07-26

- Added a checksum-verified command-line installer for Apple Silicon macOS.
- Added clean screenshots generated from an isolated empty/demo profile.
- Added 22 selectable currencies shared by the interface, SMS, PDF, and Excel exports.
- Removed the Philippines-only address search restriction and the fixed +63 company phone prefix.
- Added a persistent anonymous installation ID for future Ko-fi webhook matching.
- Removed the manual donation-reminder bypass; the reminder returns on every launch until verified.
- Added an offline language selector with 17 localized donation-dialog languages.
- Added official-build integrity rules for contributors and coding agents.

## 1.2.0 - 2026-07-26

- Renamed the public application to Lending Pro Freeware.
- Added a permanent dashboard donation action and an optional daily support reminder.
- Kept donation acknowledgement local and explicit; no payment status is inferred.
- Added public project, contribution, security, and licensing documentation.
- Strengthened exclusions for databases, credentials, keys, backups, and build artifacts.

## 1.1.0

- Added opt-in, isolated demo mode with an empty personal database by default.
- Improved loan, payment, penalty, export, backup, and shutdown workflows.
- Added a drag-to-Applications Apple Silicon DMG package.
