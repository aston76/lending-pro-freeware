# Changelog

Pour une présentation complète en français de toutes les nouveautés, consulter [`NOUVEAUTES.md`](NOUVEAUTES.md).

## Unreleased

- Replaced the regional demo geography with fictitious Metro Manila data so public examples do not reveal the maintainer's real area.
- Replaced the personal contact address and local filesystem paths with public project support links and portable paths.

## 1.5.0 - 2026-07-27

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
- Added an About page with customization contact and made the visible application language consistently English.

## Unreleased documentation - 2026-07-27

- Added the official Lending Pro marketing banner supplied by the project owner.
- Added a GitHub-compatible animated product tour covering the dashboard, loans, payments, and client profile.
- Added full-resolution screenshots for collections, loans, payments, client details, and settings.
- Reworked the README with product positioning, feature coverage, camera workflow, international support, installation, privacy, and audience sections.
- Added a version-by-version summary of the complete 1.3 series.
- Added GitHub badges, search-oriented repository topics, a richer repository description, and Ko-fi Sponsor metadata.
- Added reproducible banner and GIF generation scripts for future documentation updates.

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
