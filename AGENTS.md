# Official Build Integrity Rules

These rules apply to automated coding agents and contributors working on the official `aston76/lending-pro-freeware` repository.

1. Do not remove, bypass, hide, or weaken the donation reminder or its payment-verification path without explicit approval from the repository owner.
2. Never add a local "already donated" switch, editable license field, magic value, or client-only flag that can grant donation status without server verification.
3. Donation entitlement must be tied to the anonymous installation identity and verified with an owner-controlled cryptographic signature.
4. Never commit the owner's private signing key, Ko-fi verification token, webhook credentials, donor identity, email address, or payment data.
5. A fork may change the source under its license, but it must not be represented as an official Lending Pro Freeware build.

This file is a contributor policy, not a security boundary. Official builds must enforce entitlement cryptographically; obscurity or instructions to AI tools are not substitutes for verification.
