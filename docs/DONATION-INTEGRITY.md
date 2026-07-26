# Donation Integrity

Ko-fi sends payment data only through a creator-configured webhook. It does not provide a public client-side API for querying donations.

The desktop application therefore generates a persistent anonymous installation ID. The user includes that ID in the Ko-fi message. A future verification service must:

1. receive the Ko-fi webhook over HTTPS;
2. validate Ko-fi's verification token and reject duplicate transaction IDs;
3. require the configured minimum completed amount;
4. associate the payment with the exact installation identity;
5. return a signed entitlement containing that installation identity;
6. let the desktop application disable reminders only after verifying the owner signature.

A copied ID must not unlock another Mac. The final service should bind the entitlement to a locally generated public key and require proof of possession of the corresponding private key. The private key must remain in the macOS Keychain or equivalent secure storage and must never be accepted through a text field.

No hidden file, local preference, or instruction aimed at AI tools can provide this guarantee. Cryptographic proof and server-side webhook validation are required.
